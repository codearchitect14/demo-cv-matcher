from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db_session
from models.application import Application, ApplicationStatusEnum
from models.candidate import Candidate
from models.job import Job
from db.crud.application import application as application_crud
from api.routers.auth import get_current_user
from config.connection_pool import global_pool
from schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from middleware.recruiter_auth import get_current_recruiter, RecruiterContext
from services.email_service import email_service
from services.notification_service import notification_service

async def auto_update_application_statuses(rows):
    """Automatically update application status based on assessment scores"""
    try:
        updates_needed = []
        
        for row in rows:
            # Only update status if assessment exists, is completed, and has a valid score
            if (row["assessment_status"] is not None and 
                row["assessment_status"] == "completed" and 
                row["assessment_score"] is not None and
                row["assessment_score"] >= 0):  # Ensure score is valid (not negative)
                
                application_id = row["id"]
                current_status = row["status"]
                assessment_score = row["assessment_score"]
                
                # Determine new status based on assessment score
                if assessment_score >= 50 and current_status == "APPLIED":
                    new_status = "INTERVIEW_SCHEDULED"
                    updates_needed.append((application_id, new_status, assessment_score))
                elif assessment_score < 50 and current_status == "APPLIED":
                    new_status = "REJECTED"
                    updates_needed.append((application_id, new_status, assessment_score))
        
        # Batch update applications
        if updates_needed:
            for app_id, new_status, score in updates_needed:
                # Get candidate_id and job_id for interaction logging
                app_details = await global_pool.fetchrow("""
                    SELECT candidate_id, job_id FROM applications WHERE id = $1
                """, app_id)
                
                if app_details:
                    candidate_id = app_details['candidate_id']
                    job_id = app_details['job_id']
                    
                    # Update application status
                    await global_pool.execute("""
                        UPDATE applications 
                        SET status = $1, updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2 AND status = 'APPLIED'
                    """, new_status, app_id)
                    
                    # Log the status change interaction
                    try:
                        # Map application status to valid interaction type (use uppercase to match DB enum)
                        interaction_type_map = {
                            "APPLIED": "APPLIED",
                            "INTERVIEW_SCHEDULED": "edited",
                            "REJECTED": "REJECTED",
                            "OFFERED": "edited",
                            "HIRED": "edited"
                        }
                        interaction_type = interaction_type_map.get(new_status, "edited")
                        
                        await global_pool.execute("""
                            INSERT INTO interaction_log (user_id, user_type, job_id, interaction_type, timestamp)
                            VALUES ($1, 'candidate', $2, $3, NOW())
                        """, candidate_id, job_id, interaction_type)
                        print(f"✅ Auto-updated application {app_id}: {new_status} (assessment score: {score}%) - logged interaction")
                    except Exception as log_error:
                        print(f"⚠️ Failed to log status change interaction: {log_error}")
                    
                    # Send status update email and notification
                    try:
                        # Get candidate and job details for email
                        candidate_details = await global_pool.fetchrow("""
                            SELECT email, name FROM candidates WHERE id = $1
                        """, candidate_id)
                        
                        job_details = await global_pool.fetchrow("""
                            SELECT title, company FROM jobs WHERE id = $1
                        """, job_id)
                        
                        if candidate_details and job_details:
                            candidate_email = candidate_details['email']
                            candidate_name = candidate_details['name']
                            job_title = job_details['title']
                            company_name = job_details['company'] or "Unknown Company"
                            
                            # Send status update email
                            await email_service.send_status_update_email(
                                candidate_email=candidate_email,
                                candidate_name=candidate_name,
                                job_title=job_title,
                                company_name=company_name,
                                old_status="APPLIED",
                                new_status=new_status
                            )
                            logger.info(f"Status update email sent to {candidate_email}")
                            
                            # Create in-app notification
                            await notification_service.create_notification(
                                user_id=candidate_id,
                                user_type="candidate",
                                title="Application Status Updated",
                                message=f"Your application for '{job_title}' status has changed to {new_status}.",
                                notification_type="info" if new_status == "INTERVIEW_SCHEDULED" else "warning",
                                related_entity_type="application",
                                related_entity_id=app_id
                            )
                            logger.info(f"Status update notification created for candidate {candidate_id}")
                            
                    except Exception as notification_error:
                        logger.error(f"Failed to send status update notification: {notification_error}")
                else:
                    print(f"⚠️ Could not find application details for ID {app_id}")
                
    except Exception as e:
        print(f"⚠️ Error auto-updating application statuses: {e}")

router = APIRouter(tags=["Applications"])

@router.get("/recruiter", response_model=List[dict])
async def get_recruiter_applications(
    recruiter_id: Optional[int] = Query(None, description="Filter by recruiter ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by candidate name, email, or job title")
):
    """Get applications for jobs assigned to the authenticated recruiter"""
    import time
    start_time = time.time()
    
    try:
        from config.connection_pool import global_pool
        
        # Build dynamic WHERE clause for filtering
        where_conditions = []
        params = []
        param_count = 0
        
        # Add recruiter filter if provided
        if recruiter_id is not None:
            param_count += 1
            where_conditions.append(f"j.recruiter_id = ${param_count}")
            params.append(recruiter_id)
        
        # Add status filter
        if status_filter:
            param_count += 1
            where_conditions.append(f"a.status = ${param_count}")
            params.append(status_filter)
        
        # Add search filter
        if search:
            param_count += 1
            where_conditions.append(f"""
                (LOWER(c.name) LIKE LOWER(${param_count}) OR 
                 LOWER(c.email) LIKE LOWER(${param_count}) OR 
                 LOWER(j.title) LIKE LOWER(${param_count}))
            """)
            params.append(f"%{search}%")
        
        # Add pagination parameters
        param_count += 1
        limit_param = param_count
        param_count += 1
        skip_param = param_count
        params.extend([limit, skip])
        
        # Build the final query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
            SELECT 
                a.id, a.status, a.applied_at, a.is_qualified,
                c.id as candidate_id, c.name as candidate_name, c.email as candidate_email,
                c.location as candidate_location, c.domain as candidate_domain,
                j.id as job_id, j.title as job_title, j.company as job_company,
                j.location as job_location
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.id
            JOIN jobs j ON a.job_id = j.id
            WHERE {where_clause}
            ORDER BY a.applied_at DESC
            LIMIT ${limit_param} OFFSET ${skip_param}
        """
        
        # Execute using global connection pool
        rows = await global_pool.fetch(query, *params)
        
        # Convert to response format
        applications = []
        for row in rows:
            applications.append({
                "id": row['id'],
                "status": row['status'],
                "applied_at": row['applied_at'].isoformat() if row['applied_at'] else None,
                "is_qualified": row['is_qualified'],
                "candidate": {
                    "id": row['candidate_id'],
                    "name": row['candidate_name'],
                    "email": row['candidate_email'],
                    "location": row['candidate_location'],
                    "domain": row['candidate_domain']
                },
                "job": {
                    "id": row['job_id'],
                    "title": row['job_title'],
                    "company": row['job_company'],
                    "location": row['job_location']
                }
            })
        
        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(applications)} applications for recruiter {recruiter_id or 'all'} (took {elapsed:.3f}s)")
        return applications
        
    except Exception as e:
        logger.error(f"Error getting recruiter applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get applications"
        )

@router.get("/public", response_model=List[dict])
async def get_all_applications_public(
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by candidate name, email, job title, or company"),
    candidate_id: Optional[int] = Query(None, description="Filter by specific candidate ID"),
    job_id: Optional[int] = Query(None, description="Filter by specific job ID"),
    location: Optional[str] = Query(None, description="Filter by location"),
    experience_range: Optional[str] = Query(None, description="Filter by experience range (0-2, 3-5, 6-8, 9+)"),
    qualification_filter: Optional[str] = Query(None, description="Filter by qualification: 'qualified', 'rejected', or 'all'"),
    recruiter_id: Optional[int] = Query(None, description="Filter by assigned recruiter ID")
):
    """Get all applications with candidate and job details (optimized for fast response)"""
    import time
    start_time = time.time()
    
    try:
        from config.connection_pool import global_pool
        
        # Build dynamic WHERE clause for filtering
        where_conditions = []
        params = []
        param_count = 0
        
        # Add qualification filters
        if qualification_filter:
            if qualification_filter.lower() == "qualified":
                where_conditions.append("a.is_qualified = true")
            elif qualification_filter.lower() == "rejected":
                where_conditions.append("a.is_qualified = false")
        
        # Add recruiter filter
        if recruiter_id is not None:
            param_count += 1
            where_conditions.append(f"j.recruiter_id = ${param_count}")
            params.append(recruiter_id)
        
        # Add other existing filters
        if status_filter:
            param_count += 1
            where_conditions.append(f"a.status = ${param_count}")
            params.append(status_filter)
        
        if candidate_id:
            param_count += 1
            where_conditions.append(f"a.candidate_id = ${param_count}")
            params.append(candidate_id)
        
        if job_id:
            param_count += 1
            where_conditions.append(f"a.job_id = ${param_count}")
            params.append(job_id)
        
        # Build the final query (asyncpg positional params)
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        query = f"""
            SELECT 
                a.id, a.job_id, a.candidate_id, a.status, a.created_at, a.updated_at,
                a.candidate_score, a.is_qualified,
                c.name as candidate_name, c.email as candidate_email, c.location as candidate_location,
                c.domain as candidate_domain, c.expected_salary_min, c.expected_salary_max,
                j.title as job_title, j.company, j.location as job_location, j.domain as job_domain,
                j.salary_min, j.salary_max, j.total_years_required, j.threshold_score, j.recruiter_id,
                r.full_name as recruiter_name, r.email as recruiter_email
            FROM applications a
            LEFT JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN recruiters r ON j.recruiter_id = r.id
            WHERE {where_clause}
            ORDER BY a.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, skip])
        rows = await global_pool.fetch(query, *params)
        
        response_applications = []
        for row in rows:
            app_data = {
                "id": row['id'],
                "job_id": row['job_id'],
                "candidate_id": row['candidate_id'],
                "status": row['status'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
                "candidate_score": float(row['candidate_score']) if row['candidate_score'] is not None else None,
                "is_qualified": row['is_qualified']
            }
            
            # Add candidate data if available
            if row['candidate_name']:
                app_data["candidate"] = {
                    "id": row['candidate_id'],
                    "name": row['candidate_name'],
                    "email": row['candidate_email'],
                    "location": row['candidate_location'],
                    "domain": row['candidate_domain'],
                    "expected_salary_min": row['expected_salary_min'],
                    "expected_salary_max": row['expected_salary_max']
                }
            
            # Add job data if available
            if row['job_title']:
                app_data["job"] = {
                    "id": row['job_id'],
                    "title": row['job_title'],
                    "company": row['company'],
                    "location": row['job_location'],
                    "domain": row['job_domain'],
                    "salary_min": row['salary_min'],
                    "salary_max": row['salary_max'],
                    "total_years_required": row['total_years_required'],
                    "threshold_score": row['threshold_score'],
                    "recruiter_id": row['recruiter_id']
                }
                
                # Add recruiter data if available
                if row['recruiter_name']:
                    app_data["recruiter"] = {
                        "id": row['recruiter_id'],
                        "name": row['recruiter_name'],
                        "email": row['recruiter_email']
                    }
            
            response_applications.append(app_data)
        
        return response_applications
    except Exception as e:
        print(f"Get all applications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve applications. Please try again later."
        )

@router.get("/recruiter", response_model=List[dict])
async def get_recruiter_applications(
    db: AsyncSession = Depends(get_db_session),
    recruiter_context: RecruiterContext = Depends(get_current_recruiter),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by candidate name, email, job title, or company"),
    candidate_id: Optional[int] = Query(None, description="Filter by specific candidate ID"),
    job_id: Optional[int] = Query(None, description="Filter by specific job ID"),
    location: Optional[str] = Query(None, description="Filter by location"),
    experience_range: Optional[str] = Query(None, description="Filter by experience range (0-2, 3-5, 6-8, 9+)"),
    qualification_filter: Optional[str] = Query(None, description="Filter by qualification: 'qualified', 'rejected', or 'all'")
):
    """Get applications for the authenticated recruiter (role-based access)"""
    try:
        from sqlalchemy import text
        
        # Build dynamic WHERE clause for filtering
        where_conditions = []
        params = {"limit": limit, "skip": skip}
        
        # Add recruiter filter - non-admin recruiters can only see their assigned jobs
        if not recruiter_context.is_admin:
            where_conditions.append("j.recruiter_id = :recruiter_id")
            params["recruiter_id"] = recruiter_context.recruiter_id
        
        # Add qualification filters
        if qualification_filter:
            if qualification_filter.lower() == "qualified":
                where_conditions.append("a.is_qualified = true")
            elif qualification_filter.lower() == "rejected":
                where_conditions.append("a.is_qualified = false")
        
        # Add other existing filters
        if status_filter:
            where_conditions.append("a.status = :status_filter")
            params["status_filter"] = status_filter
        
        if candidate_id:
            where_conditions.append("a.candidate_id = :candidate_id")
            params["candidate_id"] = candidate_id
        
        if job_id:
            where_conditions.append("a.job_id = :job_id")
            params["job_id"] = job_id
        
        # Build the final query with optimized parameters
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Convert to global_pool format with positional parameters
        final_params = []
        param_count = 0
        
        # Rebuild params for global_pool
        if qualification_filter:
            # Already added to where_conditions
            pass
        if recruiter_id is not None:
            final_params.append(recruiter_id)
            param_count += 1
        if status_filter:
            final_params.append(status_filter)
            param_count += 1
        if candidate_id:
            final_params.append(candidate_id)
            param_count += 1
        if job_id:
            final_params.append(job_id)
            param_count += 1
        if location:
            final_params.append(f"%{location.lower()}%")
            param_count += 1
        if search:
            search_term = f"%{search.lower()}%"
            final_params.extend([search_term, search_term, search_term, search_term])
            param_count += 4
        if experience_range:
            if experience_range == "0-2":
                final_params.extend([0, 2])
            elif experience_range == "3-5":
                final_params.extend([3, 5])
            elif experience_range == "6-8":
                final_params.extend([6, 8])
            elif experience_range == "9+":
                final_params.append(9)
            param_count += 2 if experience_range != "9+" else 1
        
        # Add limit and offset
        final_params.extend([limit, skip])
        
        query = f"""
            SELECT 
                a.id, a.job_id, a.candidate_id, a.status, a.created_at, a.updated_at,
                a.candidate_score, a.is_qualified,
                c.name as candidate_name, c.email as candidate_email, c.location as candidate_location,
                c.domain as candidate_domain, c.expected_salary_min, c.expected_salary_max,
                j.title as job_title, j.company, j.location as job_location, j.domain as job_domain,
                j.salary_min, j.salary_max, j.total_years_required, j.threshold_score, j.recruiter_id,
                r.full_name as recruiter_name, r.email as recruiter_email,
                ass.status as assessment_status, ass.score as assessment_score, ass.completion_time as assessment_completion_time
            FROM applications a
            LEFT JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN recruiters r ON j.recruiter_id = r.id
            LEFT JOIN assessments ass ON a.id = ass.application_id
            WHERE {where_clause}
            ORDER BY a.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        
        rows = await global_pool.fetch(query, *final_params)
        
        # Auto-update application status based on assessment scores
        await auto_update_application_statuses(rows)
        
        response_applications = []
        for row in rows:
            app_data = {
                "id": row["id"],
                "job_id": row["job_id"],
                "candidate_id": row["candidate_id"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "candidate_score": float(row["candidate_score"]) if row["candidate_score"] else None,
                "is_qualified": row["is_qualified"],
                "assessment_status": row["assessment_status"],
                "assessment_score": float(row["assessment_score"]) if row["assessment_score"] else None,
                "assessment_completion_time": row["assessment_completion_time"]
            }
            
            # Add candidate data if available
            if row["candidate_name"]:
                app_data["candidate"] = {
                    "id": row["candidate_id"],
                    "name": row["candidate_name"],
                    "email": row["candidate_email"],
                    "location": row["candidate_location"],
                    "domain": row["candidate_domain"],
                    "expected_salary_min": row["expected_salary_min"],
                    "expected_salary_max": row["expected_salary_max"]
                }
            
            # Add job data if available
            if row["job_title"]:
                app_data["job"] = {
                    "id": row["job_id"],
                    "title": row["job_title"],
                    "company": row["company"],
                    "location": row["job_location"],
                    "domain": row["job_domain"],
                    "salary_min": row["salary_min"],
                    "salary_max": row["salary_max"],
                    "total_years_required": row["total_years_required"],
                    "threshold_score": row["threshold_score"],
                    "recruiter_id": row["recruiter_id"]
                }
                
                # Add recruiter data if available
                if row["recruiter_name"]:
                    app_data["recruiter"] = {
                        "id": row["recruiter_id"],
                        "name": row["recruiter_name"],
                        "email": row["recruiter_email"]
                    }
            
            response_applications.append(app_data)
        
        return response_applications
        
    except Exception as e:
        print(f"Get recruiter applications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve applications. Please try again later."
        )

@router.put("/{application_id}/status/public")
async def update_application_status_public(
    application_id: int,
    status_update: ApplicationUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update application status (public endpoint for testing)"""
    try:
        # Use raw SQL to avoid transaction issues
        from sqlalchemy import text
        
        # First check if application exists
        check_query = text("SELECT id FROM applications WHERE id = :application_id")
        result = await db.execute(check_query, {"application_id": application_id})
        application = result.fetchone()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Update the status using raw SQL (manual override)
        update_query = text("""
            UPDATE applications 
            SET status = :status, updated_at = NOW() 
            WHERE id = :application_id
            RETURNING id, job_id, candidate_id, status, candidate_score, is_qualified, created_at, updated_at
        """)
        
        result = await db.execute(update_query, {
            "application_id": application_id,
            "status": status_update.status
        })
        
        updated_application = result.fetchone()
        await db.commit()
        
        if updated_application:
            return {
                "id": updated_application[0],
                "job_id": updated_application[1],
                "candidate_id": updated_application[2],
                "status": updated_application[3],
                "candidate_score": float(updated_application[4]) if updated_application[4] else None,
                "is_qualified": updated_application[5],
                "created_at": updated_application[6],
                "updated_at": updated_application[7]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update application"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update application error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update application: {str(e)}"
        )

@router.post("/public")
async def create_application_public(
    application_data: ApplicationCreate
):
    """Create application for testing (public endpoint) - uses direct asyncpg to avoid greenlet issues"""
    try:
        print(f"DEBUG: Creating application - candidate_id: {application_data.candidate_id}, job_id: {application_data.job_id}")
        
        # Ensure candidate_id is provided for public endpoint
        if not application_data.candidate_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="candidate_id is required for public endpoint"
            )
        
        # Check if already applied using direct query
        existing_check = await global_pool.fetchrow(
            "SELECT id FROM applications WHERE candidate_id = $1 AND job_id = $2",
            application_data.candidate_id, application_data.job_id
        )
        
        if existing_check:
            # Return 200 OK with info message instead of error
            return {
                "id": existing_check['id'],
                "candidate_id": application_data.candidate_id,
                "job_id": application_data.job_id,
                "status": "APPLIED",
                "message": "You have already applied to this job!"
            }
        
        # Prepare status value
        status_value = 'APPLIED'
        if hasattr(application_data.status, 'value'):
            status_value = application_data.status.value
        elif isinstance(application_data.status, str):
            status_value = application_data.status.upper()
        
        # Create application using direct query
        application_id = await global_pool.fetchval(
            """
            INSERT INTO applications (candidate_id, job_id, status, created_at, updated_at)
            VALUES ($1, $2, $3, NOW(), NOW())
            RETURNING id
            """,
            application_data.candidate_id, application_data.job_id, status_value
        )
        
        # Log the interaction
        try:
            await global_pool.execute(
                """
                INSERT INTO interaction_log (user_id, user_type, job_id, interaction_type, timestamp)
                VALUES ($1, 'candidate', $2, 'APPLIED', NOW())
                """,
                application_data.candidate_id, application_data.job_id
            )
            print(f"✅ Logged APPLIED interaction for candidate {application_data.candidate_id} to job {application_data.job_id}")
        except Exception as log_error:
            print(f"⚠️ Failed to log interaction: {log_error}")
        
        # Send application confirmation email
        try:
            # Get candidate and job details for email
            candidate_details = await global_pool.fetchrow("""
                SELECT email, name FROM candidates WHERE id = $1
            """, application_data.candidate_id)
            
            job_details = await global_pool.fetchrow("""
                SELECT title, company FROM jobs WHERE id = $1
            """, application_data.job_id)
            
            if candidate_details and job_details:
                candidate_email = candidate_details['email']
                candidate_name = candidate_details['name']
                job_title = job_details['title']
                company_name = job_details['company'] or "Unknown Company"
                
                # Send application confirmation email
                await email_service.send_application_confirmation_email(
                    candidate_email=candidate_email,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company_name=company_name
                )
                print(f"✅ Application confirmation email sent to {candidate_email}")
        except Exception as email_error:
            print(f"⚠️ Failed to send application confirmation email: {email_error}")
        
        # Create in-app notification for candidate
        try:
            job_title = job_details['title'] if job_details else "Job Application"
            await notification_service.create_notification(
                user_id=application_data.candidate_id,
                user_type="candidate",
                title="Job Application Submitted",
                message=f"Your job application for '{job_title}' has been submitted successfully!",
                notification_type="success",
                related_entity_type="application",
                related_entity_id=application_id
            )
            print(f"✅ Application notification created for candidate {application_data.candidate_id}")
        except Exception as notification_error:
            print(f"⚠️ Failed to create application notification: {notification_error}")
        
        # Send notification to assigned sub-recruiter (if job is assigned)
        try:
            # Get job assignment details
            job_assignment = await global_pool.fetchrow("""
                SELECT j.recruiter_id, j.company_id, r.full_name as recruiter_name, r.email as recruiter_email
                FROM jobs j
                LEFT JOIN recruiters r ON j.recruiter_id = r.id
                WHERE j.id = $1 AND j.recruiter_id IS NOT NULL
            """, application_data.job_id)
            
            if job_assignment and job_assignment['recruiter_id']:
                recruiter_id = job_assignment['recruiter_id']
                recruiter_name = job_assignment['recruiter_name']
                recruiter_email = job_assignment['recruiter_email']
                candidate_name = candidate_details['name'] if candidate_details else "Candidate"
                job_title = job_details['title'] if job_details else "Job"
                
                # Send email notification to sub-recruiter
                await email_service.send_candidate_application_notification_email(
                    recruiter_email=recruiter_email,
                    recruiter_name=recruiter_name,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company_name=job_assignment.get('company_id', 'Company'),
                    application_id=application_id
                )
                print(f"✅ Candidate application email sent to sub-recruiter {recruiter_email}")
                
                # Create in-app notification for sub-recruiter
                await notification_service.create_notification(
                    user_id=recruiter_id,
                    user_type="recruiter",
                    title="New Candidate Application",
                    message=f"Candidate {candidate_name} applied for '{job_title}' position.",
                    notification_type="info",
                    related_entity_type="application",
                    related_entity_id=application_id
                )
                print(f"✅ Application notification created for sub-recruiter {recruiter_id}")
                
        except Exception as recruiter_notification_error:
            print(f"⚠️ Failed to send sub-recruiter notification: {recruiter_notification_error}")
        
        # Return simple success response to avoid greenlet issues
        return {
            "id": application_id,
            "candidate_id": application_data.candidate_id,
            "job_id": application_data.job_id,
            "status": status_value,
            "message": "Application submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )

@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application_data: ApplicationCreate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create application for the authenticated user with automatic qualification check"""
    try:
        print(f"DEBUG: Creating application for user {current_user.id} - job_id: {application_data.job_id}")

        # Use raw SQL for faster duplicate check
        from sqlalchemy import text
        from services.qualification_service import qualification_service

        # Fast duplicate check using raw SQL
        check_query = text("""
            SELECT id FROM applications
            WHERE candidate_id = :candidate_id AND job_id = :job_id
            LIMIT 1
        """)

        result = await db.execute(check_query, {
            "candidate_id": current_user.id,
            "job_id": application_data.job_id
        })

        existing_application = result.fetchone()

        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already applied for this job"
            )

        # Create application using raw SQL for better performance
        insert_query = text("""
            INSERT INTO applications (candidate_id, job_id, status, created_at, updated_at)
            VALUES (:candidate_id, :job_id, :status, NOW(), NOW())
            RETURNING id, candidate_id, job_id, status, created_at, updated_at
        """)

        result = await db.execute(insert_query, {
            "candidate_id": current_user.id,
            "job_id": application_data.job_id,
            "status": ApplicationStatusEnum.APPLIED.value
        })

        application_row = result.fetchone()
        
        if application_row:
            application_id = application_row[0]
            
            # Run automatic qualification check
            qualification_success = await qualification_service.update_application_qualification(
                db, application_id, current_user.id, application_data.job_id
            )
            
            if qualification_success:
                print(f"DEBUG: Qualification check completed for application {application_id}")
            else:
                print(f"DEBUG: Qualification check failed for application {application_id}")
            
            await db.commit()
            
            # Send application confirmation email
            try:
                # Get job details for email
                job_query = text("SELECT title, company FROM jobs WHERE id = :job_id")
                job_result = await db.execute(job_query, {"job_id": application_data.job_id})
                job_row = job_result.fetchone()
                
                if job_row:
                    job_title = job_row[0]
                    company_name = job_row[1] if job_row[1] else "Unknown Company"
                    
                    await email_service.send_application_confirmation_email(
                        candidate_email=current_user.email,
                        candidate_name=current_user.name,
                        job_title=job_title,
                        company_name=company_name
                    )
                    logger.info(f"Application confirmation email sent to {current_user.email}")
            except Exception as e:
                logger.error(f"Failed to send application confirmation email: {str(e)}")
            
            # Create in-app notification
            try:
                job_title = job_row[0] if job_row else "Job Application"
                await notification_service.create_notification(
                    user_id=current_user.id,
                    user_type="candidate",
                    title="Application Submitted Successfully",
                    message=f"Your application for '{job_title}' has been submitted successfully.",
                    notification_type="success",
                    related_entity_type="application",
                    related_entity_id=application_id
                )
                logger.info(f"Application notification created for user {current_user.id}")
            except Exception as e:
                logger.error(f"Failed to create application notification: {str(e)}")
            
            # Get the updated application data
            updated_query = text("""
                SELECT id, candidate_id, job_id, status, candidate_score, is_qualified, created_at, updated_at
                FROM applications WHERE id = :application_id
            """)
            
            result = await db.execute(updated_query, {"application_id": application_id})
            updated_row = result.fetchone()
            
            if updated_row:
                return {
                    "id": updated_row[0],
                    "candidate_id": updated_row[1],
                    "job_id": updated_row[2],
                    "status": updated_row[3],
                    "candidate_score": float(updated_row[4]) if updated_row[4] else None,
                    "is_qualified": updated_row[5],
                    "created_at": updated_row[6],
                    "updated_at": updated_row[7]
                }
            else:
                # Fallback to original data if update query fails
                return {
                    "id": application_row[0],
                    "candidate_id": application_row[1],
                    "job_id": application_row[2],
                    "status": application_row[3],
                    "candidate_score": None,
                    "is_qualified": None,
                    "created_at": application_row[4],
                    "updated_at": application_row[5]
                }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create application"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )

@router.get("/check-status/{job_id}")
async def check_application_status(
    job_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Check if user has already applied for a specific job"""
    try:
        from sqlalchemy import text
        
        check_query = text("""
            SELECT id, status, created_at 
            FROM applications 
            WHERE candidate_id = :candidate_id AND job_id = :job_id 
            LIMIT 1
        """)
        
        result = await db.execute(check_query, {
            "candidate_id": current_user.id,
            "job_id": job_id
        })
        
        application = result.fetchone()
        
        if application:
            return {
                "has_applied": True,
                "application_id": application[0],
                "status": application[1],
                "applied_at": application[2]
            }
        else:
            return {
                "has_applied": False,
                "application_id": None,
                "status": None,
                "applied_at": None
            }
            
    except Exception as e:
        print(f"DEBUG: Check application status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check application status: {str(e)}"
        )

@router.get("/my-applications", response_model=List[ApplicationResponse])
async def get_my_applications(
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get applications for the current authenticated user - asyncpg path for speed."""
    try:
        rows = await global_pool.fetch(
            """
            SELECT 
                a.id, a.job_id, a.candidate_id, a.status, a.created_at, a.updated_at,
                j.title as job_title, j.company, j.location as job_location, j.domain as job_domain,
                j.salary_min, j.salary_max, j.total_years_required
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE a.candidate_id = $1
            ORDER BY a.created_at DESC
            LIMIT $2 OFFSET $3
            """,
            current_user.id, limit, skip
        )

        applications = []
        for row in rows:
            app_data = {
                "id": row['id'],
                "job_id": row['job_id'],
                "candidate_id": row['candidate_id'],
                "status": row['status'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at'],
                "job": {
                    "id": row['job_id'],
                    "title": row['job_title'],
                    "company": row['company'],
                    "location": row['job_location'],
                    "domain": row['job_domain'],
                    "salary_min": row['salary_min'],
                    "salary_max": row['salary_max'],
                    "total_years_required": row['total_years_required']
                } if row['job_title'] else None
            }
            applications.append(app_data)

        return applications
    except Exception as e:
        print(f"Get my applications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve your applications. Please try again later."
        )

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific application by ID (only if it belongs to the current user)"""
    try:
        application = await application_crud.get(db, id=application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Ensure user can only access their own applications
        if application.candidate_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view own applications"
            )
        
        return application
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get application error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application. Please try again later."
        )

@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    update_data: ApplicationUpdate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update a specific application (only if it belongs to the current user)"""
    try:
        application = await application_crud.get(db, id=application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Ensure user can only update their own applications
        if application.candidate_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update own applications"
            )
        
        updated_application = await application_crud.update(db, db_obj=application, obj_in=update_data.model_dump())
        return updated_application
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update application error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application. Please try again later."
        )

@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a specific application (only if it belongs to the current user)"""
    try:
        application = await application_crud.get(db, id=application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Ensure user can only delete their own applications
        if application.candidate_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete own applications"
            )
        
        await application_crud.remove(db, id=application_id)
        return {"message": "Application deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete application error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete application. Please try again later."
        )

@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    status_update: ApplicationUpdate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update application status (only if it belongs to the current user)"""
    try:
        application = await application_crud.get(db, id=application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Ensure user can only update their own applications
        if application.candidate_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update own applications"
            )
        
        updated_application = await application_crud.update(db, db_obj=application, obj_in=status_update.model_dump())
        return updated_application
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update application status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application status. Please try again later."
        )

# Legacy recalculate-qualification endpoint removed - replaced by assessment-based system
# Status updates now happen automatically based on MCQ assessment scores

@router.get("/recruiters/public")
async def get_available_recruiters(
    db: AsyncSession = Depends(get_db_session)
):
    """Get list of available recruiters for job assignment"""
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT id, full_name, email, company_name, domain
            FROM recruiters 
            WHERE is_active = true
            ORDER BY full_name
        """)
        
        result = await db.execute(query)
        recruiters = result.fetchall()
        
        recruiter_list = []
        for recruiter in recruiters:
            recruiter_list.append({
                "id": recruiter.id,
                "name": recruiter.full_name,
                "email": recruiter.email,
                "company": recruiter.company_name,
                "domain": recruiter.domain
            })
        
        return recruiter_list
        
    except Exception as e:
        print(f"Get recruiters error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recruiters"
        )

@router.get("/public-fast", response_model=List[dict])
async def get_applications_fast(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by candidate name, email, job title"),
    recruiter_id: Optional[int] = Query(None, description="Filter by assigned recruiter ID"),
    qualification_filter: Optional[str] = Query(None, description="Filter by qualification")
):
    """Get applications with fast performance - no authentication required"""
    import time
    start_time = time.time()
    
    try:
        from config.connection_pool import global_pool
        
        # Build dynamic WHERE clause for filtering
        where_conditions = []
        params = []
        param_count = 0
        
        # Add qualification filters
        if qualification_filter:
            if qualification_filter.lower() == "qualified":
                where_conditions.append("a.is_qualified = true")
            elif qualification_filter.lower() == "rejected":
                where_conditions.append("a.is_qualified = false")
        
        # Add recruiter filter (most important for job assignment)
        if recruiter_id is not None:
            param_count += 1
            where_conditions.append(f"j.recruiter_id = ${param_count}")
            params.append(recruiter_id)
        
        # Add status filter
        if status_filter:
            param_count += 1
            where_conditions.append(f"a.status = ${param_count}")
            params.append(status_filter)
        
        # Add search filter
        if search:
            param_count += 1
            where_conditions.append(f"""
                (LOWER(c.name) LIKE LOWER(${param_count}) OR 
                 LOWER(c.email) LIKE LOWER(${param_count}) OR 
                 LOWER(j.title) LIKE LOWER(${param_count}))
            """)
            params.append(f"%{search}%")
        
        # Add pagination parameters
        param_count += 1
        limit_param = param_count
        param_count += 1
        skip_param = param_count
        params.extend([limit, skip])
        
        # Build the final optimized query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
            SELECT 
                a.id, a.job_id, a.candidate_id, a.status, a.created_at, a.updated_at,
                a.candidate_score, a.is_qualified,
                c.name as candidate_name, c.email as candidate_email, c.location as candidate_location,
                c.domain as candidate_domain, c.expected_salary_min, c.expected_salary_max,
                j.title as job_title, j.company, j.location as job_location, j.domain as job_domain,
                j.salary_min, j.salary_max, j.total_years_required, j.threshold_score, j.recruiter_id,
                r.full_name as recruiter_name, r.email as recruiter_email
            FROM applications a
            LEFT JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN recruiters r ON j.recruiter_id = r.id
            WHERE {where_clause}
            ORDER BY a.created_at DESC
            LIMIT ${limit_param} OFFSET ${skip_param}
        """
        
        # Execute using global connection pool for maximum performance
        rows = await global_pool.fetch(query, *params)
        
        # Convert to response format efficiently
        applications = []
        for row in rows:
            app_data = {
                "id": row['id'],
                "job_id": row['job_id'],
                "candidate_id": row['candidate_id'],
                "status": row['status'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
                "candidate_score": row['candidate_score'],
                "is_qualified": row['is_qualified'],
                "candidate": {
                    "id": row['candidate_id'],
                    "name": row['candidate_name'],
                    "email": row['candidate_email'],
                    "location": row['candidate_location'],
                    "domain": row['candidate_domain'],
                    "expected_salary_min": row['expected_salary_min'],
                    "expected_salary_max": row['expected_salary_max']
                },
                "job": {
                    "id": row['job_id'],
                    "title": row['job_title'],
                    "company": row['company'],
                    "location": row['job_location'],
                    "domain": row['job_domain'],
                    "salary_min": row['salary_min'],
                    "salary_max": row['salary_max'],
                    "total_years_required": row['total_years_required'],
                    "threshold_score": row['threshold_score'],
                    "recruiter_id": row['recruiter_id']
                },
                "recruiter": {
                    "id": row['recruiter_id'],
                    "full_name": row['recruiter_name'],
                    "email": row['recruiter_email']
                } if row['recruiter_name'] else None
            }
            applications.append(app_data)
        
        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(applications)} applications for recruiter {recruiter_id or 'all'} (took {elapsed:.3f}s)")
        return applications
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Error getting fast applications: {e} (took {elapsed:.3f}s)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get applications"
        )
