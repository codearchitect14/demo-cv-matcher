#Today's date: 25/07/2025
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db_session
from models.candidate import Candidate, CandidateExperience
from db.crud.candidate import candidate as candidate_crud
from db.crud.application import application as application_crud
from api.routers.auth import get_current_user
from schemas.candidate import CandidateCreate, CandidateUpdate, CandidateResponse, CandidateExperienceCreate, CandidateExperienceUpdate

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.post("/", response_model=CandidateResponse)
async def create_candidate(
    candidate_data: CandidateCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new candidate profile"""
    try:
        candidate = await candidate_crud.create(db, obj_in=candidate_data)
        return candidate
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create candidate: {str(e)}"
        )

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get candidate profile by ID"""
    try:
        candidate = await candidate_crud.get_with_experiences(db, id=candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate: {str(e)}"
        )

@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: int,
    candidate_data: CandidateUpdate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update candidate profile (only own profile)"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update own profile"
            )
        
        candidate = await candidate_crud.update(db, db_obj=current_user, obj_in=candidate_data)
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update candidate: {str(e)}"
        )

@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete candidate profile (GDPR compliance)"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete own profile"
            )
        
        # Delete all related data (applications, interactions, experiences)
        await candidate_crud.remove(db, id=candidate_id)
        
        return {"message": "Candidate profile deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete candidate: {str(e)}"
        )

@router.post("/{candidate_id}/experience", response_model=CandidateResponse)
async def add_candidate_experience(
    candidate_id: int,
    experience_data: CandidateExperienceCreate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Add experience to candidate profile"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only add experience to own profile"
            )
        
        candidate = await candidate_crud.add_experience(
            db, candidate_id=candidate_id, experience_data=experience_data
        )
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add experience: {str(e)}"
        )

@router.put("/{candidate_id}/experience/{experience_id}")
async def update_candidate_experience(
    candidate_id: int,
    experience_id: int,
    experience_data: CandidateExperienceUpdate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update candidate experience"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update own experience"
            )
        
        experience = await candidate_crud.update_experience(
            db, candidate_id=candidate_id, experience_id=experience_id, experience_data=experience_data
        )
        return experience
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update experience: {str(e)}"
        )

@router.delete("/{candidate_id}/experience/{experience_id}")
async def delete_candidate_experience(
    candidate_id: int,
    experience_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete candidate experience"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete own experience"
            )
        
        await candidate_crud.remove_experience(
            db, candidate_id=candidate_id, experience_id=experience_id
        )
        
        return {"message": "Experience deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete experience: {str(e)}"
        )

@router.get("/{candidate_id}/applications")
async def get_candidate_applications(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get candidate's applications"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view own applications"
            )
        
        applications = await application_crud.get_by_candidate(
            db, candidate_id=candidate_id, skip=skip, limit=limit
        )
        return applications
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {str(e)}"
        )

@router.get("/{candidate_id}/interactions")
async def get_candidate_interactions(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(30, ge=1, le=365)
):
    """Get candidate's interaction history"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view own interactions"
            )
        
        from services.interaction_service import interaction_service
        interactions = await interaction_service.get_user_interactions(
            db, candidate_id=candidate_id, days_back=days_back
        )
        return interactions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interactions: {str(e)}"
        )