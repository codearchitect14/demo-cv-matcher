"""
Sub-recruiter specific actions and endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
import asyncio

from config.database import get_db_session
from middleware.recruiter_auth import get_current_recruiter, RecruiterContext
from services.integrated_notification_service import integrated_notification_service
from sqlalchemy import text

router = APIRouter(tags=["Sub-Recruiter Actions"])
logger = logging.getLogger(__name__)

class StatusUpdateRequest:
    def __init__(self, application_id: int, new_status: str, notes: Optional[str] = None):
        self.application_id = application_id
        self.new_status = new_status
        self.notes = notes

@router.put("/applications/{application_id}/status")
async def update_application_status(
    application_id: int,
    new_status: str,
    notes: Optional[str] = None,
    recruiter_context: RecruiterContext = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update application status - Sub-recruiter only
    This endpoint allows sub-recruiters to update candidate application statuses
    for jobs assigned to them.
    """
    try:
        # Verify recruiter has access to this application
        application_query = await db.execute(text("""
            SELECT a.id, a.candidate_id, a.job_id, a.status, 
                   j.title as job_title, j.recruiter_id, j.company_id,
                   c.name as candidate_name, c.email as candidate_email
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN candidates c ON a.candidate_id = c.id
            WHERE a.id = :application_id
        """), {"application_id": application_id})
        
        application_result = application_query.fetchone()
        
        if not application_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check if the job is assigned to this recruiter
        if application_result[5] != recruiter_context.recruiter_id:  # recruiter_id
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update applications for jobs assigned to you"
            )
        
        # Check if recruiter belongs to the same company
        if application_result[6] != recruiter_context.company_id:  # company_id
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Application does not belong to your company"
            )
        
        # Validate status transition
        current_status = application_result[3]
        valid_transitions = {
            "APPLIED": ["INTERVIEW_SCHEDULED", "REJECTED"],
            "INTERVIEW_SCHEDULED": ["REJECTED", "OFFERED"],
            "OFFERED": ["REJECTED", "HIRED"],
            "REJECTED": [],  # Cannot change from rejected
            "HIRED": []  # Cannot change from hired
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status} to {new_status}"
            )
        
        # Update application status
        await db.execute(text("""
            UPDATE applications 
            SET status = :new_status, updated_at = NOW()
            WHERE id = :application_id
        """), {
            "new_status": new_status,
            "application_id": application_id
        })
        
        await db.commit()
        
        # Get company name
        company_query = await db.execute(text("""
            SELECT name FROM companies WHERE id = :company_id
        """), {"company_id": recruiter_context.company_id})
        company_result = company_query.fetchone()
        company_name = company_result[0] if company_result else "Your Company"
        
        # Prepare notification data
        candidate_name = application_result[7]
        candidate_email = application_result[8]
        job_title = application_result[4]
        
        # Determine next steps based on status
        next_steps = None
        if new_status == "INTERVIEW_SCHEDULED":
            next_steps = "We will contact you shortly to schedule an interview. Please ensure your contact information is up to date."
        elif new_status == "REJECTED":
            next_steps = "While we won't be moving forward with your application for this position, we encourage you to apply for other suitable roles."
        elif new_status == "OFFERED":
            next_steps = "Congratulations! We are excited to extend an offer to you. Please review the offer details and respond within the specified timeframe."
        elif new_status == "HIRED":
            next_steps = "Welcome to the team! We are thrilled to have you join us. You will receive onboarding information shortly."
        
        # Send status update notifications (non-blocking)
        async def send_status_update_notifications():
            try:
                # Get candidate user ID (assuming candidates have user accounts)
                candidate_user_query = await db.execute(text("""
                    SELECT id FROM candidates WHERE email = :candidate_email
                """), {"candidate_email": candidate_email})
                candidate_user_result = candidate_user_query.fetchone()
                candidate_user_id = candidate_user_result[0] if candidate_user_result else None
                
                results = await integrated_notification_service.send_candidate_status_update(
                    candidate_email=candidate_email,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    new_status=new_status,
                    company_name=company_name,
                    recruiter_name=recruiter_context.full_name,
                    candidate_user_id=candidate_user_id or 0,  # Fallback if no user ID
                    admin_user_id=recruiter_context.recruiter_id,  # Notify the recruiter who made the change
                    next_steps=next_steps
                )
                
                logger.info(f"Status update notifications sent: {results}")
                
            except Exception as e:
                logger.error(f"Failed to send status update notifications: {e}")
        
        # Send notifications asynchronously
        asyncio.create_task(send_status_update_notifications())
        
        logger.info(f"Sub-recruiter {recruiter_context.recruiter_id} updated application {application_id} status to {new_status}")
        
        return {
            "message": "Application status updated successfully",
            "application_id": application_id,
            "old_status": current_status,
            "new_status": new_status,
            "candidate_name": candidate_name,
            "job_title": job_title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application status"
        )

@router.get("/my-assigned-jobs")
async def get_my_assigned_jobs(
    recruiter_context: RecruiterContext = Depends(get_current_recruiter)
):
    """
    Get jobs assigned to the current sub-recruiter (FAST - uses connection pool)
    """
    try:
        # Verify this is a sub-recruiter (not admin)
        if recruiter_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint is for sub-recruiters only"
            )
        
        # Use global connection pool for better performance (no new connection needed!)
        from config.connection_pool import global_pool
        
        # Get assigned jobs WITH application counts
        # Handle case where company_id might be None
        if recruiter_context.company_id:
            jobs = await global_pool.fetch("""
                SELECT j.id, j.title, j.job_description, j.location, j.company,
                       j.salary_min, j.salary_max, j.domain, j.total_years_required,
                       j.is_active, j.created_at, j.recruiter_id,
                       COUNT(a.id) as total_applications,
                       COUNT(CASE WHEN a.status = 'APPLIED' THEN 1 END) as applied_count,
                       COUNT(CASE WHEN a.status = 'INTERVIEW_SCHEDULED' THEN 1 END) as interview_count,
                       COUNT(CASE WHEN a.status = 'REJECTED' THEN 1 END) as rejected_count,
                       COUNT(CASE WHEN a.status = 'HIRED' THEN 1 END) as hired_count
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id
                WHERE j.recruiter_id = $1 
                AND j.company_id = $2
                AND j.is_active = true
                GROUP BY j.id, j.title, j.job_description, j.location, j.company,
                         j.salary_min, j.salary_max, j.domain, j.total_years_required,
                         j.is_active, j.created_at, j.recruiter_id
                ORDER BY j.created_at DESC
                LIMIT 50
            """, recruiter_context.recruiter_id, recruiter_context.company_id)
        else:
            # Fallback if company_id is None
            jobs = await global_pool.fetch("""
                SELECT j.id, j.title, j.job_description, j.location, j.company,
                       j.salary_min, j.salary_max, j.domain, j.total_years_required,
                       j.is_active, j.created_at, j.recruiter_id,
                       COUNT(a.id) as total_applications,
                       COUNT(CASE WHEN a.status = 'APPLIED' THEN 1 END) as applied_count,
                       COUNT(CASE WHEN a.status = 'INTERVIEW_SCHEDULED' THEN 1 END) as interview_count,
                       COUNT(CASE WHEN a.status = 'REJECTED' THEN 1 END) as rejected_count,
                       COUNT(CASE WHEN a.status = 'HIRED' THEN 1 END) as hired_count
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id
                WHERE j.recruiter_id = $1 
                AND j.is_active = true
                GROUP BY j.id, j.title, j.job_description, j.location, j.company,
                         j.salary_min, j.salary_max, j.domain, j.total_years_required,
                         j.is_active, j.created_at, j.recruiter_id
                ORDER BY j.created_at DESC
                LIMIT 50
            """, recruiter_context.recruiter_id)
        
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                "id": job[0],
                "title": job[1],
                "description": job[2],  # job_description
                "location": job[3],
                "company": job[4],
                "salary_min": job[5],
                "salary_max": job[6],
                "domain": job[7],
                "total_years_required": job[8],
                "is_active": job[9],
                "created_at": job[10],
                "recruiter_id": job[11],
                "applications": {
                    "total": job[12] or 0,  # total_applications
                    "applied": job[13] or 0,  # applied_count
                    "interview": job[14] or 0,  # interview_count
                    "rejected": job[15] or 0,  # rejected_count
                    "hired": job[16] or 0  # hired_count
                }
            })
        
        # Calculate total applications across all jobs
        total_apps = sum(job['applications']['total'] for job in jobs_data)
        
        logger.info(f"[MY-JOBS] Recruiter {recruiter_context.recruiter_id} ({recruiter_context.email}) - Found {len(jobs_data)} jobs with {total_apps} total applications")
        
        return {
            "jobs": jobs_data,
            "total_jobs": len(jobs_data),
            "total_applications": total_apps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching assigned jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch assigned jobs"
        )

@router.get("/jobs/{job_id}/applications")
async def get_job_applications(
    job_id: int,
    recruiter_context: RecruiterContext = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get applications for a specific job assigned to the current sub-recruiter
    """
    try:
        # Verify this is a sub-recruiter
        if recruiter_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint is for sub-recruiters only"
            )
        
        # Verify job is assigned to this recruiter
        job_query = await db.execute(text("""
            SELECT id, title, recruiter_id, company_id
            FROM jobs 
            WHERE id = :job_id
        """), {"job_id": job_id})
        
        job_result = job_query.fetchone()
        
        if not job_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        if job_result[2] != recruiter_context.recruiter_id:  # recruiter_id
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view applications for jobs assigned to you"
            )
        
        if job_result[3] != recruiter_context.company_id:  # company_id
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Job does not belong to your company"
            )
        
        # Get applications for this job
        applications_query = await db.execute(text("""
            SELECT a.id, a.candidate_id, a.status, a.created_at, a.updated_at,
                   c.name as candidate_name, c.email as candidate_email
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.id
            WHERE a.job_id = :job_id
            ORDER BY a.created_at DESC
        """), {"job_id": job_id})
        
        applications = applications_query.fetchall()
        
        applications_data = []
        for app in applications:
            applications_data.append({
                "id": app[0],
                "candidate_id": app[1],
                "status": app[2],
                "created_at": app[3],
                "updated_at": app[4],
                "candidate_name": app[5],
                "candidate_email": app[6]
            })
        
        return {
            "job_id": job_id,
            "job_title": job_result[1],
            "applications": applications_data,
            "total_applications": len(applications_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch job applications"
        )
