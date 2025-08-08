#Today's date: 25/07/2025

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from models.candidate import Candidate
from models.recruiter import Recruiter
from config.database import get_db_session
from models.job import Job, JobMandatorySkill
from db.crud.job import job as job_crud
from db.crud.application import application as application_crud
from api.routers.auth import get_current_user, get_current_recruiter
from schemas.job import JobCreate, JobUpdate, JobResponse, JobResponseSimple, JobMandatorySkillCreate, JobSearchFilter
from sqlalchemy import select, text
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Jobs"])

@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new job posting"""
    try:
        # Create the job
        job = await job_crud.create(db, obj_in=job_data)
        
        # Add mandatory skills if provided
        if job_data.mandatory_skills:
            for skill_data in job_data.mandatory_skills:
                await job_crud.add_mandatory_skill(db, job_id=job.id, skill_data=skill_data.dict())
        
        # Get the job with loaded relationships
        job_with_skills = await job_crud.get_with_mandatory_skills(db, job.id)
        return job_with_skills
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create job error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job. Please try again later."
        )

@router.post("/recruiter", response_model=JobResponse)
async def create_job_as_recruiter(
    job_data: JobCreate,
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new job posting as a recruiter"""
    try:
        # Create the job with recruiter ID
        job_dict = job_data.dict()
        job_dict["recruiter_id"] = current_recruiter.id
        job = await job_crud.create(db, obj_in=JobCreate(**job_dict))
        
        # Add mandatory skills if provided
        if job_data.mandatory_skills:
            for skill_data in job_data.mandatory_skills:
                await job_crud.add_mandatory_skill(db, job_id=job.id, skill_data=skill_data.dict())
        
        # Get the job with loaded relationships
        job_with_skills = await job_crud.get_with_mandatory_skills(db, job.id)
        return job_with_skills
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create job as recruiter error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job. Please try again later."
        )

@router.post("/public", response_model=JobResponse)
async def create_job_public(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new job posting (public endpoint for testing)"""
    try:
        # Use default recruiter ID for public endpoint
        job_dict = job_data.dict()
        job_dict["recruiter_id"] = 1  # Default recruiter ID
        job = await job_crud.create(db, obj_in=JobCreate(**job_dict))
        
        # Add mandatory skills if provided
        if job_data.mandatory_skills:
            for skill_data in job_data.mandatory_skills:
                await job_crud.add_mandatory_skill(db, job_id=job.id, skill_data=skill_data.dict())
        
        # Get the job with loaded relationships
        job_with_skills = await job_crud.get_with_mandatory_skills(db, job.id)
        return job_with_skills
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create job public error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job. Please try again later."
        )

@router.get("/public", response_model=List[JobResponseSimple])
async def list_jobs_public(
    location: Optional[str] = Query(None, description="Filter by location"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    salary_min: Optional[int] = Query(None, ge=0, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, ge=0, description="Maximum salary"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session)
):
    """List jobs with filters (public endpoint)"""
    try:
        # Use a simpler query without loading relationships to avoid prepared statement issues
        query = select(Job)
        
        # Apply filters
        if location:
            query = query.where(Job.location == location)
        if domain:
            query = query.where(Job.domain == domain)
        if salary_min is not None:
            query = query.where(Job.salary_min >= salary_min)
        if salary_max is not None:
            query = query.where(Job.salary_max <= salary_max)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return jobs
    except Exception as e:
        print(f"Error in list_jobs_public: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}"
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
    """List jobs with filters using raw SQL to avoid prepared statements"""
    try:
        # Build raw SQL query to avoid prepared statements
        query = """
            SELECT j.*, jms.skill, jms.min_experience, jms.id as skill_id, 
                   jms.created_at as skill_created_at, jms.updated_at as skill_updated_at
            FROM jobs j
            LEFT JOIN job_mandatory_skills jms ON j.id = jms.job_id
            WHERE 1=1
        """
        params = {}
        
        if location:
            query += " AND j.location = :location"
            params["location"] = location
        
        if domain:
            query += " AND j.domain = :domain"
            params["domain"] = domain
        
        if salary_min is not None:
            query += " AND j.salary_min >= :salary_min"
            params["salary_min"] = salary_min
        
        if salary_max is not None:
            query += " AND j.salary_max <= :salary_max"
            params["salary_max"] = salary_max
        
        query += " ORDER BY j.created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = skip
        
        # Execute raw SQL
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        
        # Group by job
        jobs = {}
        for row in rows:
            job_id = row.id
            if job_id not in jobs:
                jobs[job_id] = {
                    "id": row.id,
                    "title": row.title,
                    "company": row.company,
                    "location": row.location,
                    "salary_min": row.salary_min,
                    "salary_max": row.salary_max,
                    "domain": row.domain,
                    "total_years_required": row.total_years_required,
                    "job_description": row.job_description,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "mandatory_skills": []
                }
            
            if row.skill:
                jobs[job_id]["mandatory_skills"].append({
                    "id": row.skill_id,
                    "skill": row.skill,
                    "min_experience": row.min_experience,
                    "job_id": job_id,
                    "created_at": row.skill_created_at,
                    "updated_at": row.skill_updated_at
                })
        
        return list(jobs.values())
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs. Please try again later."
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

@router.get("/recruiter-jobs", response_model=List[JobResponse])
async def get_recruiter_jobs(
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all jobs posted by the current recruiter"""
    try:
        jobs = await job_crud.get_by_recruiter(db, recruiter_id=current_recruiter.id)
        return jobs
    except Exception as e:
        print(f"Get recruiter jobs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recruiter jobs. Please try again later."
        )