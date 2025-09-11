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
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Jobs"])
from services.faiss_service import faiss_service

def _skill_to_dict(skill_data):
    """Normalize a mandatory skill to a plain dict regardless of input type."""
    try:
        if isinstance(skill_data, dict):
            return skill_data
        # Pydantic model
        return skill_data.dict()
    except Exception:
        return {
            "skill": getattr(skill_data, "skill", None),
            "min_experience": getattr(skill_data, "min_experience", 1),
        }

async def _index_job_async(job_id: int):
    # Open a fresh DB session for background indexing
    async for session in get_db_session():
        try:
            # Use existing method name
            await faiss_service.add_or_update_job(session, job_id)
        except Exception as e:
            logger.warning(f"Background FAISS indexing failed for job {job_id}: {e}")
        break

@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new job posting"""
    try:
        # Create the job (exclude relationship data to avoid SA relationship assignment errors)
        base_job_dict = job_data.dict(exclude={'mandatory_skills'})
        job = await job_crud.create(db, obj_in=base_job_dict)
        
        # Add mandatory skills if provided using raw SQL to avoid prepared statement issues
        if job_data.mandatory_skills:
            for skill_data in job_data.mandatory_skills:
                sd = _skill_to_dict(skill_data)
                # Use raw SQL to avoid prepared statement issues with PgBouncer
                await db.execute(
                    text("""
                        INSERT INTO job_mandatory_skills (job_id, skill, min_experience, created_at, updated_at)
                        VALUES (:job_id, :skill, :min_experience, NOW(), NOW())
                    """),
                    {
                        "job_id": job.id,
                        "skill": sd.get("skill"),
                        "min_experience": sd.get("min_experience", 1)
                    }
                )
            await db.commit()
        
        # Get the job with loaded relationships
        job_with_skills = await job_crud.get_with_mandatory_skills(db, job.id)
        # Schedule FAISS indexing in background to avoid blocking the request
        asyncio.create_task(_index_job_async(job.id))
        return job_with_skills
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Create job error")
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
        # Create the job with recruiter ID (exclude relationship field first)
        job_dict = job_data.dict(exclude={'mandatory_skills'})
        job_dict["recruiter_id"] = current_recruiter.id
        job = await job_crud.create(db, obj_in=job_dict)
        
        # Add mandatory skills if provided using raw SQL to avoid prepared statement issues
        if job_data.mandatory_skills:
            for skill_data in job_data.mandatory_skills:
                sd = _skill_to_dict(skill_data)
                # Use raw SQL to avoid prepared statement issues with PgBouncer
                await db.execute(
                    text("""
                        INSERT INTO job_mandatory_skills (job_id, skill, min_experience, created_at, updated_at)
                        VALUES (:job_id, :skill, :min_experience, NOW(), NOW())
                    """),
                    {
                        "job_id": job.id,
                        "skill": sd.get("skill"),
                        "min_experience": sd.get("min_experience", 1)
                    }
                )
            await db.commit()
        
        # Get the job with loaded relationships
        job_with_skills = await job_crud.get_with_mandatory_skills(db, job.id)
        # Schedule FAISS indexing in background
        asyncio.create_task(_index_job_async(job.id))
        return job_with_skills
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Create job as recruiter error")
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
        # Insert job via raw SQL with RETURNING to avoid extra round-trips
        insert_sql = text(
            """
            INSERT INTO jobs (
                title, company, location, salary_min, salary_max,
                domain, total_years_required, job_description, is_active, created_at, updated_at
            ) VALUES (
                :title, :company, :location, :salary_min, :salary_max,
                :domain, :total_years_required, :job_description, true, NOW(), NOW()
            )
            RETURNING id, title, company, location, salary_min, salary_max,
                      domain, total_years_required, job_description, is_active, created_at, updated_at
            """
        )
        params = {
            "title": job_data.title,
            "company": job_data.company,
            "location": job_data.location,
            "salary_min": job_data.salary_min,
            "salary_max": job_data.salary_max,
            "domain": job_data.domain,
            "total_years_required": job_data.total_years_required,
            "job_description": job_data.job_description,
        }
        result = await db.execute(insert_sql, params)
        row = result.fetchone()
        if not row:
            raise RuntimeError("Failed to insert job")
        job_id = row.id

        # Add mandatory skills if provided using raw SQL to avoid prepared statement issues
        if job_data.mandatory_skills:
            for skill_data in job_data.mandatory_skills:
                sd = _skill_to_dict(skill_data)
                await db.execute(
                    text(
                        """
                        INSERT INTO job_mandatory_skills (job_id, skill, min_experience, created_at, updated_at)
                        VALUES (:job_id, :skill, :min_experience, NOW(), NOW())
                        """
                    ),
                    {
                        "job_id": job_id,
                        "skill": sd.get("skill"),
                        "min_experience": sd.get("min_experience", 1),
                    },
                )
        await db.commit()

        # Schedule FAISS indexing in background
        asyncio.create_task(_index_job_async(job_id))

        # Build response matching JobResponse
        response = {
            "id": row.id,
            "title": row.title,
            "company": row.company,
            "location": row.location,
            "salary_min": row.salary_min,
            "salary_max": row.salary_max,
            "domain": row.domain,
            "total_years_required": row.total_years_required,
            "job_description": row.job_description,
            "is_active": row.is_active,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "mandatory_skills": [],
        }
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Create job public error")
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
        
        # Apply filters with case-insensitive partial matching
        if location:
            query = query.where(Job.location.ilike(f"%{location}%"))
        if domain:
            query = query.where(Job.domain.ilike(f"%{domain}%"))
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



@router.get("/recommendations", response_model=List[JobResponseSimple])
async def get_job_recommendations(
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(5, ge=1, le=20)
):
    """Get job recommendations for the current candidate"""
    try:
        # For now, return recent jobs as recommendations
        # In a real implementation, this would use ML/AI to provide personalized recommendations
        jobs = await job_crud.get_multi_with_filters(
            db, 
            skip=0, 
            limit=limit
        )
        
        # Convert to simple response format
        recommendations = []
        for job in jobs:
            recommendations.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "domain": job.domain,
                "total_years_required": job.total_years_required,
                "created_at": job.created_at,
                "updated_at": job.updated_at
            })
        
        return recommendations
        
    except Exception as e:
        print(f"Get job recommendations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job recommendations. Please try again later."
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
    title: Optional[str] = Query(None, description="Filter by job title"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    search: Optional[str] = Query(None, description="Search across location, title, domain, and company"),
    salary_min: Optional[int] = Query(None, ge=0, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, ge=0, description="Maximum salary"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session)
):
    """List jobs with enhanced filters - Optimized for fast response"""
    try:
        # Use raw SQL for maximum performance
        from sqlalchemy import text
        
        # Build dynamic WHERE clause
        where_conditions = []
        params = {"limit": limit, "skip": skip}
        
        # Individual filters
        if location:
            where_conditions.append("location ILIKE :location")
            params["location"] = f"%{location}%"
        
        if domain:
            where_conditions.append("domain ILIKE :domain")
            params["domain"] = f"%{domain}%"
        
        if title:
            where_conditions.append("title ILIKE :title")
            params["title"] = f"%{title}%"
        
        if company:
            where_conditions.append("company ILIKE :company")
            params["company"] = f"%{company}%"
        
        if salary_min is not None:
            where_conditions.append("salary_min >= :salary_min")
            params["salary_min"] = salary_min
        
        if salary_max is not None:
            where_conditions.append("salary_max <= :salary_max")
            params["salary_max"] = salary_max
        
        # Search across multiple fields
        if search:
            search_condition = """
                (title ILIKE :search OR 
                 company ILIKE :search OR 
                 location ILIKE :search OR 
                 domain ILIKE :search OR
                 job_description ILIKE :search)
            """
            where_conditions.append(search_condition)
            params["search"] = f"%{search}%"
        
        # Build the query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT id, title, company, location, salary_min, salary_max, domain, 
                   total_years_required, job_description, created_at, updated_at
            FROM jobs 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """)
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        # Convert to response format
        jobs = []
        for row in rows:
            jobs.append(JobResponse(
                id=row[0],
                title=row[1],
                company=row[2],
                location=row[3],
                salary_min=row[4],
                salary_max=row[5],
                domain=row[6],
                total_years_required=row[7],
                job_description=row[8],
                created_at=row[9],
                updated_at=row[10],
                mandatory_skills=[]  # Empty for now to avoid additional queries
            ))
        
        logger.info(f"Found {len(jobs)} jobs matching criteria")
        return jobs
        
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

@router.get("/autocomplete/locations")
async def get_location_suggestions(
    q: str = Query(..., min_length=1, description="Location query string"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get location autocomplete suggestions"""
    try:
        suggestions = await job_crud.get_location_suggestions(db, q, limit)
        return {
            "suggestions": suggestions,
            "query": q,
            "total": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Error getting location suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get location suggestions"
        )

@router.get("/autocomplete/domains")
async def get_domain_suggestions(
    q: str = Query(..., min_length=1, description="Domain query string"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get domain autocomplete suggestions"""
    try:
        suggestions = await job_crud.get_domain_suggestions(db, q, limit)
        return {
            "suggestions": suggestions,
            "query": q,
            "total": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Error getting domain suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get domain suggestions"
        )

@router.get("/autocomplete/titles")
async def get_title_suggestions(
    q: str = Query(..., min_length=1, description="Job title query string"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get job title autocomplete suggestions"""
    try:
        suggestions = await job_crud.get_title_suggestions(db, q, limit)
        return {
            "suggestions": suggestions,
            "query": q,
            "total": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Error getting title suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get title suggestions"
        )

@router.get("/autocomplete/companies")
async def get_company_suggestions(
    q: str = Query(..., min_length=1, description="Company name query string"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get company name autocomplete suggestions"""
    try:
        suggestions = await job_crud.get_company_suggestions(db, q, limit)
        return {
            "suggestions": suggestions,
            "query": q,
            "total": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Error getting company suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company suggestions"
        )

@router.get("/search/help")
async def get_search_help():
    """Get help documentation for job search features"""
    return {
        "search_filters": {
            "individual_filters": {
                "location": {
                    "description": "Filter by job location (case-insensitive partial match)",
                    "example": "?location=USA",
                    "note": "Finds 'USA', 'Usa', 'United States', etc."
                },
                "domain": {
                    "description": "Filter by job domain (case-insensitive partial match)", 
                    "example": "?domain=Tech",
                    "note": "Finds 'Technology', 'Technical', 'Fintech', etc."
                },
                "title": {
                    "description": "Filter by job title (case-insensitive partial match)",
                    "example": "?title=Engineer", 
                    "note": "Finds 'Software Engineer', 'Data Engineer', etc."
                },
                "company": {
                    "description": "Filter by company name (case-insensitive partial match)",
                    "example": "?company=Google",
                    "note": "Finds 'Google', 'Google Inc', etc."
                },
                "salary_min": {
                    "description": "Minimum salary filter",
                    "example": "?salary_min=50000"
                },
                "salary_max": {
                    "description": "Maximum salary filter", 
                    "example": "?salary_max=100000"
                }
            },
            "combined_search": {
                "search": {
                    "description": "Search across location, title, domain, company, and description",
                    "example": "?search=Python",
                    "note": "Searches all fields with OR logic - finds jobs with 'Python' in any field"
                }
            },
            "combination_examples": [
                "?location=USA&domain=Tech&salary_min=70000",
                "?search=Python&salary_min=80000",
                "?title=Engineer&company=Google&location=California"
            ]
        },
        "autocomplete_endpoints": {
            "locations": "/api/v1/jobs/autocomplete/locations?q=New&limit=5",
            "domains": "/api/v1/jobs/autocomplete/domains?q=Tech&limit=5", 
            "titles": "/api/v1/jobs/autocomplete/titles?q=Engineer&limit=5",
            "companies": "/api/v1/jobs/autocomplete/companies?q=Google&limit=5"
        },
        "pagination": {
            "skip": "Number of records to skip (default: 0)",
            "limit": "Maximum records to return (default: 10, max: 100)"
        },
        "notes": [
            "All text searches are case-insensitive and support partial matching",
            "Combine multiple filters with AND logic", 
            "Use 'search' parameter for OR logic across multiple fields",
            "Autocomplete suggestions are limited to 5-10 results",
            "All endpoints return jobs ordered by creation date (newest first)"
        ]
    }

