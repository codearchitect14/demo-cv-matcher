"""
Job assignment management endpoints for admin functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
import asyncio

from config.database import get_db_session
from db.crud.job import job as job_crud
from schemas.job import JobResponse
from middleware.recruiter_auth import get_current_recruiter as get_recruiter_context, RecruiterContext
from services.integrated_notification_service import integrated_notification_service
from sqlalchemy import text

router = APIRouter(tags=["Job Assignments"])
logger = logging.getLogger(__name__)

@router.put("/{job_id}/assign/{recruiter_id}")
async def assign_job_to_recruiter(
    job_id: int,
    recruiter_id: int,
    db: AsyncSession = Depends(get_db_session),
    recruiter_context: RecruiterContext = Depends(get_recruiter_context)
):
    """Assign a job to a specific recruiter - Admin only"""
    try:
        # Only admins can reassign jobs
        if not recruiter_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required to assign jobs"
            )
        
        # Verify job exists and assign to recruiter
        updated_job = await job_crud.assign_job_to_recruiter(db, job_id, recruiter_id)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get assigned recruiter details
        recruiter_query = await db.execute(text("SELECT full_name, email FROM recruiters WHERE id = :recruiter_id"), 
                                         {"recruiter_id": recruiter_id})
        recruiter_result = recruiter_query.fetchone()
        
        # Get company name
        company_name = "Your Company"  # Default fallback
        company_query = await db.execute(text("SELECT name FROM companies WHERE id = :company_id"), 
                                       {"company_id": updated_job.company_id})
        company_result = company_query.fetchone()
        if company_result:
            company_name = company_result[0]
        
        # Send job assignment notifications using integrated service (non-blocking)
        if recruiter_result:
            async def send_job_assignment_notifications():
                try:
                    results = await integrated_notification_service.send_job_assignment_notifications(
                        recruiter_email=recruiter_result[1],  # email
                        recruiter_name=recruiter_result[0],   # full_name
                        job_title=updated_job.title,
                        company_name=company_name,
                        job_id=job_id,
                        admin_name=recruiter_context.full_name,
                        recruiter_user_id=recruiter_id,
                        admin_user_id=recruiter_context.recruiter_id
                    )
                    logger.info(f"Job assignment notifications sent: {results}")
                except Exception as e:
                    logger.error(f"Failed to send job assignment notifications: {e}")
            
            # Send notifications asynchronously (non-blocking)
            asyncio.create_task(send_job_assignment_notifications())
        
        logger.info(f"Admin assigned job {job_id} to recruiter {recruiter_id}")
        
        return {
            "message": "Job assigned successfully",
            "job_id": job_id,
            "recruiter_id": recruiter_id,
            "job_title": updated_job.title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign job"
        )

@router.put("/{job_id}/unassign")
async def unassign_job(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
    recruiter_context: RecruiterContext = Depends(get_recruiter_context)
):
    """Remove recruiter assignment from a job - Admin only"""
    try:
        # Only admins can unassign jobs
        if not recruiter_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required to unassign jobs"
            )
        
        # Verify job exists and unassign
        updated_job = await job_crud.unassign_job(db, job_id)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        logger.info(f"Admin unassigned job {job_id}")
        
        return {
            "message": "Job unassigned successfully",
            "job_id": job_id,
            "job_title": updated_job.title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unassigning job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unassign job"
        )

@router.get("/unassigned", response_model=List[JobResponse])
async def get_unassigned_jobs(
    db: AsyncSession = Depends(get_db_session),
    recruiter_context: RecruiterContext = Depends(get_recruiter_context),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get jobs that are not assigned to any recruiter - Admin only"""
    try:
        # Only admins can view unassigned jobs
        if not recruiter_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required to view unassigned jobs"
            )
        
        # Get unassigned jobs using CRUD method
        unassigned_jobs = await job_crud.get_unassigned_jobs(db, skip, limit)
        
        # Convert to response format
        jobs = []
        for job in unassigned_jobs:
            jobs.append(JobResponse(
                id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                domain=job.domain,
                total_years_required=job.total_years_required,
                job_description=job.job_description,
                is_active=job.is_active,
                threshold_score=getattr(job, 'threshold_score', 70),
                recruiter_id=job.recruiter_id,
                created_at=job.created_at,
                updated_at=job.updated_at,
                mandatory_skills=[]  # Skip skills for performance
            ))
        
        logger.info(f"Retrieved {len(jobs)} unassigned jobs for admin")
        return jobs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unassigned jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unassigned jobs"
        )

@router.get("/stats")
async def get_job_assignment_stats(
    db: AsyncSession = Depends(get_db_session),
    recruiter_context: RecruiterContext = Depends(get_recruiter_context)
):
    """Get job assignment statistics - Admin only"""
    try:
        # Only admins can view assignment stats
        if not recruiter_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required to view assignment statistics"
            )
        
        from config.connection_pool import global_pool
        
        # Get assignment statistics using optimized queries
        stats_query = """
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(recruiter_id) as assigned_jobs,
                COUNT(*) - COUNT(recruiter_id) as unassigned_jobs,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_jobs,
                COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_jobs
            FROM jobs
        """
        
        recruiter_stats_query = """
            SELECT 
                r.id,
                r.full_name,
                r.email,
                COUNT(j.id) as job_count,
                COUNT(CASE WHEN j.is_active = true THEN 1 END) as active_job_count
            FROM recruiters r
            LEFT JOIN jobs j ON r.id = j.recruiter_id
            WHERE r.is_active = true
            GROUP BY r.id, r.full_name, r.email
            ORDER BY job_count DESC
        """
        
        # Execute queries using global pool
        stats_row = await global_pool.fetchrow(stats_query)
        recruiter_rows = await global_pool.fetch(recruiter_stats_query)
        
        return {
            "total_jobs": stats_row['total_jobs'],
            "assigned_jobs": stats_row['assigned_jobs'],
            "unassigned_jobs": stats_row['unassigned_jobs'],
            "active_jobs": stats_row['active_jobs'],
            "inactive_jobs": stats_row['inactive_jobs'],
            "recruiters": [
                {
                    "recruiter_id": row['id'],
                    "recruiter_name": row['full_name'],
                    "recruiter_email": row['email'],
                    "total_jobs": row['job_count'],
                    "active_jobs": row['active_job_count']
                }
                for row in recruiter_rows
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assignment stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get assignment statistics"
        )
