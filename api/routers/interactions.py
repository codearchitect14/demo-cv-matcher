from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
from pydantic import BaseModel
import logging

from config.database import get_db_session
from models.candidate import Candidate
from models.recruiter import Recruiter
from api.routers.auth import get_current_recruiter_or_user
from services.interaction_service import interaction_service
from db.crud.interaction import interaction
from db.crud.candidate import candidate as candidate_crud
from db.crud.recruiter import recruiter as recruiter_crud
from db.crud.job import job as job_crud
from schemas.interaction import InteractionLogCreate, InteractionLogResponse
from models.interaction import InteractionTypeEnum

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Interactions"])

class InteractionCreate(BaseModel):
    job_id: int
    interaction_type: str  # "View", "Applied", "Rejected", "Saved"

class InteractionResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    interaction_type: str
    created_at: str
    
    class Config:
        from_attributes = True

@router.post("/log-interaction/", response_model=dict)
async def log_interaction(
    interaction: InteractionLogCreate,
    db: AsyncSession = Depends(get_db_session)
):
    # Validate user
    user = await candidate_crud.get(db, id=interaction.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Validate job
    job = await job_crud.get(db, id=interaction.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Log interaction
    await interaction.log_interaction(db, interaction)
    return {"message": "Interaction logged successfully"}

@router.get("/test-auth")
async def test_authentication(
    current_user: Union[Candidate, Recruiter] = Depends(get_current_recruiter_or_user)
):
    """Test endpoint to check authentication"""
    return {
        "user_type": type(current_user).__name__,
        "user_id": current_user.id,
        "email": current_user.email,
        "message": "Authentication working correctly"
    }

@router.get("/debug-user/{email}")
async def debug_user_by_email(
    email: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Debug endpoint to check what users exist with a given email"""
    try:
        # Check for candidate
        candidate = await candidate_crud.get_by_email(db, email)
        candidate_info = None
        if candidate:
            candidate_info = {
                "id": candidate.id,
                "email": candidate.email,
                "name": candidate.name,
                "role": getattr(candidate, 'role', 'N/A'),
                "type": "Candidate"
            }
        
        # Check for recruiter
        recruiter = await recruiter_crud.get_by_email(db, email)
        recruiter_info = None
        if recruiter:
            recruiter_info = {
                "id": recruiter.id,
                "email": recruiter.email,
                "name": recruiter.full_name,
                "role": getattr(recruiter, 'role', 'N/A'),
                "type": "Recruiter"
            }
        
        return {
            "email": email,
            "candidate": candidate_info,
            "recruiter": recruiter_info,
            "message": "Debug info for email"
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/candidates/{candidate_id}/interactions")
async def get_candidate_interactions(
    candidate_id: int,
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    interaction_types: Optional[List[str]] = Query(None, description="Filter by interaction types")
):
    """Get candidate's interaction history - public endpoint for testing"""
    try:
        logger.info(f"Fetching interactions for candidate {candidate_id}")
        interactions = await interaction_service.get_user_interactions(
            db, candidate_id, days_back=days_back, interaction_types=interaction_types
        )
        
        return interactions
        
    except Exception as e:
        logger.error(f"Error in get_candidate_interactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interactions: {str(e)}"
        )

@router.get("/public/candidates/{candidate_id}/interactions")
async def get_candidate_interactions_public(
    candidate_id: int,
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    interaction_types: Optional[List[str]] = Query(None, description="Filter by interaction types")
):
    """Public endpoint to get candidate's interaction history (no auth - for testing)"""
    try:
        interactions = await interaction_service.get_user_interactions(
            db, candidate_id, days_back=days_back, interaction_types=interaction_types
        )
        return interactions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interactions: {str(e)}"
        )

@router.get("/candidates/{candidate_id}/behavior-patterns")
async def get_candidate_behavior_patterns(
    candidate_id: int,
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(90, ge=1, le=365, description="Days to analyze")
):
    """Get candidate's behavior patterns for personalization - public endpoint for testing"""
    try:
        patterns = await interaction_service.get_user_behavior_patterns(
            db, candidate_id, days_back=days_back
        )
        return patterns
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve behavior patterns: {str(e)}"
        )

@router.get("/public/candidates/{candidate_id}/behavior-patterns")
async def get_candidate_behavior_patterns_public(
    candidate_id: int,
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(90, ge=1, le=365, description="Days to analyze")
):
    """Public endpoint to get behavior patterns (no auth - for testing)"""
    try:
        patterns = await interaction_service.get_user_behavior_patterns(
            db, candidate_id, days_back=days_back
        )
        return patterns
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve behavior patterns: {str(e)}"
        )

@router.get("/candidates/{candidate_id}/similar-users")
async def get_similar_users(
    candidate_id: int,
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50, description="Number of similar users")
):
    """Get users with similar behavior patterns - public endpoint for testing"""
    try:
        similar_users = await interaction_service.get_similar_users(
            db, candidate_id, limit=limit
        )
        return similar_users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve similar users: {str(e)}"
        )

@router.get("/public/candidates/{candidate_id}/similar-users")
async def get_similar_users_public(
    candidate_id: int,
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50, description="Number of similar users")
):
    """Public endpoint to get similar users (no auth - for testing)"""
    try:
        similar_users = await interaction_service.get_similar_users(
            db, candidate_id, limit=limit
        )
        return similar_users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve similar users: {str(e)}"
        )

@router.get("/recent/")
async def get_recent_interactions(
    limit: int = Query(20, ge=1, le=100, description="Number of recent interactions")
):
    """Get recent interactions across all candidates for dashboard view - uses direct asyncpg"""
    try:
        from config.connection_pool import global_pool
        import asyncio
        
        # Debug: Check if there are any interactions at all
        debug_query = "SELECT COUNT(*) FROM interaction_log WHERE user_type = 'candidate' OR user_type IS NULL"
        total_interactions = await global_pool.fetchval(debug_query)
        logger.info(f"Total candidate interactions in database: {total_interactions}")
        
        # Use direct asyncpg query to get recent interactions
        query = """
            SELECT 
                i.id,
                i.user_id as candidate_id,
                i.job_id,
                i.interaction_type,
                i.timestamp,
                c.name as candidate_name,
                c.email as candidate_email,
                j.title as job_title,
                j.company
            FROM interaction_log i
            LEFT JOIN candidates c ON i.user_id = c.id
            LEFT JOIN jobs j ON i.job_id = j.id
            WHERE i.user_type = 'candidate' OR i.user_type IS NULL
            ORDER BY i.timestamp DESC
            LIMIT $1
        """
        
        rows = await asyncio.wait_for(
            global_pool.fetch(query, limit),
            timeout=5.0
        )
        
        interactions = []
        for row in rows:
            interaction = {
                "id": row["id"],
                "candidate_id": row["candidate_id"],
                "job_id": row["job_id"],
                "interaction_type": row["interaction_type"],
                "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
                "candidate_name": row["candidate_name"] or "Unknown",
                "candidate_email": row["candidate_email"] or "",
                "job_title": row["job_title"] or f"Job #{row['job_id']}",
                "company": row["company"] or ""
            }
            interactions.append(interaction)
        
        logger.info(f"Retrieved {len(interactions)} recent interactions")
        return interactions
        
    except asyncio.TimeoutError:
        logger.error("Recent interactions query timeout")
        return []
    except Exception as e:
        logger.error(f"Error in get_recent_interactions: {str(e)}")
        return []