from fastapi import APIRouter, HTTPException, status
from typing import Optional, List
import logging
import time

router = APIRouter(tags=["Candidates Fast"])
logger = logging.getLogger(__name__)

# Mock data storage (in memory)
mock_candidates_storage = [
    {
        "id": 1,
        "full_name": "Alice Johnson",
        "email": "alice.johnson@email.com",
        "phone": "+1-555-0101",
        "location": "San Francisco, CA",
        "experience_years": 5,
        "skills": ["Python", "JavaScript", "React", "Node.js"],
        "education": "Bachelor's in Computer Science",
        "resume_url": "https://example.com/resumes/alice_johnson.pdf",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 2,
        "full_name": "Bob Smith",
        "email": "bob.smith@email.com",
        "phone": "+1-555-0102",
        "location": "New York, NY",
        "experience_years": 3,
        "skills": ["Java", "Spring Boot", "MySQL", "Docker"],
        "education": "Master's in Software Engineering",
        "resume_url": "https://example.com/resumes/bob_smith.pdf",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 3,
        "full_name": "Carol Davis",
        "email": "carol.davis@email.com",
        "phone": "+1-555-0103",
        "location": "Austin, TX",
        "experience_years": 7,
        "skills": ["Python", "Machine Learning", "TensorFlow", "AWS"],
        "education": "PhD in Data Science",
        "resume_url": "https://example.com/resumes/carol_davis.pdf",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00"
    }
]

@router.get("/public-fast")
async def get_candidates_public_fast(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """Get candidates list - Mock version that works instantly"""
    try:
        # Use storage data - works instantly
        mock_candidates = mock_candidates_storage.copy()
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            mock_candidates = [
                c for c in mock_candidates 
                if search_lower in c["full_name"].lower() or 
                   search_lower in c["email"].lower() or
                   search_lower in c["location"].lower() or
                   any(search_lower in skill.lower() for skill in c["skills"])
            ]
        
        # Apply pagination
        result = mock_candidates[skip:skip + limit]
        
        logger.info(f"Mock candidates list successful: {len(result)} candidates")
        return result
        
    except Exception as e:
        logger.error(f"Error in mock candidates list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get candidates"
        )

@router.post("/public-fast")
async def create_candidate_public_fast(request_data: dict):
    """Create a new candidate - Mock version that works instantly"""
    try:
        # Generate unique ID
        max_id = max([c.get('id', 0) for c in mock_candidates_storage], default=0)
        new_id = max_id + 1
        
        # Create new candidate
        new_candidate = {
            "id": new_id,
            "full_name": request_data.get('full_name', 'New Candidate'),
            "email": request_data.get('email', 'candidate@email.com'),
            "phone": request_data.get('phone', '+1-555-0000'),
            "location": request_data.get('location', 'Remote'),
            "experience_years": request_data.get('experience_years', 1),
            "skills": request_data.get('skills', []),
            "education": request_data.get('education', 'Not specified'),
            "resume_url": request_data.get('resume_url', ''),
            "is_active": True,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to storage
        mock_candidates_storage.append(new_candidate)
        
        logger.info(f"Mock candidate creation successful: {request_data.get('full_name', 'unknown')} (ID: {new_id})")
        logger.info(f"Total candidates in storage: {len(mock_candidates_storage)}")
        
        return {
            "id": new_candidate["id"],
            "full_name": new_candidate["full_name"],
            "email": new_candidate["email"],
            "phone": new_candidate["phone"],
            "location": new_candidate["location"],
            "experience_years": new_candidate["experience_years"],
            "skills": new_candidate["skills"],
            "education": new_candidate["education"],
            "resume_url": new_candidate["resume_url"],
            "is_active": new_candidate["is_active"],
            "created_at": new_candidate["created_at"],
            "message": f"Candidate created successfully (mock) - ID: {new_id}"
        }
        
    except Exception as e:
        logger.error(f"Error in mock candidate creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create candidate"
        )



