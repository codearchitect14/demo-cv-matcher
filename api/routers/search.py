
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from config.database import get_db_session
from recommender.semantic import semantic_search_service
from schemas.search import JobRecommendation, CandidateRecommendation, JobSearchFilter
from db.crud.job import job as job_crud
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])

@router.get("/jobs", response_model=List[JobRecommendation])
async def search_jobs_get(
    location: Optional[str] = Query(None, description="Job location"),
    domain: Optional[str] = Query(None, description="Job domain"),
    title: Optional[str] = Query(None, description="Job title (partial match)"),
    company: Optional[str] = Query(None, description="Company name (partial match)"),
    search: Optional[str] = Query(None, description="Search across title, company, domain, location"),
    salary_min: Optional[int] = Query(None, ge=0, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, ge=0, description="Maximum salary"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search jobs using GET parameters - uses direct asyncpg to avoid PgBouncer issues
    """
    try:
        from config.connection_pool import global_pool
        import asyncio
        
        # Build dynamic WHERE clause
        where_conditions = []
        params = []
        param_count = 0
        
        if domain:
            param_count += 1
            where_conditions.append(f"domain ILIKE ${param_count}")
            params.append(f"%{domain}%")
        
        if location:
            param_count += 1
            where_conditions.append(f"location ILIKE ${param_count}")
            params.append(f"%{location}%")

        if title:
            param_count += 1
            where_conditions.append(f"title ILIKE ${param_count}")
            params.append(f"%{title}%")

        if company:
            param_count += 1
            where_conditions.append(f"company ILIKE ${param_count}")
            params.append(f"%{company}%")

        if search:
            param_count += 1
            like = f"%{search}%"
            where_conditions.append(
                f"(title ILIKE ${param_count} OR company ILIKE ${param_count} OR domain ILIKE ${param_count} OR location ILIKE ${param_count})"
            )
            params.append(like)
        
        if salary_min is not None:
            param_count += 1
            where_conditions.append(f"salary_min >= ${param_count}")
            params.append(salary_min)
        
        if salary_max is not None:
            param_count += 1
            where_conditions.append(f"salary_max <= ${param_count}")
            params.append(salary_max)
        
        # Build the query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Use direct asyncpg query with timeout
        query = f"""
            SELECT id, title, company, location, salary_min, salary_max, domain, total_years_required
            FROM jobs 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count + 1}
        """
        params.append(limit)
        
        # Execute with timeout to prevent hanging
        rows = await asyncio.wait_for(
            global_pool.fetch(query, *params),
            timeout=10.0
        )

        # Convert to response format WITHOUT any scoring (deterministic)
        job_recommendations: List[JobRecommendation] = []
        for row in rows:
            job_id, title, company, job_location, job_salary_min, job_salary_max, job_domain, total_years = row
            job_recommendations.append(JobRecommendation(
                job_id=job_id,
                title=title,
                company=company or "Unknown Company",
                location=job_location,
                salary_min=job_salary_min,
                salary_max=job_salary_max,
                domain=job_domain,
                match_score=None,
                is_valid=True,
                validation_reasons=[],
                explanation="Search result (no scoring)"
            ))
        logger.info(f"Found {len(job_recommendations)} jobs matching search criteria")
        return job_recommendations
        
    except asyncio.TimeoutError:
        logger.error("Search jobs timeout")
        return []
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        return []  # Return empty list instead of raising exception to prevent 500 errors

@router.post("/jobs", response_model=List[JobRecommendation])
async def search_jobs(
    search_filter: JobSearchFilter,
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search jobs based on filters (location, domain, salary, skills) - uses direct asyncpg to avoid PgBouncer issues
    """
    try:
        from config.connection_pool import global_pool
        import asyncio
        
        # Build dynamic WHERE clause
        where_conditions = []
        params = []
        param_count = 0
        
        if search_filter.domain:
            param_count += 1
            where_conditions.append(f"domain ILIKE ${param_count}")
            params.append(f"%{search_filter.domain}%")
        
        if search_filter.location:
            param_count += 1
            where_conditions.append(f"location ILIKE ${param_count}")
            params.append(f"%{search_filter.location}%")
        
        if search_filter.salary_min is not None:
            param_count += 1
            where_conditions.append(f"salary_min >= ${param_count}")
            params.append(search_filter.salary_min)
        
        if search_filter.salary_max is not None:
            param_count += 1
            where_conditions.append(f"salary_max <= ${param_count}")
            params.append(search_filter.salary_max)
        
        # Build the query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Use direct asyncpg query with timeout
        query = f"""
            SELECT id, title, company, location, salary_min, salary_max, domain, total_years_required
            FROM jobs 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count + 1}
        """
        params.append(limit)
        
        # Execute with timeout to prevent hanging
        rows = await asyncio.wait_for(
            global_pool.fetch(query, *params),
            timeout=10.0
        )

        # Convert to response format WITHOUT any scoring (deterministic)
        job_recommendations: List[JobRecommendation] = []
        for row in rows:
            job_id, title, company, job_location, job_salary_min, job_salary_max, job_domain, total_years = row
            job_recommendations.append(JobRecommendation(
                job_id=job_id,
                title=title,
                company=company or "Unknown Company",
                location=job_location,
                salary_min=job_salary_min,
                salary_max=job_salary_max,
                domain=job_domain,
                match_score=None,
                is_valid=True,
                validation_reasons=[],
                explanation="Search result (no scoring)"
            ))
        logger.info(f"Found {len(job_recommendations)} jobs matching search criteria")
        return job_recommendations
        
    except asyncio.TimeoutError:
        logger.error("Search jobs timeout")
        return []
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        return []  # Return empty list instead of raising exception to prevent 500 errors

@router.post("/jobs/recommend", response_model=List[JobRecommendation])
async def recommend_jobs_for_candidate(
    candidate_id: int,
    limit: int = Query(10, ge=1, le=50),
    apply_filters: bool = Query(True, description="Apply business rule filtering"),
    strict_mode: bool = Query(True, description="Enforce all constraints strictly"),
    use_ml_ranking: bool = Query(True, description="Use ML-based ranking"),
    db: AsyncSession = Depends(get_db_session)
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
                company=job.company or "Unknown Company",
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
        
        logger.info(f"Generated {len(job_recommendations)} job recommendations for candidate {candidate_id}")
        return job_recommendations
        
    except ValueError as e:
        logger.error(f"Validation error in job recommendations: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request parameters: {str(e)}")
    except ConnectionError as e:
        logger.error(f"Database connection error in job recommendations: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except ImportError as e:
        logger.error(f"ML model import error in job recommendations: {e}")
        raise HTTPException(status_code=503, detail="ML service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in job recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job recommendations: {str(e)}")

@router.post("/candidates/recommend", response_model=List[CandidateRecommendation])
async def recommend_candidates_for_job(
    job_id: int,
    limit: int = Query(10, ge=1, le=50),
    apply_filters: bool = Query(True, description="Apply business rule filtering"),
    strict_mode: bool = Query(True, description="Enforce all constraints strictly"),
    use_ml_ranking: bool = Query(True, description="Use ML-based ranking"),
    db: AsyncSession = Depends(get_db_session)
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
        
        logger.info(f"Generated {len(candidate_recommendations)} candidate recommendations for job {job_id}")
        return candidate_recommendations
        
    except ValueError as e:
        logger.error(f"Validation error in candidate recommendations: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request parameters: {str(e)}")
    except ConnectionError as e:
        logger.error(f"Database connection error in candidate recommendations: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except ImportError as e:
        logger.error(f"ML model import error in candidate recommendations: {e}")
        raise HTTPException(status_code=503, detail="ML service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in candidate recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get candidate recommendations: {str(e)}")

@router.post("/index/jobs")
async def index_jobs(db: AsyncSession = Depends(get_db_session)):
    """Index all jobs for semantic search"""
    try:
        await semantic_search_service.index_jobs(db)
        logger.info("Jobs indexed successfully")
        return {"message": "Jobs indexed successfully"}
    except ConnectionError as e:
        logger.error(f"Database connection error during job indexing: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")
    except ImportError as e:
        logger.error(f"Embedding model import error during job indexing: {e}")
        raise HTTPException(status_code=503, detail="Embedding service unavailable")
    except Exception as e:
        logger.error(f"Failed to index jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to index jobs: {str(e)}")

@router.post("/index/candidates")
async def index_candidates(db: AsyncSession = Depends(get_db_session)):
    """Index all candidates for semantic search"""
    try:
        await semantic_search_service.index_candidates(db)
        logger.info("Candidates indexed successfully")
        return {"message": "Candidates indexed successfully"}
    except ConnectionError as e:
        logger.error(f"Database connection error during candidate indexing: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")
    except ImportError as e:
        logger.error(f"Embedding model import error during candidate indexing: {e}")
        raise HTTPException(status_code=503, detail="Embedding service unavailable")
    except Exception as e:
        logger.error(f"Failed to index candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to index candidates: {str(e)}")

@router.get("/index/stats")
async def get_index_stats():
    """Get semantic search index statistics"""
    try:
        stats = semantic_search_service.get_index_stats()
        logger.info("Retrieved index statistics")
        return stats
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get index stats: {str(e)}")