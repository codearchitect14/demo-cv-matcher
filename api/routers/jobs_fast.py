from fastapi import APIRouter, HTTPException, status
from typing import Optional, List
import logging
import time

router = APIRouter(tags=["Jobs Fast"])
logger = logging.getLogger(__name__)

# Mock data storage (in memory)
mock_jobs_storage = [
    {
        "id": 1,
        "title": "Software Engineer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "salary_min": 80000,
        "salary_max": 120000,
        "domain": "IT",
        "total_years_required": 3,
        "job_description": "Looking for a skilled software engineer",
        "threshold_score": 70,
        "recruiter_id": 1,
        "company_id": 1,
        "is_active": True,
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 2,
        "title": "Data Scientist",
        "company": "Data Inc",
        "location": "New York, NY",
        "salary_min": 90000,
        "salary_max": 130000,
        "domain": "IT",
        "total_years_required": 2,
        "job_description": "Seeking a data scientist with ML experience",
        "threshold_score": 75,
        "recruiter_id": 2,
        "company_id": 1,
        "is_active": True,
        "created_at": "2024-01-01T00:00:00"
    }
]

@router.post("/public-fast")
async def create_job_public_fast(request_data: dict):
    """Create a new job - Now saves to real database"""
    try:
        from config.connection_pool import global_pool
        import asyncio
        
        # Extract data from request
        title = request_data.get('title', 'New Job')
        company = request_data.get('company', 'Test Company')
        location = request_data.get('location', 'Remote')
        salary_min = request_data.get('salary_min', 50000)
        salary_max = request_data.get('salary_max', 80000)
        domain = request_data.get('domain', 'IT')
        total_years_required = request_data.get('total_years_required', 1)
        job_description = request_data.get('job_description', 'Job description')
        threshold_score = request_data.get('threshold_score', 70)
        recruiter_id = request_data.get('recruiter_id', 1)
        company_id = request_data.get('company_id', 1)
        
        # Insert into real database using asyncpg
        query = """
            INSERT INTO jobs (
                title, company, location, salary_min, salary_max, domain, 
                total_years_required, job_description, threshold_score, 
                recruiter_id, company_id, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
            RETURNING id, title, company, location, salary_min, salary_max, domain,
                     total_years_required, job_description, threshold_score,
                     recruiter_id, company_id, is_active, created_at
        """
        
        # Execute with timeout to prevent hanging
        row = await asyncio.wait_for(
            global_pool.fetchrow(
                query, title, company, location, salary_min, salary_max, domain,
                total_years_required, job_description, threshold_score,
                recruiter_id, company_id, True  # is_active = True
            ),
            timeout=8.0  # 8 second timeout
        )
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create job in database"
            )
        
        logger.info(f"Real job creation successful: {title} (ID: {row['id']})")
        
        return {
            "id": row['id'],
            "title": row['title'],
            "company": row['company'],
            "location": row['location'],
            "salary_min": row['salary_min'],
            "salary_max": row['salary_max'],
            "domain": row['domain'],
            "total_years_required": row['total_years_required'],
            "job_description": row['job_description'],
            "threshold_score": row['threshold_score'],
            "recruiter_id": row['recruiter_id'],
            "company_id": row['company_id'],
            "is_active": row['is_active'],
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "message": f"Job created successfully in database - ID: {row['id']}"
        }
        
    except asyncio.TimeoutError:
        logger.error(f"Job creation timeout for: {request_data.get('title', 'unknown')}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Job creation timed out. Please try again."
        )
    except Exception as e:
        logger.error(f"Error in real job creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )

@router.get("/public-fast")
async def list_jobs_public_fast(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """Get jobs list - Now uses real database"""
    try:
        from config.connection_pool import global_pool
        import asyncio
        
        # Build query with optional search filter
        where_clause = "WHERE is_active = true"
        params = []
        param_count = 0
        
        if search:
            param_count += 1
            where_clause += f" AND (LOWER(title) LIKE LOWER(${param_count}) OR LOWER(company) LIKE LOWER(${param_count}) OR LOWER(location) LIKE LOWER(${param_count}))"
            params.append(f"%{search}%")
        
        param_count += 1
        limit_param_idx = param_count
        param_count += 1
        skip_param_idx = param_count
        params.extend([limit, skip])
        
        query = f"""
            SELECT id, title, company, location, salary_min, salary_max, domain, 
                   total_years_required, job_description, threshold_score, 
                   recruiter_id, company_id, is_active, created_at, updated_at
            FROM jobs 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${limit_param_idx} OFFSET ${skip_param_idx}
        """
        
        # Execute with timeout to prevent hanging
        rows = await asyncio.wait_for(
            global_pool.fetch(query, *params),
            timeout=10.0  # 10 second timeout
        )
        
        # Convert to response format
        result = []
        for row in rows:
            job = {
                "id": row['id'],
                "title": row['title'],
                "company": row['company'],
                "location": row['location'],
                "salary_min": row['salary_min'],
                "salary_max": row['salary_max'],
                "domain": row['domain'],
                "total_years_required": row['total_years_required'],
                "job_description": row['job_description'],
                "threshold_score": row['threshold_score'],
                "recruiter_id": row['recruiter_id'],
                "company_id": row['company_id'],
                "is_active": row['is_active'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
            }
            result.append(job)
        
        logger.info(f"Real jobs list successful: {len(result)} jobs")
        return result
        
    except asyncio.TimeoutError:
        logger.error("Jobs list timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Jobs list timed out. Please try again."
        )
    except Exception as e:
        logger.error(f"Error in real jobs list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get jobs"
        )

@router.get("/recruiters-fast")
async def get_recruiters_for_jobs_fast():
    """Get recruiters for job assignment - Now shows real database records"""
    try:
        from config.database import SessionLocal
        from sqlalchemy import text
        
        # Use global connection pool to avoid prepared statement issues
        from config.connection_pool import global_pool
        
        # Get all active recruiters from database
        query = """
            SELECT id, full_name, email, company_name, role
            FROM recruiters 
            WHERE is_active = true
            ORDER BY full_name ASC
        """
        rows = await global_pool.fetch(query)
        
        recruiters = []
        for row in rows:
            recruiters.append({
                "id": row['id'],
                "full_name": row['full_name'],
                "email": row['email'],
                "company_name": row['company_name'],
                "role": row['role']
            })
        
        logger.info(f"Real recruiters list successful: {len(recruiters)} recruiters")
        return recruiters
        
    except Exception as e:
        logger.error(f"Error in mock recruiters list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recruiters"
        )

@router.get("/assignments-fast")
async def get_job_assignments_fast():
    """Get job assignments - which jobs are assigned to which recruiters - Now uses real database"""
    try:
        from config.connection_pool import global_pool
        import asyncio
        
        # Query real database for jobs with their assigned recruiters
        query = """
            SELECT 
                j.id as job_id,
                j.title as job_title,
                j.company,
                j.location,
                j.recruiter_id,
                r.full_name as recruiter_name,
                r.email as recruiter_email,
                CASE 
                    WHEN j.recruiter_id IS NOT NULL AND r.id IS NOT NULL THEN 'Assigned'
                    ELSE 'Unassigned'
                END as status
            FROM jobs j
            LEFT JOIN recruiters r ON j.recruiter_id = r.id
            WHERE j.is_active = true
            ORDER BY j.created_at DESC
        """
        
        # Execute with timeout to prevent hanging
        rows = await asyncio.wait_for(
            global_pool.fetch(query),
            timeout=10.0  # 10 second timeout
        )
        
        assignments = []
        for row in rows:
            assignment = {
                "job_id": row['job_id'],
                "job_title": row['job_title'],
                "company": row['company'],
                "location": row['location'],
                "recruiter_id": row['recruiter_id'],
                "recruiter_name": row['recruiter_name'] if row['recruiter_name'] else "Unassigned",
                "recruiter_email": row['recruiter_email'] if row['recruiter_email'] else "N/A",
                "status": row['status']
            }
            assignments.append(assignment)
        
        assigned_count = len([a for a in assignments if a['status'] == 'Assigned'])
        unassigned_count = len([a for a in assignments if a['status'] == 'Unassigned'])
        
        logger.info(f"Real job assignments retrieved: {len(assignments)} assignments ({assigned_count} assigned, {unassigned_count} unassigned)")
        
        return {
            "total_assignments": len(assignments),
            "assigned_jobs": assigned_count,
            "unassigned_jobs": unassigned_count,
            "assignments": assignments
        }
        
    except asyncio.TimeoutError:
        logger.error("Job assignments timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Job assignments timed out. Please try again."
        )
    except Exception as e:
        logger.error(f"Error getting job assignments from database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job assignments"
        )
