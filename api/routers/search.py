
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from db.connection import get_db
from recommender.semantic import semantic_search_service
from schemas.search import JobRecommendation, CandidateRecommendation

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/jobs/recommend", response_model=List[JobRecommendation])
async def recommend_jobs_for_candidate(
    candidate_id: int,
    limit: int = Query(10, ge=1, le=50),
    apply_filters: bool = Query(True, description="Apply business rule filtering"),
    strict_mode: bool = Query(True, description="Enforce all constraints strictly"),
    use_ml_ranking: bool = Query(True, description="Use ML-based ranking"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get job recommendations for a candidate using semantic search + filtering + ML ranking
    """
    try:
        recommendations = await semantic_search_service.find_similar_jobs(
            candidate_id=candidate_id,
            db=db,
            k=limit,
            apply_filters=apply_filters,
            strict_mode=strict_mode,
            use_ml_ranking=use_ml_ranking
        )
        
        # Convert to response format
        job_recommendations = []
        for rec in recommendations:
            job = rec["job"]
            validation = rec.get("validation", {})
            
            job_recommendations.append(JobRecommendation(
                job_id=rec["job_id"],
                title=job.title,
                company=job.company or "Unknown",
                location=job.location,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                domain=job.domain,
                similarity_score=rec.get("similarity_score", 0),
                combined_score=rec.get("combined_score", 0),
                filter_score=validation.get("filter_score", 0),
                ml_score=rec.get("ml_score", 0),
                is_valid=validation.get("is_valid", True),
                validation_reasons=validation.get("reasons", []),
                explanation=rec.get("explanation", "")
            ))
        
        return job_recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job recommendations: {str(e)}")

@router.post("/candidates/recommend", response_model=List[CandidateRecommendation])
async def recommend_candidates_for_job(
    job_id: int,
    limit: int = Query(10, ge=1, le=50),
    apply_filters: bool = Query(True, description="Apply business rule filtering"),
    strict_mode: bool = Query(True, description="Enforce all constraints strictly"),
    use_ml_ranking: bool = Query(True, description="Use ML-based ranking"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get candidate recommendations for a job using semantic search + filtering + ML ranking
    """
    try:
        recommendations = await semantic_search_service.find_similar_candidates(
            job_id=job_id,
            db=db,
            k=limit,
            apply_filters=apply_filters,
            strict_mode=strict_mode,
            use_ml_ranking=use_ml_ranking
        )
        
        # Convert to response format
        candidate_recommendations = []
        for rec in recommendations:
            candidate = rec["candidate"]
            validation = rec.get("validation", {})
            
            candidate_recommendations.append(CandidateRecommendation(
                candidate_id=rec["candidate_id"],
                name=candidate.name,
                location=candidate.location,
                domain=candidate.domain,
                expected_salary_min=candidate.expected_salary_min,
                expected_salary_max=candidate.expected_salary_max,
                similarity_score=rec.get("similarity_score", 0),
                combined_score=rec.get("combined_score", 0),
                filter_score=validation.get("filter_score", 0),
                ml_score=rec.get("ml_score", 0),
                is_valid=validation.get("is_valid", True),
                validation_reasons=validation.get("reasons", []),
                explanation=rec.get("explanation", "")
            ))
        
        return candidate_recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get candidate recommendations: {str(e)}")

@router.post("/index/jobs")
async def index_jobs(db: AsyncSession = Depends(get_db)):
    """
    Index all jobs in the database for semantic search
    """
    try:
        await semantic_search_service.index_jobs(db)
        return {"message": "Jobs indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index jobs: {str(e)}")

@router.post("/index/candidates")
async def index_candidates(db: AsyncSession = Depends(get_db)):
    """
    Index all candidates in the database for semantic search
    """
    try:
        await semantic_search_service.index_candidates(db)
        return {"message": "Candidates indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index candidates: {str(e)}")

@router.get("/index/stats")
async def get_index_stats():
    """
    Get FAISS index statistics
    """
    try:
        stats = semantic_search_service.get_index_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get index stats: {str(e)}")