#Today's date: 25/07/2025

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
from models.candidate import Candidate
from models.recruiter import Recruiter
from config.database import get_db_session
from models.job import Job, JobMandatorySkill
from db.crud.job import job as job_crud
from db.crud.application import application as application_crud
from api.routers.auth import get_current_user, get_current_recruiter
from schemas.job import JobCreate, JobUpdate, JobResponse, JobResponseSimple, JobMandatorySkillCreate, JobSearchFilter
from middleware.recruiter_auth import get_current_recruiter as get_recruiter_context, RecruiterContext
from sqlalchemy import select, text
import logging
import asyncio
from services.email_service import email_service
from services.notification_service import notification_service

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
        # Create the job with recruiter ID and company ID (exclude relationship field first)
        job_dict = job_data.dict(exclude={'mandatory_skills'})
        job_dict["recruiter_id"] = current_recruiter.id
        job_dict["company_id"] = getattr(current_recruiter, 'company_id', 1)  # Default to company 1
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
        
        # Send job posting confirmation email to Company Admin
        try:
            # Get company name
            company_name = "Your Company"  # Default fallback
            company_query = await db.execute(text("SELECT name FROM companies WHERE id = :company_id"), 
                                           {"company_id": job.company_id})
            company_result = company_query.fetchone()
            if company_result:
                company_name = company_result[0]
            
            await email_service.send_job_posting_confirmation_email(
                admin_email=current_recruiter.email,
                admin_name=current_recruiter.full_name,
                job_title=job.title,
                company_name=company_name
            )
            logger.info(f"Job posting confirmation email sent to admin: {current_recruiter.email}")
        except Exception as email_error:
            logger.error(f"Failed to send job posting confirmation email: {email_error}")
        
        # Create notification for job posting confirmation
        try:
            await notification_service.create_notification(
                user_id=current_recruiter.id,
                user_type="recruiter",
                title="Job Posted Successfully",
                message=f"Your job posting '{job.title}' has been published and is now live.",
                notification_type="success",
                related_entity_type="job",
                related_entity_id=job.id
            )
            logger.info(f"Job posting notification created for recruiter: {current_recruiter.id}")
        except Exception as notification_error:
            logger.error(f"Failed to create job posting notification: {notification_error}")
        
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
    job_data: JobCreate
):
    """Create a new job posting (public endpoint for testing) with direct connection"""
    try:
        import asyncpg
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Validate recruiter_id if provided using direct connection
        if hasattr(job_data, 'recruiter_id') and job_data.recruiter_id is not None:
            conn = None
            try:
                conn = await asyncpg.connect(
                    os.getenv('DATABASE_URL'), 
                    statement_cache_size=0,
                    command_timeout=8
                )
                recruiter_check = await conn.fetchrow(
                    "SELECT id FROM recruiters WHERE id = $1 AND is_active = true",
                    job_data.recruiter_id
                )
                if not recruiter_check:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Recruiter with ID {job_data.recruiter_id} not found or inactive"
                    )
            finally:
                if conn:
                    try:
                        await conn.close()
                    except Exception as e:
                        logger.warning(f"Error closing recruiter validation connection: {e}")
        
        # Insert job using direct connection with timeout handling
        conn = None
        try:
            conn = await asyncpg.connect(
                os.getenv('DATABASE_URL'), 
                statement_cache_size=0,
                command_timeout=8
            )
            
            insert_sql = """
                INSERT INTO jobs (
                    title, company, location, salary_min, salary_max,
                    domain, total_years_required, job_description, is_active, threshold_score, recruiter_id, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, true, $9, $10, NOW(), NOW()
                )
                RETURNING id, title, company, location, salary_min, salary_max,
                          domain, total_years_required, job_description, is_active, threshold_score, recruiter_id, created_at, updated_at
            """
            
            params = [
                job_data.title,
                job_data.company,
                job_data.location,
                job_data.salary_min,
                job_data.salary_max,
                job_data.domain,
                job_data.total_years_required,
                job_data.job_description,
                getattr(job_data, 'threshold_score', 70),  # Default to 70 if not provided
                getattr(job_data, 'recruiter_id', None)  # Default to None if not provided
            ]
            
            row = await conn.fetchrow(insert_sql, *params)
        finally:
            if conn:
                try:
                    await conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
        if not row:
            raise RuntimeError("Failed to insert job")
        job_id = row['id']

        # Add mandatory skills if provided using direct connection
        if hasattr(job_data, 'mandatory_skills') and job_data.mandatory_skills:
            conn2 = None
            try:
                conn2 = await asyncpg.connect(
                    os.getenv('DATABASE_URL'), 
                    statement_cache_size=0,
                    command_timeout=8
                )
                for skill_data in job_data.mandatory_skills:
                    sd = _skill_to_dict(skill_data)
                    await conn2.execute(
                        """
                        INSERT INTO job_mandatory_skills (job_id, skill, min_experience, created_at, updated_at)
                        VALUES ($1, $2, $3, NOW(), NOW())
                        """,
                        job_id,
                        sd.get("skill"),
                        sd.get("min_experience", 1)
                    )
            finally:
                if conn2:
                    try:
                        await conn2.close()
                    except Exception as e:
                        logger.warning(f"Error closing mandatory skills connection: {e}")

        # Schedule FAISS indexing in background
        asyncio.create_task(_index_job_async(job_id))

        # Build response matching JobResponse
        response = {
            "id": row['id'],
            "title": row['title'],
            "company": row['company'],
            "location": row['location'],
            "salary_min": row['salary_min'],
            "salary_max": row['salary_max'],
            "domain": row['domain'],
            "total_years_required": row['total_years_required'],
            "job_description": row['job_description'],
            "is_active": row['is_active'],
            "threshold_score": row['threshold_score'],
            "recruiter_id": row['recruiter_id'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at'],
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
    limit: int = Query(5, ge=1, le=20),
    debug: bool = Query(False)
):
    """Get job recommendations for the current candidate using unified scoring"""
    from config.connection_pool import global_pool
    import asyncio
    
    try:
        # Get candidate data with skills
        candidate_query = """
            SELECT c.id, c.name, c.domain, c.location, c.expected_salary_min, c.expected_salary_max,
                   COALESCE(ARRAY_AGG(ce.skill), ARRAY[]::text[]) as skills,
                   COALESCE(ARRAY_AGG(ce.years), ARRAY[]::int[]) as skill_years,
                   COALESCE(SUM(ce.years), 0) as total_experience
            FROM candidates c
            LEFT JOIN candidate_experience ce ON ce.candidate_id = c.id
            WHERE c.id = $1
            GROUP BY c.id, c.name, c.domain, c.location, c.expected_salary_min, c.expected_salary_max
        """
        
        candidate_rows = await global_pool.fetch(candidate_query, current_user.id)
        if not candidate_rows:
            return []
        
        candidate_row = candidate_rows[0]
        
        # Prepare candidate data for unified scoring
        candidate_skills = []
        if candidate_row["skills"] and candidate_row["skill_years"]:
            candidate_skills = [
                {"skill": skill, "years": years} 
                for skill, years in zip(candidate_row["skills"], candidate_row["skill_years"])
            ]
        
        candidate_data = {
            "id": candidate_row["id"],
            "name": candidate_row["name"],
            "domain": candidate_row["domain"],
            "location": candidate_row["location"],
            "total_experience": candidate_row["total_experience"],
            "expected_salary_min": candidate_row["expected_salary_min"],
            "expected_salary_max": candidate_row["expected_salary_max"],
            "skills": candidate_skills,
            "education": candidate_row.get("education")  # Add education if available
        }
        
        # Get jobs with their skills
        jobs_query = """
            SELECT j.id, j.title, j.company, j.location, j.salary_min, j.salary_max, 
                   j.domain, j.total_years_required, j.job_description, j.created_at, j.updated_at
            FROM jobs j
            WHERE j.is_active = TRUE
            ORDER BY j.created_at DESC 
            LIMIT $1
        """
        
        job_rows = await asyncio.wait_for(
            global_pool.fetch(jobs_query, min(limit * 2, 20)),  # Max 20 jobs to prevent timeout
            timeout=8.0
        )
        
        # Import matching service
        from services.matching_service import matching_service
        
        # Get all job skills in one query for efficiency
        job_ids = [row["id"] for row in job_rows]
        all_job_skills_query = """
            SELECT job_id, skill, min_years_experience
            FROM job_skills
            WHERE job_id = ANY($1::int[])
        """
        try:
            all_job_skills_rows = await global_pool.fetch(all_job_skills_query, job_ids)
        except:
            # Try alternative table
            try:
                alt_all_skills_query = """
                    SELECT job_id, skill, min_experience as min_years_experience
                    FROM job_mandatory_skills
                    WHERE job_id = ANY($1::int[])
                """
                all_job_skills_rows = await global_pool.fetch(alt_all_skills_query, job_ids)
            except:
                all_job_skills_rows = []
        
        # Group skills by job_id
        job_skills_map = {}
        for skill_row in all_job_skills_rows:
            job_id = skill_row["job_id"]
            if job_id not in job_skills_map:
                job_skills_map[job_id] = []
            job_skills_map[job_id].append({
                "skill": skill_row["skill"],
                "min_experience": skill_row["min_years_experience"]
            })
        
        # Calculate scores for each job
        scored_jobs = []
        for job_row in job_rows:
            jd = dict(job_row)  # Convert asyncpg Record to dict
            
            # Get job skills from map
            job_skills = job_skills_map.get(jd["id"], [])
            
            # Prepare job data for unified scoring
            job_data = {
                "id": jd.get("id"),
                "title": jd.get("title", ""),
                "domain": jd.get("domain"),
                "location": jd.get("location"),
                "total_years_required": jd.get("total_years_required", 0),
                "salary_min": jd.get("salary_min"),
                "salary_max": jd.get("salary_max"),
                "skills": job_skills,  # Already formatted correctly
                "education_required": jd.get("education_required")  # Add if available
            }
            # Calculate unified match score via shared scorer
            from services.scoring import calculate_match_score
            match_score, breakdown = calculate_match_score(candidate_data, job_data)
            logger.info(f"[Score] candidate_id={candidate_data.get('id')} job_id={job_data.get('id')} match_score={match_score}")

            scored_jobs.append({
                "job_data": jd,
                "match_score": match_score,
                **({"breakdown": breakdown} if debug and breakdown is not None else {})
            })
        
        # Sort by match score descending and take top results
        scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        top_jobs = scored_jobs[:limit]
        
        # Format response
        recommendations = []
        for item in top_jobs:
            job = item["job_data"]
            rec = {
                "id": job['id'],
                "title": job['title'],
                "company": job['company'],
                "location": job['location'],
                "salary_min": job['salary_min'],
                "salary_max": job['salary_max'],
                "domain": job['domain'],
                "total_years_required": job['total_years_required'],
                "job_description": job['job_description'] or "",
                "created_at": job['created_at'].isoformat() if job['created_at'] else None,
                "updated_at": job['updated_at'].isoformat() if job['updated_at'] else None,
                "match_score": item["match_score"]  # Include match score in response
            }
            if debug and 'breakdown' in item:
                rec['debug_breakdown'] = item['breakdown']
            recommendations.append(rec)
        
        return recommendations
        
    except asyncio.TimeoutError:
        logger.warning("Job recommendations query timed out")
        return []
        
    except Exception as e:
        logger.error(f"Get job recommendations error: {e}")
        return []

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    candidate_id: Optional[int] = Query(None, description="Candidate ID to log view interaction"),
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
        
        # Log the view interaction if candidate_id is provided
        if candidate_id:
            try:
                from config.connection_pool import global_pool
                await global_pool.execute(
                    """
                    INSERT INTO interaction_log (user_id, user_type, job_id, interaction_type, timestamp)
                    VALUES ($1, 'candidate', $2, 'VIEWED', NOW())
                    """,
                    candidate_id, job_id
                )
                print(f"✅ Logged VIEWED interaction for candidate {candidate_id} viewing job {job_id}")
            except Exception as log_error:
                print(f"⚠️ Failed to log view interaction: {log_error}")
        
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
    limit: int = Query(10, ge=1, le=100)
):
    """List jobs with enhanced filters - Ultra-fast response using global connection pool"""
    import time
    start_time = time.time()
    
    try:
        from config.connection_pool import global_pool
        
        # Build optimized WHERE clause with indexed columns first
        where_conditions = []
        params = []
        param_count = 0
        
        # Use indexed columns for better performance
        if domain:
            param_count += 1
            where_conditions.append(f"domain = ${param_count}")
            params.append(domain)
        
        if location:
            param_count += 1
            where_conditions.append(f"location ILIKE ${param_count}")
            params.append(f"%{location}%")
        
        if title:
            param_count += 1
            where_conditions.append(f"title ILIKE ${param_count}")
            params.append(f"%{title}%")
        
        if company:
            param_count += 1
            where_conditions.append(f"company ILIKE ${param_count}")
            params.append(f"%{company}%")
        
        if salary_min is not None:
            param_count += 1
            where_conditions.append(f"salary_min >= ${param_count}")
            params.append(salary_min)
        
        if salary_max is not None:
            param_count += 1
            where_conditions.append(f"salary_max <= ${param_count}")
            params.append(salary_max)
        
        # Search across multiple fields (optimized for indexed columns)
        if search:
            param_count += 1
            search_condition = f"""
                (title ILIKE ${param_count} OR 
                 company ILIKE ${param_count} OR 
                 location ILIKE ${param_count} OR 
                 domain ILIKE ${param_count})
            """
            where_conditions.append(search_condition)
            params.append(f"%{search}%")
        
        # Build optimized query with proper indexing
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Add limit and offset parameters
        param_count += 1
        limit_param = f"${param_count}"
        param_count += 1
        offset_param = f"${param_count}"
        params.extend([limit, skip])
        
        # Optimized query - only select needed columns, use indexed ORDER BY
        query = f"""
            SELECT id, title, company, location, salary_min, salary_max, domain, 
                   total_years_required, job_description, created_at, updated_at
            FROM jobs 
            WHERE {where_clause} AND is_active = true
            ORDER BY created_at DESC
            LIMIT {limit_param} OFFSET {offset_param}
        """
        
        # Execute using global connection pool for better performance
        rows = await global_pool.fetch(query, *params)
        
        # Convert to response format efficiently
        jobs = []
        for row in rows:
            jobs.append(JobResponse(
                id=row['id'],
                title=row['title'],
                company=row['company'],
                location=row['location'],
                salary_min=row['salary_min'],
                salary_max=row['salary_max'],
                domain=row['domain'],
                total_years_required=row['total_years_required'],
                job_description=row['job_description'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                mandatory_skills=[]  # Skip skills to avoid N+1 queries
            ))
        
        elapsed = time.time() - start_time
        logger.info(f"Found {len(jobs)} jobs matching criteria (took {elapsed:.3f}s)")
        return jobs
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
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
    limit: int = Query(5, ge=1, le=10, description="Maximum number of suggestions")
):
    """Get job title autocomplete suggestions - asyncpg to avoid PgBouncer timeouts"""
    try:
        from config.connection_pool import global_pool
        import asyncio

        rows = await asyncio.wait_for(
            global_pool.fetch(
                """
                SELECT DISTINCT title
                FROM jobs
                WHERE LOWER(title) LIKE LOWER($1)
                ORDER BY title ASC
                LIMIT $2
                """,
                f"%{q}%", limit
            ),
            timeout=5.0
        )

        suggestions = [r["title"] for r in rows]
        return {"suggestions": suggestions, "query": q, "total": len(suggestions)}
    except asyncio.TimeoutError:
        return {"suggestions": [], "query": q, "total": 0}
    except Exception as e:
        logger.error(f"Error getting title suggestions: {e}")
        return {"suggestions": [], "query": q, "total": 0}

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

@router.get("/recruiter/assigned", response_model=List[JobResponse])
async def get_recruiter_assigned_jobs(
    db: AsyncSession = Depends(get_db_session),
    recruiter_context: RecruiterContext = Depends(get_recruiter_context),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, description="Filter by job status (active/inactive)"),
    search: Optional[str] = Query(None, description="Search by job title, company, or location")
):
    """Get jobs assigned to the authenticated recruiter with optimized performance"""
    import time
    start_time = time.time()
    
    try:
        from config.connection_pool import global_pool
        
        # Build dynamic WHERE clause for filtering
        where_conditions = []
        params = {"limit": limit, "skip": skip}
        
        # Add recruiter filter - non-admin recruiters can only see their assigned jobs
        if not recruiter_context.is_admin:
            where_conditions.append("recruiter_id = :recruiter_id")
            params["recruiter_id"] = recruiter_context.recruiter_id
        else:
            # Admins see all jobs, but can optionally filter by recruiter
            if hasattr(recruiter_context, 'filter_recruiter_id') and recruiter_context.filter_recruiter_id:
                where_conditions.append("recruiter_id = :recruiter_id")
                params["recruiter_id"] = recruiter_context.filter_recruiter_id
        
        # Add status filter
        if status_filter:
            if status_filter.lower() == "active":
                where_conditions.append("is_active = true")
            elif status_filter.lower() == "inactive":
                where_conditions.append("is_active = false")
        
        # Add search filter
        if search:
            where_conditions.append("""
                (LOWER(title) LIKE LOWER(:search) OR 
                 LOWER(company) LIKE LOWER(:search) OR 
                 LOWER(location) LIKE LOWER(:search))
            """)
            params["search"] = f"%{search}%"
        
        # Build the final query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                j.id, j.title, j.company, j.location, j.salary_min, j.salary_max,
                j.domain, j.total_years_required, j.job_description, j.is_active, 
                j.threshold_score, j.recruiter_id, j.created_at, j.updated_at,
                r.full_name as recruiter_name, r.email as recruiter_email
            FROM jobs j
            LEFT JOIN recruiters r ON j.recruiter_id = r.id
            WHERE {where_clause}
            ORDER BY j.created_at DESC
            LIMIT :limit OFFSET :skip
        """)
        
        # Execute using global connection pool for better performance
        rows = await global_pool.fetch(query.text, **params)
        
        # Convert to JobResponse format efficiently
        jobs = []
        for row in rows:
            jobs.append(JobResponse(
                id=row['id'],
                title=row['title'],
                company=row['company'],
                location=row['location'],
                salary_min=row['salary_min'],
                salary_max=row['salary_max'],
                domain=row['domain'],
                total_years_required=row['total_years_required'],
                job_description=row['job_description'],
                is_active=row['is_active'],
                threshold_score=row.get('threshold_score', 70),
                recruiter_id=row['recruiter_id'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                mandatory_skills=[]  # Skip skills to avoid N+1 queries
            ))
        
        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(jobs)} assigned jobs for recruiter {recruiter_context.recruiter_id} (took {elapsed:.3f}s)")
        return jobs
        
    except Exception as e:
        print(f"Get recruiter jobs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs. Please try again later."
        )

