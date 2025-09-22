import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc, func
# Interaction model not available - using placeholder
from sqlalchemy.orm import selectinload
from models.job import Job
from models.candidate import Candidate
from models.job_skill import JobSkill
from models.skill import Skill
from embeddings.embedder import OptimizedEmbeddingService
from services.adaptive_weighting_service import adaptive_weighting_service
from services.cold_start_handler import cold_start_handler
from services.cache_service import cache_service
from services.faiss_service import faiss_service

logger = logging.getLogger(__name__)

class SemanticSearchService:
    """Enhanced semantic search service with adaptive weighting and cold start handling"""
    
    def __init__(self):
        self.embedding_service = OptimizedEmbeddingService()
        self.cache_service = cache_service
        
    async def find_similar_jobs(
        self, 
        candidate_id: int, 
        db: AsyncSession, 
        k: int = 10, 
        apply_filters: bool = True,
        use_ml_ranking: bool = True
    ) -> List[Dict[str, Any]]:
        """Find similar jobs for a candidate with adaptive weighting"""
        
        try:
            # Check cache first
            cache_key = f"job_recommendations_{candidate_id}_{k}"
            try:
                cached_result = await self.cache_service.get("recommendation", cache_key)
                if cached_result:
                    logger.info(f"[INFO] Retrieved job recommendations from cache for candidate {candidate_id}")
                    return cached_result
            except Exception as e:
                logger.warning(f"[WARNING] Cache service error: {e}")
            
            # Get candidate details
            candidate_result = await db.execute(
                select(Candidate)
                .where(Candidate.id == candidate_id)
            )
            candidate = candidate_result.scalar_one_or_none()
            
            if not candidate:
                logger.warning(f"[WARNING] Candidate {candidate_id} not found")
                return []
            
            # Check if user has any interactions (placeholder - Interaction model not available)
            interaction_count = 0
            
            # Preferred path: FAISS recall -> filters -> (optional) ML ranking
            # Guard FAISS with try/except to avoid cascading failures
            try:
                faiss_results = await faiss_service.search_jobs_for_candidate(db, candidate_id, k=max(k * 5, 50))
            except Exception as e:
                logger.warning(f"[WARNING] FAISS search failed: {e}; falling back to cold start")
                faiss_results = []
            candidate_faiss_job_ids = [int(r['vector_id'].split(':', 1)[1]) for r in faiss_results if 'vector_id' in r and r['vector_id'].startswith('job:')]

            if candidate_faiss_job_ids:
                # Fetch these jobs and score with existing logic
                jobs_result = await db.execute(
                    select(Job).where(Job.id.in_(candidate_faiss_job_ids), Job.is_active == True)
                )
                jobs = jobs_result.scalars().all()
            else:
                # Fallback to cold start if FAISS returns nothing
                logger.info(f"[INFO] FAISS returned no results; using cold start for candidate {candidate_id}")
                cold_start_recs = await cold_start_handler.handle_new_user_recommendations(db, candidate_id, k)
                recommendations = [{
                    'job_id': rec['job_id'],
                    'job': rec['job'],
                    'combined_score': rec['score'],
                    'method': rec['method'],
                    'weights_used': {'cold_start': 1.0}
                } for rec in cold_start_recs]
                try:
                    await self.cache_service.set("recommendation", cache_key, recommendations, ttl=300)
                except Exception as e:
                    logger.warning(f"[WARNING] Cache service error: {e}")
                return recommendations
            
            # Get adaptive weights
            # Note: We need a job_id for adaptive weighting, so we'll use a placeholder
            # In a real implementation, you'd get this from the candidate's preferences or recent applications
            sample_job_result = await db.execute(
                select(Job.id)
                .where(Job.is_active == True)
                .limit(1)
            )
            sample_job_id = sample_job_result.scalar()
            
            if sample_job_id:
                adaptive_weights = await adaptive_weighting_service.get_adaptive_weights(
                    db, candidate_id, sample_job_id
                )
            else:
                adaptive_weights = {'semantic': 0.7, 'filter': 0.3}
            
            # Get candidate embedding
            candidate_text = f"{candidate.summary or ''} {candidate.domain or ''} {candidate.role or ''}"
            candidate_embedding = await self.embedding_service.get_embedding(candidate_text)
            
            if candidate_embedding is None:
                logger.warning(f"[WARNING] Failed to generate embedding for candidate {candidate_id}")
                return []
            
            if not jobs:
                return []
            
            # Get job IDs for bulk skill loading
            job_ids = [job.id for job in jobs]
            
            # Get all job skills in one query
            job_skills_result = await db.execute(
                select(JobSkill)
                .where(JobSkill.job_id.in_(job_ids))
            )
            job_skills = job_skills_result.scalars().all()
            
            # Group skills by job
            job_skills_map = {}
            for js in job_skills:
                if js.job_id not in job_skills_map:
                    job_skills_map[js.job_id] = []
                job_skills_map[js.job_id].append(js)
            
            # Calculate similarities
            recommendations = []
            for job in jobs:
                # Get job skills
                job_skill_objects = job_skills_map.get(job.id, [])
                
                # Create job text for embedding
                job_text = f"{job.title} {job.description or ''}"
                if job_skill_objects:
                    skill_names = [js.skill.name for js in job_skill_objects if js.skill]
                    job_text += f" {' '.join(skill_names)}"
                
                # Get job embedding
                job_embedding = await self.embedding_service.get_embedding(job_text)
                
                if job_embedding is not None:
                    # Calculate semantic similarity
                    semantic_similarity = np.dot(candidate_embedding, job_embedding)
                    
                    # Calculate filter score
                    filter_score = self._calculate_filter_score(candidate, job, job_skill_objects)
                    
                    # Apply adaptive weights
                    combined_score = (
                        semantic_similarity * adaptive_weights['semantic'] +
                        filter_score * adaptive_weights['filter']
                    )
                    
                    recommendations.append({
                        'job_id': job.id,
                        'job': job,
                        'semantic_score': semantic_similarity,
                        'filter_score': filter_score,
                        'combined_score': combined_score,
                        'weights_used': adaptive_weights,
                        'method': 'adaptive_semantic'
                    })
            
            # Sort by combined score
            recommendations.sort(key=lambda x: x['combined_score'], reverse=True)
            
            # Apply ML ranking if requested
            if use_ml_ranking:
                recommendations = await self._apply_ml_ranking(recommendations, candidate, db)
            
            # Cache the results
            try:
                await self.cache_service.set("recommendation", cache_key, recommendations[:k], ttl=300)
            except Exception as e:
                logger.warning(f"[WARNING] Cache service error: {e}")
            
            logger.info(f"[INFO] Generated {len(recommendations)} recommendations for candidate {candidate_id}")
            return recommendations[:k]
            
        except Exception as e:
            logger.error(f"Failed to find similar jobs: {e}")
            return []
    
    def _calculate_filter_score(
        self, 
        candidate: Candidate, 
        job: Job, 
        job_skills: List[JobSkill]
    ) -> float:
        """Calculate filter-based score"""
        
        score = 0.0
        
        # Domain match
        if candidate.domain and job.domain:
            if candidate.domain.lower() == job.domain.lower():
                score += 0.3
        
        # Location match
        if candidate.location and job.location:
            if candidate.location.lower() in job.location.lower():
                score += 0.2
        
        # Salary match
        if candidate.expected_salary_min and job.salary_max:
            if candidate.expected_salary_min <= job.salary_max:
                score += 0.2
        
        # Role match
        if candidate.role and job.title:
            if candidate.role.lower() in job.title.lower():
                score += 0.2
        
        # Skill match (simplified)
        if job_skills:
            score += min(0.1, len(job_skills) * 0.02)
        
        return min(1.0, score)
    
    async def _apply_ml_ranking(
        self, 
        recommendations: List[Dict[str, Any]], 
        candidate: Candidate,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Apply ML-based ranking to recommendations"""
        
        # This is a placeholder for ML ranking
        # In a real implementation, you'd use a trained model
        
        for rec in recommendations:
            # Add some ML-based adjustments
            job = rec['job']
            
            # Boost score for jobs in candidate's preferred domain
            if candidate.domain and job.domain:
                if candidate.domain.lower() == job.domain.lower():
                    rec['combined_score'] *= 1.1
            
            # Boost score for jobs in candidate's location
            if candidate.location and job.location:
                if candidate.location.lower() in job.location.lower():
                    rec['combined_score'] *= 1.05
        
        # Re-sort by adjusted scores
        recommendations.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return recommendations

# Global instance
semantic_search_service = SemanticSearchService()
