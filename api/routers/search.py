
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.search_service import SearchService
from db.session import get_db

router = APIRouter(prefix="/search", tags=["search"])

class SearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    skip: int = 0
    limit: int = 100

@router.post("/jobs")
async def search_jobs(
    search: SearchQuery,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = SearchService(db)
        return await service.search_jobs(
            query=search.query,
            filters=search.filters,
            skip=search.skip,
            limit=search.limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/candidates")
async def search_candidates(
    search: SearchQuery,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = SearchService(db)
        return await service.search_candidates(
            query=search.query,
            filters=search.filters,
            skip=search.skip,
            limit=search.limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )