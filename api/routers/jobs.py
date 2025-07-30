#Today's date: 25/07/2025

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from models.candidate import Candidate
from config.database import get_db_session
from models.job import Job, JobMandatorySkill
from db.crud.job import job as job_crud
from db.crud.application import application as application_crud
from api.routers.auth import get_current_user
from schemas.job import JobCreate, JobUpdate, JobResponse, JobMandatorySkillCreate
from sqlalchemy import select

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new job posting"""
    try:
        # Extract mandatory skills from the request
        mandatory_skills = job_data.mandatory_skills
        
        # Create job without mandatory skills first
        job_create_data = job_data.dict(exclude={'mandatory_skills'})
        job = await job_crud.create(db, obj_in=JobCreate(**job_create_data))
        
        # Add mandatory skills separately
        for skill_data in mandatory_skills:
            await job_crud.add_mandatory_skill(db, job_id=job.id, skill_data=skill_data.dict())
        
        # Get the job with loaded relationships
        job_with_relations = await job_crud.get_with_mandatory_skills(db, job.id)
        return job_with_relations
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Create job error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job. Please try again later."
        )

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get job details by ID"""
    try:
        job = await job_crud.get_with_mandatory_skills(db, id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        return job
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Get job error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job. Please try again later."
        )

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update job posting"""
    try:
        job = await job_crud.get(db, id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Extract mandatory skills from the request
        mandatory_skills = job_data.mandatory_skills
        
        # Update job fields (excluding mandatory_skills)
        job_update_data = job_data.dict(exclude={'mandatory_skills'}, exclude_unset=True)
        job = await job_crud.update(db, db_obj=job, obj_in=JobUpdate(**job_update_data))
        
        # Handle mandatory skills if provided
        if mandatory_skills is not None:
            # For now, just add new skills without clearing old ones
            # This avoids the complex deletion logic that might cause issues
            for skill_data in mandatory_skills:
                try:
                    await job_crud.add_mandatory_skill(db, job_id=job.id, skill_data=skill_data.dict())
                except Exception as skill_error:
                    # If skill already exists, skip it
                    if "already exists" not in str(skill_error).lower():
                        raise skill_error
        
        # Get the job with loaded relationships
        job_with_relations = await job_crud.get_with_mandatory_skills(db, job.id)
        return job_with_relations
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Update job error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job. Please try again later."
        )

@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete job posting"""
    try:
        job = await job_crud.get(db, id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        await job_crud.delete(db, id=job_id)
        return {"message": "Job deleted successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Delete job error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job. Please try again later."
        )

@router.post("/{job_id}/mandatory-skills")
async def add_mandatory_skill(
    job_id: int,
    skill_data: JobMandatorySkillCreate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Add mandatory skill to job"""
    try:
        job = await job_crud.get(db, id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Convert Pydantic model to dict
        skill_dict = skill_data.dict()
        skill = await job_crud.add_mandatory_skill(
            db, job_id=job_id, skill_data=skill_dict
        )
        return skill
    except HTTPException:
        raise
    except Exception as e:
        print(f"Add mandatory skill error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add mandatory skill. Please try again later."
        )

@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    location: Optional[str] = Query(None, description="Filter by location"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    salary_min: Optional[int] = Query(None, ge=0, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, ge=0, description="Maximum salary"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session)
):
    """List jobs with filters"""
    try:
        filters = {}
        if location:
            filters["location"] = location
        if domain:
            filters["domain"] = domain
        if salary_min is not None:
            filters["salary_min"] = salary_min
        if salary_max is not None:
            filters["salary_max"] = salary_max
        
        jobs = await job_crud.get_multi_with_filters(
            db, filters=filters, skip=skip, limit=limit
        )
        return jobs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}"
        )

@router.get("/{job_id}/applications")
async def get_job_applications(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get applications for a job"""
    try:
        job = await job_crud.get(db, id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        applications = await application_crud.get_by_job(
            db, job_id=job_id, skip=skip, limit=limit
        )
        return applications
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {str(e)}"
        )