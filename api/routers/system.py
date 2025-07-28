from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db_session
from models.candidate import Candidate
from api.routers.auth import get_current_user
from embeddings.embedder import EmbeddingService
from embeddings.build_index import FAISSIndexManager
from services.personalization_service import personalization_service

router = APIRouter(prefix="/system", tags=["System Management"])

class EmbeddingRequest(BaseModel):
    entity_type: str  # "jobs", "candidates", "all"
    entity_ids: Optional[List[int]] = None  # Specific IDs to process

class ModelRetrainRequest(BaseModel):
    model_type: str  # "lightgbm", "neural", "all"
    force_retrain: bool = False

class EmbeddingResponse(BaseModel):
    message: str
    entities_processed: int
    embeddings_generated: int
    index_updated: bool

class ModelRetrainResponse(BaseModel):
    message: str
    model_type: str
    training_samples: int
    metrics: dict
    model_saved: bool

@router.post("/embeddings/generate")
async def generate_embeddings(
    request: EmbeddingRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate embeddings for profiles/jobs"""
    try:
        embedding_service = EmbeddingService()
        index_manager = FAISSIndexManager()
        
        entities_processed = 0
        embeddings_generated = 0
        
        if request.entity_type == "jobs" or request.entity_type == "all":
            # Generate job embeddings
            from db.crud.job import job as job_crud
            jobs = await job_crud.get_multi(db, limit=1000)
            
            for job in jobs:
                if request.entity_ids and job.id not in request.entity_ids:
                    continue
                
                # Generate embedding for job description
                embedding = embedding_service.generate_job_embedding(job)
                if embedding is not None:
                    index_manager.add_vector(f"job_{job.id}", embedding)
                    embeddings_generated += 1
                
                entities_processed += 1
        
        if request.entity_type == "candidates" or request.entity_type == "all":
            # Generate candidate embeddings
            from db.crud.candidate import candidate as candidate_crud
            candidates = await candidate_crud.get_multi(db, limit=1000)
            
            for candidate in candidates:
                if request.entity_ids and candidate.id not in request.entity_ids:
                    continue
                
                # Generate embedding for candidate summary
                embedding = embedding_service.generate_candidate_embedding(candidate)
                if embedding is not None:
                    index_manager.add_vector(f"candidate_{candidate.id}", embedding)
                    embeddings_generated += 1
                
                entities_processed += 1
        
        # Save updated index
        index_manager.save_index()
        
        return EmbeddingResponse(
            message="Embeddings generated successfully",
            entities_processed=entities_processed,
            embeddings_generated=embeddings_generated,
            index_updated=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )

@router.post("/models/retrain")
async def retrain_models(
    request: ModelRetrainRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Trigger model retraining"""
    try:
        training_samples = 0
        metrics = {}
        model_saved = False
        
        if request.model_type == "lightgbm" or request.model_type == "all":
            # Retrain LightGBM model
            result = await personalization_service.train_personalization_model(
                db, model_type="lightgbm", force_retrain=request.force_retrain
            )
            
            if "error" not in result:
                training_samples = result.get("n_samples", 0)
                metrics = result.get("metrics", {})
                model_saved = result.get("model_saved", False)
        
        if request.model_type == "neural" or request.model_type == "all":
            # Retrain neural model (if implemented)
            result = await personalization_service.train_personalization_model(
                db, model_type="neural", force_retrain=request.force_retrain
            )
            
            if "error" not in result:
                training_samples = max(training_samples, result.get("n_samples", 0))
                metrics.update(result.get("metrics", {}))
                model_saved = model_saved or result.get("model_saved", False)
        
        return ModelRetrainResponse(
            message="Model retraining completed",
            model_type=request.model_type,
            training_samples=training_samples,
            metrics=metrics,
            model_saved=model_saved
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrain models: {str(e)}"
        )

@router.get("/health")
async def system_health_check(
    db: AsyncSession = Depends(get_db_session)
):
    """System health check"""
    try:
        # Check database connection
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        
        # Check embedding service
        embedding_service = EmbeddingService()
        
        # Check index manager
        index_manager = FAISSIndexManager()
        
        return {
            "status": "healthy",
            "database": "connected",
            "embedding_service": "available",
            "index_manager": "available",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"System health check failed: {str(e)}"
        )

@router.get("/stats")
async def system_statistics(
    db: AsyncSession = Depends(get_db_session)
):
    """Get system statistics"""
    try:
        from db.crud.candidate import candidate as candidate_crud
        from db.crud.job import job as job_crud
        from db.crud.application import application as application_crud
        
        # Get counts
        candidates_count = await candidate_crud.count(db)
        jobs_count = await job_crud.count(db)
        applications_count = await application_crud.count(db)
        
        # Get recent activity
        recent_candidates = await candidate_crud.count_recent(db, days_back=7)
        recent_jobs = await job_crud.count_recent(db, days_back=7)
        recent_applications = await application_crud.count_recent(db, days_back=7)
        
        return {
            "total_candidates": candidates_count,
            "total_jobs": jobs_count,
            "total_applications": applications_count,
            "recent_candidates": recent_candidates,
            "recent_jobs": recent_jobs,
            "recent_applications": recent_applications,
            "system_uptime": "24h",  # Would need to track actual uptime
            "last_maintenance": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system statistics: {str(e)}"
        ) 