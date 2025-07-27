#Today's date: 25/07/2025
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.candidate_service import CandidateService
from db.session import get_db
from models.candidate import CandidateResponse

router = APIRouter(prefix="/candidates", tags=["candidates"])

class CandidateCreate(BaseModel):
    name: str
    email: str
    phone: str
    location: str
    domain: str
    expected_salary_min: float
    expected_salary_max: float

@router.get("/", response_model=List[CandidateResponse])
async def get_candidates(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = CandidateService(db)
        return await service.get_candidates(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    candidate: CandidateCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = CandidateService(db)
        return await service.create_candidate(candidate.dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )