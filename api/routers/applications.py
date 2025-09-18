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
from schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from middleware.recruiter_auth import get_current_recruiter, RecruiterContext

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
        
        # Build the final query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
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
            LIMIT :limit OFFSET :skip
        """)
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        response_applications = []
        for row in rows:
            app_data = {
                "id": row[0],
                "job_id": row[1],
                "candidate_id": row[2],
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "candidate_score": float(row[6]) if row[6] else None,
                "is_qualified": row[7]
            }
            
            # Add candidate data if available
            if row[8]:  # candidate_name exists
                app_data["candidate"] = {
                    "id": row[2],  # candidate_id
                    "name": row[8],
                    "email": row[9],
                    "location": row[10],
                    "domain": row[11],
                    "expected_salary_min": row[12],
                    "expected_salary_max": row[13]
                }
            
            # Add job data if available
            if row[14]:  # job_title exists
                app_data["job"] = {
                    "id": row[1],  # job_id
                    "title": row[14],
                    "company": row[15],
                    "location": row[16],
                    "domain": row[17],
                    "salary_min": row[18],
                    "salary_max": row[19],
                    "total_years_required": row[20],
                    "threshold_score": row[21],
                    "recruiter_id": row[22]
                }
                
                # Add recruiter data if available
                if row[23]:  # recruiter_name exists
                    app_data["recruiter"] = {
                        "id": row[22],  # recruiter_id
                        "name": row[23],
                        "email": row[24]
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
        
        # Build the final query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
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
            LIMIT :limit OFFSET :skip
        """)
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        response_applications = []
        for row in rows:
            app_data = {
                "id": row[0],
                "job_id": row[1],
                "candidate_id": row[2],
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "candidate_score": float(row[6]) if row[6] else None,
                "is_qualified": row[7]
            }
            
            # Add candidate data if available
            if row[8]:  # candidate_name exists
                app_data["candidate"] = {
                    "id": row[2],  # candidate_id
                    "name": row[8],
                    "email": row[9],
                    "location": row[10],
                    "domain": row[11],
                    "expected_salary_min": row[12],
                    "expected_salary_max": row[13]
                }
            
            # Add job data if available
            if row[14]:  # job_title exists
                app_data["job"] = {
                    "id": row[1],  # job_id
                    "title": row[14],
                    "company": row[15],
                    "location": row[16],
                    "domain": row[17],
                    "salary_min": row[18],
                    "salary_max": row[19],
                    "total_years_required": row[20],
                    "threshold_score": row[21],
                    "recruiter_id": row[22]
                }
                
                # Add recruiter data if available
                if row[23]:  # recruiter_name exists
                    app_data["recruiter"] = {
                        "id": row[22],  # recruiter_id
                        "name": row[23],
                        "email": row[24]
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

@router.post("/public", response_model=ApplicationResponse)
async def create_application_public(
    application_data: ApplicationCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create application for testing (public endpoint)"""
    try:
        print(f"DEBUG: Creating application - candidate_id: {application_data.candidate_id}, job_id: {application_data.job_id}")
        
        # Ensure candidate_id is provided for public endpoint
        if not application_data.candidate_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="candidate_id is required for public endpoint"
            )
        
        # Check if already applied
        existing_application = await application_crud.get_by_candidate_and_job(
            db, candidate_id=application_data.candidate_id, job_id=application_data.job_id
        )
        
        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already applied for this job"
            )
        
        # Create application with proper status handling
        application_data_dict = application_data.model_dump()
        # Ensure status is properly set - convert enum to string value
        if 'status' in application_data_dict and application_data_dict['status']:
            # If status is an enum object, convert it to its value
            if hasattr(application_data_dict['status'], 'value'):
                application_data_dict['status'] = application_data_dict['status'].value
            elif isinstance(application_data_dict['status'], ApplicationStatusEnum):
                application_data_dict['status'] = application_data_dict['status'].value
        else:
            application_data_dict['status'] = ApplicationStatusEnum.APPLIED.value
        
        application = await application_crud.create(db, obj_in=application_data_dict)
        
        return application
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
    """Get applications for the current authenticated user"""
    try:
        # Use raw SQL to avoid enum issues
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                a.id, a.job_id, a.candidate_id, a.status, a.created_at, a.updated_at,
                j.title as job_title, j.company, j.location as job_location, j.domain as job_domain,
                j.salary_min, j.salary_max, j.total_years_required
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE a.candidate_id = :candidate_id
            ORDER BY a.created_at DESC
            LIMIT :limit OFFSET :skip
        """)
        
        result = await db.execute(query, {
            "candidate_id": current_user.id,
            "limit": limit,
            "skip": skip
        })
        rows = result.fetchall()
        
        applications = []
        for row in rows:
            app_data = {
                "id": row[0],
                "job_id": row[1],
                "candidate_id": row[2],
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "job": {
                    "id": row[1],
                    "title": row[6],
                    "company": row[7],
                    "location": row[8],
                    "domain": row[9],
                    "salary_min": row[10],
                    "salary_max": row[11],
                    "total_years_required": row[12]
                } if row[6] else None
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

@router.post("/{application_id}/recalculate-qualification")
async def recalculate_qualification(
    application_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Manually trigger qualification recalculation for an application"""
    try:
        from sqlalchemy import text
        from services.qualification_service import qualification_service
        
        # Get application data
        app_query = text("""
            SELECT id, candidate_id, job_id 
            FROM applications WHERE id = :application_id
        """)
        result = await db.execute(app_query, {"application_id": application_id})
        application = result.fetchone()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Recalculate qualification
        success = await qualification_service.update_application_qualification(
            db, application_id, application[1], application[2]
        )
        
        if success:
            # Get updated application data
            updated_query = text("""
                SELECT id, job_id, candidate_id, status, candidate_score, is_qualified, created_at, updated_at
                FROM applications WHERE id = :application_id
            """)
            
            result = await db.execute(updated_query, {"application_id": application_id})
            updated_row = result.fetchone()
            
            if updated_row:
                return {
                    "id": updated_row[0],
                    "job_id": updated_row[1],
                    "candidate_id": updated_row[2],
                    "status": updated_row[3],
                    "candidate_score": float(updated_row[4]) if updated_row[4] else None,
                    "is_qualified": updated_row[5],
                    "created_at": updated_row[6],
                    "updated_at": updated_row[7],
                    "message": "Qualification recalculated successfully"
                }
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recalculate qualification"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Recalculate qualification error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recalculate qualification: {str(e)}"
        )

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
