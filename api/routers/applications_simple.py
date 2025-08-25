from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db_session
from models.application import Application
from models.candidate import Candidate
from models.job import Job
from db.crud.application import application as application_crud
from api.routers.auth import get_current_user
from schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse

router = APIRouter(tags=["Applications"])

@router.get("/public", response_model=List[dict])
async def get_all_applications_public(
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, description="Filter by status")
):
    """Get all applications with candidate and job details (public endpoint for management)"""
    try:
        # Get all applications using CRUD function
        applications = await application_crud.get_multi(db, skip=skip, limit=limit)
        
        # Convert to response format with full details
        response_applications = []
        for app in applications:
            app_data = {
                "id": app.id,
                "job_id": app.job_id,
                "candidate_id": app.candidate_id,
                "status": app.status,
                "created_at": app.created_at,
                "updated_at": app.updated_at
            }
            
            # Get candidate details using separate query
            if app.candidate_id:
                from sqlalchemy import select
                candidate_query = select(Candidate).where(Candidate.id == app.candidate_id)
                candidate_result = await db.execute(candidate_query)
                candidate = candidate_result.scalar_one_or_none()
                
                if candidate:
                    app_data["candidate"] = {
                        "id": candidate.id,
                        "name": candidate.name,
                        "email": candidate.email,
                        "location": candidate.location,
                        "domain": candidate.domain,
                        "total_years_experience": candidate.total_years_experience,
                        "expected_salary_min": candidate.expected_salary_min,
                        "expected_salary_max": candidate.expected_salary_max
                    }
            
            # Get job details using separate query
            if app.job_id:
                from sqlalchemy import select
                job_query = select(Job).where(Job.id == app.job_id)
                job_result = await db.execute(job_query)
                job = job_result.scalar_one_or_none()
                
                if job:
                    app_data["job"] = {
                        "id": job.id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "domain": job.domain,
                        "salary_min": job.salary_min,
                        "salary_max": job.salary_max,
                        "total_years_required": job.total_years_required
                    }
            
            response_applications.append(app_data)
        
        return response_applications
    except Exception as e:
        print(f"Get all applications error: {e}")
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
        application = await application_crud.get(db, id=application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        application = await application_crud.update(
            db, db_obj=application, obj_in=status_update
        )
        
        return application
    except HTTPException:
        raise
    except Exception as e:
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
        
        # Create application
        application_data_dict = application_data.dict()
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
