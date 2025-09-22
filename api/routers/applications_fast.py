from fastapi import APIRouter, HTTPException, status
from typing import Optional, List
import logging
import time

router = APIRouter(tags=["Applications Fast"])
logger = logging.getLogger(__name__)

# Mock data storage (in memory)
mock_applications_storage = [
    {
        "id": 1,
        "candidate_id": 1,
        "job_id": 1,
        "status": "APPLIED",
        "applied_at": "2024-01-15T10:30:00",
        "candidate_score": 85.5,
        "is_qualified": True,
        "candidate_name": "Alice Johnson",
        "candidate_email": "alice.johnson@email.com",
        "job_title": "Software Engineer",
        "company": "Tech Corp",
        "recruiter_id": 1,
        "recruiter_name": "John Smith"
    },
    {
        "id": 2,
        "candidate_id": 2,
        "job_id": 2,
        "status": "INTERVIEW_SCHEDULED",
        "applied_at": "2024-01-16T14:20:00",
        "candidate_score": 78.2,
        "is_qualified": True,
        "candidate_name": "Bob Smith",
        "candidate_email": "bob.smith@email.com",
        "job_title": "Data Scientist",
        "company": "Data Inc",
        "recruiter_id": 2,
        "recruiter_name": "Sarah Johnson"
    },
    {
        "id": 3,
        "candidate_id": 3,
        "job_id": 1,
        "status": "REJECTED",
        "applied_at": "2024-01-17T09:15:00",
        "candidate_score": 45.8,
        "is_qualified": False,
        "candidate_name": "Carol Davis",
        "candidate_email": "carol.davis@email.com",
        "job_title": "Software Engineer",
        "company": "Tech Corp",
        "recruiter_id": 1,
        "recruiter_name": "John Smith"
    }
]

@router.get("/public-fast")
async def get_applications_public_fast(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    qualification_filter: Optional[str] = None
):
    """Get applications list - Mock version that works instantly"""
    try:
        # Use storage data - works instantly
        mock_applications = mock_applications_storage.copy()
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            mock_applications = [
                a for a in mock_applications 
                if search_lower in a["candidate_name"].lower() or 
                   search_lower in a["candidate_email"].lower() or
                   search_lower in a["job_title"].lower() or
                   search_lower in a["company"].lower()
            ]
        
        # Apply status filter
        if status_filter:
            mock_applications = [a for a in mock_applications if a["status"] == status_filter]
        
        # Apply qualification filter
        if qualification_filter:
            if qualification_filter == "qualified":
                mock_applications = [a for a in mock_applications if a["is_qualified"] == True]
            elif qualification_filter == "rejected":
                mock_applications = [a for a in mock_applications if a["is_qualified"] == False]
        
        # Apply pagination
        result = mock_applications[skip:skip + limit]
        
        logger.info(f"Mock applications list successful: {len(result)} applications")
        return result
        
    except Exception as e:
        logger.error(f"Error in mock applications list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get applications"
        )

@router.post("/public-fast")
async def create_application_public_fast(request_data: dict):
    """Create a new application - Mock version that works instantly"""
    try:
        # Generate unique ID
        max_id = max([a.get('id', 0) for a in mock_applications_storage], default=0)
        new_id = max_id + 1
        
        # Mock candidate and job data
        candidates = [
            {"id": 1, "full_name": "Alice Johnson", "email": "alice.johnson@email.com"},
            {"id": 2, "full_name": "Bob Smith", "email": "bob.smith@email.com"},
            {"id": 3, "full_name": "Carol Davis", "email": "carol.davis@email.com"}
        ]
        
        jobs = [
            {"id": 1, "title": "Software Engineer", "company": "Tech Corp", "recruiter_id": 1},
            {"id": 2, "title": "Data Scientist", "company": "Data Inc", "recruiter_id": 2}
        ]
        
        recruiters = [
            {"id": 1, "full_name": "John Smith"},
            {"id": 2, "full_name": "Sarah Johnson"}
        ]
        
        # Find candidate and job info
        candidate = next((c for c in candidates if c['id'] == request_data.get('candidate_id')), None)
        job = next((j for j in jobs if j['id'] == request_data.get('job_id')), None)
        recruiter = next((r for r in recruiters if r['id'] == job['recruiter_id']), None) if job else None
        
        # Calculate mock score
        import random
        candidate_score = round(random.uniform(40, 95), 1)
        is_qualified = candidate_score >= 70
        
        # Create new application
        new_application = {
            "id": new_id,
            "candidate_id": request_data.get('candidate_id', 1),
            "job_id": request_data.get('job_id', 1),
            "status": "APPLIED",
            "applied_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "candidate_score": candidate_score,
            "is_qualified": is_qualified,
            "candidate_name": candidate['full_name'] if candidate else "Unknown Candidate",
            "candidate_email": candidate['email'] if candidate else "unknown@email.com",
            "job_title": job['title'] if job else "Unknown Job",
            "company": job['company'] if job else "Unknown Company",
            "recruiter_id": job['recruiter_id'] if job else None,
            "recruiter_name": recruiter['full_name'] if recruiter else "Unassigned"
        }
        
        # Add to storage
        mock_applications_storage.append(new_application)
        
        logger.info(f"Mock application creation successful: {new_application['candidate_name']} -> {new_application['job_title']} (ID: {new_id})")
        logger.info(f"Total applications in storage: {len(mock_applications_storage)}")
        
        return {
            "id": new_application["id"],
            "candidate_id": new_application["candidate_id"],
            "job_id": new_application["job_id"],
            "status": new_application["status"],
            "applied_at": new_application["applied_at"],
            "candidate_score": new_application["candidate_score"],
            "is_qualified": new_application["is_qualified"],
            "candidate_name": new_application["candidate_name"],
            "candidate_email": new_application["candidate_email"],
            "job_title": new_application["job_title"],
            "company": new_application["company"],
            "recruiter_id": new_application["recruiter_id"],
            "recruiter_name": new_application["recruiter_name"],
            "message": f"Application created successfully (mock) - ID: {new_id}"
        }
        
    except Exception as e:
        logger.error(f"Error in mock application creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application"
        )


