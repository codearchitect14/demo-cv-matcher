"""
Optimized applications endpoints for fast performance
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
import logging
import time

router = APIRouter(tags=["Applications Optimized"])
logger = logging.getLogger(__name__)

@router.get("/public-fast", response_model=List[dict])
async def get_applications_optimized(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by candidate name, email, job title"),
    recruiter_id: Optional[int] = Query(None, description="Filter by assigned recruiter ID"),
    qualification_filter: Optional[str] = Query(None, description="Filter by qualification")
):
    """Get applications with optimized performance using global connection pool"""
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
        
        # Build the final optimized query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
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
            LIMIT ${limit_param} OFFSET ${skip_param}
        """
        
        # Execute using global connection pool for maximum performance
        rows = await global_pool.fetch(query, *params)
        
        # Convert to response format efficiently
        applications = []
        for row in rows:
            # Build candidate object
            candidate = {
                "id": row['candidate_id'],
                "name": row['candidate_name'],
                "email": row['candidate_email'],
                "location": row['candidate_location'],
                "domain": row['candidate_domain'],
                "expected_salary_min": row['expected_salary_min'],
                "expected_salary_max": row['expected_salary_max']
            }
            
            # Build job object
            job = {
                "id": row['job_id'],
                "title": row['job_title'],
                "company": row['company'],
                "location": row['job_location'],
                "domain": row['job_domain'],
                "salary_min": row['salary_min'],
                "salary_max": row['salary_max'],
                "total_years_required": row['total_years_required'],
                "threshold_score": row['threshold_score'],
                "recruiter_id": row['recruiter_id']
            }
            
            # Build recruiter object
            recruiter = None
            if row['recruiter_name']:
                recruiter = {
                    "id": row['recruiter_id'],
                    "full_name": row['recruiter_name'],
                    "email": row['recruiter_email']
                }
            
            # Build application object
            app_data = {
                "id": row['id'],
                "job_id": row['job_id'],
                "candidate_id": row['candidate_id'],
                "status": row['status'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
                "candidate_score": row['candidate_score'],
                "is_qualified": row['is_qualified'],
                "candidate": candidate,
                "job": job,
                "recruiter": recruiter
            }
            
            applications.append(app_data)
        
        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(applications)} applications (took {elapsed:.3f}s)")
        return applications
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Error getting applications: {e} (took {elapsed:.3f}s)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get applications"
        )
