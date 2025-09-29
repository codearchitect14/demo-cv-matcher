from fastapi import APIRouter, HTTPException
from config.connection_pool import global_pool
import logging
import asyncpg

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/debug-recruiters")
async def debug_recruiters():
    """Debug endpoint to check recruiters and job assignments"""
    try:
        async with global_pool.acquire() as conn:
            # Get all recruiters
            recruiters_query = "SELECT id, email, full_name FROM recruiters"
            recruiters = await conn.fetch(recruiters_query)
            
            # Get all jobs with their recruiter assignments
            jobs_query = """
                SELECT j.id, j.title, j.recruiter_id, r.email as recruiter_email 
                FROM jobs j 
                LEFT JOIN recruiters r ON j.recruiter_id = r.id
                ORDER BY j.id
            """
            jobs = await conn.fetch(jobs_query)
            
            return {
                "recruiters": [dict(r) for r in recruiters],
                "jobs": [dict(j) for j in jobs]
            }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Debug failed")

@router.get("/assigned-jobs")
async def get_assigned_jobs():
    """Get all jobs assigned to the sub-recruiter (public endpoint)"""
    try:
        # Use direct asyncpg connection to avoid PgBouncer issues
        async with global_pool.acquire() as conn:
            # First, find the recruiter ID for tayyab10@boolmind.com
            recruiter_query = "SELECT id FROM recruiters WHERE email = 'tayyab10@boolmind.com'"
            recruiter_result = await conn.fetchrow(recruiter_query)
            
            if not recruiter_result:
                logger.warning("Recruiter tayyab10@boolmind.com not found, using default ID 1")
                recruiter_id = 1
            else:
                recruiter_id = recruiter_result['id']
                logger.info(f"Found recruiter ID {recruiter_id} for tayyab10@boolmind.com")
            # Query to get assigned jobs with application counts
            query = """
                SELECT 
                    j.id,
                    j.title,
                    j.location,
                    j.company,
                    j.created_at,
                    j.is_active,
                    COUNT(a.id) as total_applications,
                    COUNT(CASE WHEN a.status = 'APPLIED' THEN 1 END) as applied_count,
                    COUNT(CASE WHEN a.status = 'INTERVIEW_SCHEDULED' THEN 1 END) as interview_count,
                    COUNT(CASE WHEN a.status = 'REJECTED' THEN 1 END) as rejected_count,
                    COUNT(CASE WHEN a.status = 'HIRED' THEN 1 END) as hired_count
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id
                WHERE j.recruiter_id = $1
                GROUP BY j.id, j.title, j.location, j.company, j.created_at, j.is_active
                ORDER BY j.created_at DESC
            """
            
            rows = await conn.fetch(query, recruiter_id)
            jobs = []
            
            for row in rows:
                job = {
                    "id": row['id'],
                    "title": row['title'],
                    "location": row['location'],
                    "company": row['company'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "status": "ACTIVE" if row['is_active'] else "INACTIVE",
                    "applications": {
                        "total": row['total_applications'] or 0,
                        "APPLIED": row['applied_count'] or 0,
                        "INTERVIEW_SCHEDULED": row['interview_count'] or 0,
                        "REJECTED": row['rejected_count'] or 0,
                        "HIRED": row['hired_count'] or 0
                    }
                }
                jobs.append(job)
            
            return {"jobs": jobs}
        
    except Exception as e:
        logger.error(f"Error fetching assigned jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch assigned jobs")

@router.get("/job-candidates/{job_id}")
async def get_job_candidates(job_id: int):
    """Get all candidates for a specific job assigned to the sub-recruiter (public endpoint)"""
    try:
        # Use direct asyncpg connection to avoid PgBouncer issues
        async with global_pool.acquire() as conn:
            # First, find the recruiter ID for tayyab10@boolmind.com
            recruiter_query = "SELECT id FROM recruiters WHERE email = 'tayyab10@boolmind.com'"
            recruiter_result = await conn.fetchrow(recruiter_query)
            
            if not recruiter_result:
                logger.warning("Recruiter tayyab10@boolmind.com not found, using default ID 1")
                recruiter_id = 1
            else:
                recruiter_id = recruiter_result['id']
                logger.info(f"Found recruiter ID {recruiter_id} for tayyab10@boolmind.com")
            # First verify the job is assigned to this recruiter
            verify_query = """
                SELECT id FROM jobs 
                WHERE id = $1 AND recruiter_id = $2
            """
            
            verify_result = await conn.fetchrow(verify_query, job_id, recruiter_id)
            
            if not verify_result:
                raise HTTPException(status_code=403, detail="Job not assigned to you")
            
            # Get candidates with their application details
            query = """
                SELECT 
                    c.id,
                    c.name,
                    c.email,
                    c.location,
                    c.total_experience_years,
                    a.status,
                    a.created_at as applied_at
                FROM applications a
                JOIN candidates c ON a.candidate_id = c.id
                WHERE a.job_id = $1
                ORDER BY a.created_at DESC
            """
            
            rows = await conn.fetch(query, job_id)
            candidates = []
            
            for row in rows:
                candidate = {
                    "id": row['id'],
                    "name": row['name'],
                    "email": row['email'],
                    "location": row['location'],
                    "total_experience_years": row['total_experience_years'],
                    "status": row['status'],
                    "applied_at": row['applied_at'].isoformat() if row['applied_at'] else None,
                    "assessment_score": None,
                    "assessment_status": None
                }
                candidates.append(candidate)
            
            return {"candidates": candidates}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job candidates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch candidates")

@router.put("/update-candidate-status")
async def update_candidate_status(
    candidate_id: int,
    job_id: int,
    status: str
):
    """Update candidate application status (public endpoint)"""
    try:
        # Use direct asyncpg connection to avoid PgBouncer issues
        async with global_pool.acquire() as conn:
            # First, find the recruiter ID for tayyab10@boolmind.com
            recruiter_query = "SELECT id FROM recruiters WHERE email = 'tayyab10@boolmind.com'"
            recruiter_result = await conn.fetchrow(recruiter_query)
            
            if not recruiter_result:
                logger.warning("Recruiter tayyab10@boolmind.com not found, using default ID 1")
                recruiter_id = 1
            else:
                recruiter_id = recruiter_result['id']
                logger.info(f"Found recruiter ID {recruiter_id} for tayyab10@boolmind.com")
            # Verify the job is assigned to this recruiter
            verify_query = """
                SELECT id FROM jobs 
                WHERE id = $1 AND recruiter_id = $2
            """
            
            verify_result = await conn.fetchrow(verify_query, job_id, recruiter_id)
            
            if not verify_result:
                raise HTTPException(status_code=403, detail="Job not assigned to you")
            
            # Update the application status
            update_query = """
                UPDATE applications 
                SET status = $1, updated_at = NOW()
                WHERE candidate_id = $2 AND job_id = $3
            """
            
            result = await conn.execute(update_query, status, candidate_id, job_id)
            
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Application not found")
            
            # Log the interaction
            log_query = """
                INSERT INTO interaction_log (candidate_id, job_id, interaction_type, user_id, user_type, created_at)
                VALUES ($1, $2, $3, $4, 'recruiter', NOW())
            """
            
            await conn.execute(log_query, candidate_id, job_id, status, recruiter_id)
            
            return {"message": "Status updated successfully", "status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update status")

@router.get("/candidate-details/{candidate_id}")
async def get_candidate_details(candidate_id: int):
    """Get detailed candidate information (public endpoint)"""
    try:
        # Use direct asyncpg connection to avoid PgBouncer issues
        async with global_pool.acquire() as conn:
            # Get candidate details
            query = """
                SELECT 
                    c.id,
                    c.name,
                    c.email,
                    c.location,
                    c.total_experience_years,
                    c.professional_summary,
                    c.domain,
                    c.min_salary,
                    c.max_salary,
                    c.resume_url,
                    c.created_at
                FROM candidates c
                WHERE c.id = $1
            """
            
            candidate = await conn.fetchrow(query, candidate_id)
            
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
            
            # Get candidate's skills
            skills_query = """
                SELECT skill_name, years_of_experience
                FROM candidate_skills
                WHERE candidate_id = $1
            """
            
            skills_rows = await conn.fetch(skills_query, candidate_id)
            skills = [{"name": row['skill_name'], "years": row['years_of_experience']} for row in skills_rows]
            
            candidate_data = {
                "id": candidate['id'],
                "name": candidate['name'],
                "email": candidate['email'],
                "location": candidate['location'],
                "total_experience_years": candidate['total_experience_years'],
                "professional_summary": candidate['professional_summary'],
                "domain": candidate['domain'],
                "min_salary": candidate['min_salary'],
                "max_salary": candidate['max_salary'],
                "resume_url": candidate['resume_url'],
                "created_at": candidate['created_at'].isoformat() if candidate['created_at'] else None,
                "skills": skills
            }
            
            return {"candidate": candidate_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candidate details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch candidate details")
