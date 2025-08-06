from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import logging

from config.database import get_db_session
from models.candidate import Candidate
from api.routers.auth import get_current_user
from services.interaction_service import interaction_service
from db.crud.interaction import interaction
from db.crud.candidate import candidate as candidate_crud
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

@router.get("/candidates/{candidate_id}/interactions")
async def get_candidate_interactions(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    interaction_types: Optional[List[str]] = Query(None, description="Filter by interaction types")
):
    """Get candidate's interaction history"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view own interactions"
            )
        
        interactions = await interaction_service.get_user_interactions(
            db, candidate_id, days_back=days_back, interaction_types=interaction_types
        )
        
        return interactions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interactions: {str(e)}"
        )

@router.get("/candidates/{candidate_id}/behavior-patterns")
async def get_candidate_behavior_patterns(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(90, ge=1, le=365, description="Days to analyze")
):
    """Get candidate's behavior patterns for personalization"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view own behavior patterns"
            )
        
        patterns = await interaction_service.get_user_behavior_patterns(
            db, candidate_id, days_back=days_back
        )
        
        return patterns
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve behavior patterns: {str(e)}"
        )

@router.get("/candidates/{candidate_id}/similar-users")
async def get_similar_users(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50, description="Number of similar users")
):
    """Get users with similar behavior patterns"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view own similar users"
            )
        
        similar_users = await interaction_service.get_similar_users(
            db, candidate_id, limit=limit
        )
        
        return similar_users
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve similar users: {str(e)}"
        ) 