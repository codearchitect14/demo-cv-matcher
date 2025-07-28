from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from config.database import get_db_session
from models.candidate import Candidate
from api.routers.auth import get_current_user
from recommender.semantic import SemanticSearchService
from services.personalization_service import personalization_service

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

class JobRecommendation(BaseModel):
    job_id: int
    title: str
    company: str
    location: str
    domain: str
    salary_min: int
    salary_max: int
    similarity_score: float
    filter_score: float
    personalization_score: Optional[float] = None
    final_score: float
    explanation: str

class CandidateRecommendation(BaseModel):
    candidate_id: int
    name: str
    location: str
    domain: str
    expected_salary_min: int
    expected_salary_max: int
    similarity_score: float
    filter_score: float
    personalization_score: Optional[float] = None
    final_score: float
    explanation: str

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    apply_filters: bool = True
    strict_mode: bool = False
    use_ml_ranking: bool = True

@router.get("/candidates/{candidate_id}/job-recommendations")
async def get_job_recommendations(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50),
    apply_filters: bool = Query(True, description="Apply business rule filters"),
    strict_mode: bool = Query(False, description="Use strict filtering mode"),
    use_ml_ranking: bool = Query(True, description="Use ML-based ranking")
):
    """Get job recommendations for a candidate"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only get recommendations for own profile"
            )
        
        # Get candidate profile for semantic search
        from db.crud.candidate import candidate as candidate_crud
        candidate = await candidate_crud.get_with_experiences(db, id=candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        # Initialize semantic search service
        semantic_service = SemanticSearchService()
        
        # Get job recommendations
        recommendations = await semantic_service.find_similar_jobs(
            db, candidate, limit=limit, apply_filters=apply_filters, 
            strict_mode=strict_mode, use_ml_ranking=use_ml_ranking
        )
        
        # Personalize recommendations
        personalized_recommendations = await personalization_service.personalize_job_recommendations(
            db, candidate_id, recommendations, use_ml_scoring=use_ml_ranking
        )
        
        return personalized_recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job recommendations: {str(e)}"
        )

@router.get("/jobs/{job_id}/candidate-recommendations")
async def get_candidate_recommendations(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50),
    apply_filters: bool = Query(True, description="Apply business rule filters"),
    strict_mode: bool = Query(False, description="Use strict filtering mode"),
    use_ml_ranking: bool = Query(True, description="Use ML-based ranking")
):
    """Get candidate recommendations for a job"""
    try:
        # Get job details
        from db.crud.job import job as job_crud
        job = await job_crud.get_with_mandatory_skills(db, id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Initialize semantic search service
        semantic_service = SemanticSearchService()
        
        # Get candidate recommendations
        recommendations = await semantic_service.find_similar_candidates(
            db, job, limit=limit, apply_filters=apply_filters,
            strict_mode=strict_mode, use_ml_ranking=use_ml_ranking
        )
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candidate recommendations: {str(e)}"
        )

@router.post("/search/jobs")
async def semantic_job_search(
    search_request: SearchRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Semantic job search"""
    try:
        # Initialize semantic search service
        semantic_service = SemanticSearchService()
        
        # Perform semantic search
        results = await semantic_service.search_jobs(
            db, search_request.query, limit=search_request.limit,
            apply_filters=search_request.apply_filters,
            strict_mode=search_request.strict_mode,
            use_ml_ranking=search_request.use_ml_ranking
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform semantic job search: {str(e)}"
        )

@router.post("/search/candidates")
async def semantic_candidate_search(
    search_request: SearchRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Semantic candidate search"""
    try:
        # Initialize semantic search service
        semantic_service = SemanticSearchService()
        
        # Perform semantic search
        results = await semantic_service.search_candidates(
            db, search_request.query, limit=search_request.limit,
            apply_filters=search_request.apply_filters,
            strict_mode=search_request.strict_mode,
            use_ml_ranking=search_request.use_ml_ranking
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform semantic candidate search: {str(e)}"
        ) 