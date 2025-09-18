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
    """Create a new job - Mock version that works instantly"""
    try:
        # Mock response - works instantly
        current_time = time.time()
        
        # Generate unique ID based on current time and existing jobs
        max_id = max([job.get('id', 0) for job in mock_jobs_storage], default=0)
        new_id = max_id + 1
        
        # Create new job
        new_job = {
            "id": new_id,
            "title": request_data.get('title', 'New Job'),
            "company": request_data.get('company', 'Test Company'),
            "location": request_data.get('location', 'Remote'),
            "salary_min": request_data.get('salary_min', 50000),
            "salary_max": request_data.get('salary_max', 80000),
            "domain": request_data.get('domain', 'IT'),
            "total_years_required": request_data.get('total_years_required', 1),
            "job_description": request_data.get('job_description', 'Job description'),
            "threshold_score": request_data.get('threshold_score', 70),
            "recruiter_id": request_data.get('recruiter_id', 1),
            "company_id": 1,  # Always set company_id
            "is_active": True,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to storage
        mock_jobs_storage.append(new_job)
        
        logger.info(f"Mock job creation successful: {request_data.get('title', 'unknown')} (ID: {new_id})")
        logger.info(f"Total jobs in storage: {len(mock_jobs_storage)}")
        
        return {
            "id": new_job["id"],
            "title": new_job["title"],
            "company": new_job["company"],
            "location": new_job["location"],
            "salary_min": new_job["salary_min"],
            "salary_max": new_job["salary_max"],
            "domain": new_job["domain"],
            "total_years_required": new_job["total_years_required"],
            "job_description": new_job["job_description"],
            "threshold_score": new_job["threshold_score"],
            "recruiter_id": new_job["recruiter_id"],
            "company_id": new_job["company_id"],
            "is_active": new_job["is_active"],
            "created_at": new_job["created_at"],
            "message": f"Job created successfully (mock) - ID: {new_id}"
        }
        
    except Exception as e:
        logger.error(f"Error in mock job creation: {e}")
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
    """Get jobs list - Mock version that works instantly"""
    try:
        # Use storage data - works instantly
        mock_jobs = mock_jobs_storage.copy()
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            mock_jobs = [
                j for j in mock_jobs 
                if search_lower in j["title"].lower() or 
                   search_lower in j["company"].lower() or 
                   search_lower in j["location"].lower()
            ]
        
        # Apply pagination
        result = mock_jobs[skip:skip + limit]
        
        logger.info(f"Mock jobs list successful: {len(result)} jobs")
        return result
        
    except Exception as e:
        logger.error(f"Error in mock jobs list: {e}")
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
    """Get job assignments - which jobs are assigned to which recruiters"""
    try:
        # Get all jobs with their assigned recruiters
        assignments = []
        
        logger.info(f"Processing {len(mock_jobs_storage)} jobs for assignments")
        
        for job in mock_jobs_storage:
            # Find the assigned recruiter
            assigned_recruiter = None
            if job.get('recruiter_id'):
                # Mock recruiter data
                recruiters = [
                    {"id": 1, "full_name": "John Smith", "email": "john@company.com"},
                    {"id": 2, "full_name": "Sarah Johnson", "email": "sarah@company.com"},
                    {"id": 3, "full_name": "Mike Wilson", "email": "mike@company.com"}
                ]
                assigned_recruiter = next((r for r in recruiters if r['id'] == job['recruiter_id']), None)
                logger.info(f"Job {job['id']} ({job['title']}) assigned to recruiter {job['recruiter_id']}")
            else:
                logger.info(f"Job {job['id']} ({job['title']}) has no recruiter assigned")
            
            assignment = {
                "job_id": job['id'],
                "job_title": job['title'],
                "company": job['company'],
                "location": job['location'],
                "recruiter_id": job.get('recruiter_id'),
                "recruiter_name": assigned_recruiter['full_name'] if assigned_recruiter else "Unassigned",
                "recruiter_email": assigned_recruiter['email'] if assigned_recruiter else "N/A",
                "status": "Assigned" if assigned_recruiter else "Unassigned"
            }
            assignments.append(assignment)
        
        logger.info(f"Job assignments retrieved: {len(assignments)} assignments")
        return {
            "total_assignments": len(assignments),
            "assigned_jobs": len([a for a in assignments if a['status'] == 'Assigned']),
            "unassigned_jobs": len([a for a in assignments if a['status'] == 'Unassigned']),
            "assignments": assignments
        }
        
    except Exception as e:
        logger.error(f"Error getting job assignments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job assignments"
        )
