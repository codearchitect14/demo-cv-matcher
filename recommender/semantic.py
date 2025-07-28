from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from embeddings.embedder import embedding_service
from embeddings.build_index import faiss_manager
from models.job import Job, JobMandatorySkill
from models.candidate import Candidate, CandidateExperience
from db.crud.job import job as job_crud
from db.crud.candidate import candidate as candidate_crud
from .filters import filtering_service
from .ranker import recommendation_engine
import logging

logger = logging.getLogger(__name__)

class SemanticSearchService:
    """Service for semantic job-candidate matching using embeddings and FAISS"""
    
    def __init__(self):
        """Initialize semantic search service"""
        self.embedding_service = embedding_service
        self.faiss_manager = faiss_manager
        self.filtering_service = filtering_service
        self.ranking_engine = recommendation_engine
    
    async def index_jobs(self, db: AsyncSession):
        """Index all jobs in the database"""
        try:
            # Get all jobs with their mandatory skills
            result = await db.execute(
                select(Job)
                .options(selectinload(Job.mandatory_skills))
            )
            jobs = result.scalars().all()
            
            if not jobs:
                logger.info("No jobs found to index")
                return
            
            # Generate embeddings for jobs
            job_vectors = []
            job_ids = []
            
            for job in jobs:
                # Get mandatory skills text
                skills_text = ""
                for skill in job.mandatory_skills:
                    skills_text += f"Required skill: {skill.skill}, Min experience: {skill.min_experience} years. "
                
                # Generate job embedding
                embedding = self.embedding_service.generate_job_embedding(
                    job_title=job.title,
                    job_description=job.job_description or "",
                    domain=job.domain or ""
                )
                
                job_vectors.append(embedding)
                job_ids.append(job.id)
            
            # Add to FAISS index
            self.faiss_manager.add_vectors(job_vectors, job_ids, "job")
            self.faiss_manager.save_index()
            
            logger.info(f"Indexed {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Failed to index jobs: {e}")
            raise
    
    async def index_candidates(self, db: AsyncSession):
        """Index all candidates in the database"""
        try:
            # Get all candidates with their experiences
            result = await db.execute(
                select(Candidate)
                .options(selectinload(Candidate.experiences))
            )
            candidates = result.scalars().all()
            
            if not candidates:
                logger.info("No candidates found to index")
                return
            
            # Generate embeddings for candidates
            candidate_vectors = []
            candidate_ids = []
            
            for candidate in candidates:
                # Convert experiences to dict format
                experiences = []
                for exp in candidate.experiences:
                    experiences.append({
                        "skill": exp.skill,
                        "years": exp.years,
                        "description": exp.description or ""
                    })
                
                # Generate candidate embedding
                embedding = self.embedding_service.generate_candidate_embedding(
                    summary=candidate.summary or "",
                    experiences=experiences
                )
                
                candidate_vectors.append(embedding)
                candidate_ids.append(candidate.id)
            
            # Add to FAISS index
            self.faiss_manager.add_vectors(candidate_vectors, candidate_ids, "candidate")
            self.faiss_manager.save_index()
            
            logger.info(f"Indexed {len(candidates)} candidates")
            
        except Exception as e:
            logger.error(f"Failed to index candidates: {e}")
            raise
    
    async def find_similar_jobs(
        self, 
        candidate_id: int, 
        db: AsyncSession, 
        k: int = 10,
        apply_filters: bool = True,
        strict_mode: bool = True,
        use_ml_ranking: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find similar jobs for a candidate using semantic search + filtering + ML ranking
        
        Args:
            candidate_id: Candidate ID
            db: Database session
            k: Number of results to return
            apply_filters: Whether to apply business rule filtering
            strict_mode: If True, enforce all constraints strictly
            use_ml_ranking: Whether to use ML-based ranking
            
        Returns:
            List of job recommendations with ML scores
        """
        try:
            # Get candidate with experiences
            candidate = await candidate_crud.get_with_experiences(db, candidate_id)
            if not candidate:
                return []
            
            # Generate candidate embedding
            experiences = []
            for exp in candidate.experiences:
                experiences.append({
                    "skill": exp.skill,
                    "years": exp.years,
                    "description": exp.description or ""
                })
            
            candidate_embedding = self.embedding_service.generate_candidate_embedding(
                summary=candidate.summary or "",
                experiences=experiences
            )
            
            # Search for similar jobs
            similar_jobs = self.faiss_manager.search(
                query_vector=candidate_embedding,
                k=k * 2,  # Get more results for filtering
                entity_type="job"
            )
            
            # Get job details
            job_recommendations = []
            for job_id, similarity_score in similar_jobs:
                job = await job_crud.get_with_skills(db, job_id)
                if not job:
                    continue
                
                job_recommendations.append({
                    "job_id": job_id,
                    "job": job,
                    "similarity_score": similarity_score,
                    "explanation": self._generate_explanation(candidate, job, similarity_score)
                })
            
            # Apply business rule filtering if requested
            if apply_filters:
                filtered_jobs = await self.filtering_service.filter_jobs_for_candidate(
                    job_recommendations, candidate, db, strict_mode
                )
                
                # Combine semantic and filter scores
                for job_data in filtered_jobs:
                    semantic_score = job_data.get('similarity_score', 0)
                    filter_score = job_data.get('filter_score', 0)
                    # Combined score: 70% semantic + 30% filter
                    job_data['combined_score'] = (semantic_score * 0.7) + (filter_score * 0.3)
                
                # Apply ML-based ranking if requested
                if use_ml_ranking:
                    ranked_jobs = self.ranking_engine.rank_matches(filtered_jobs)
                    return ranked_jobs[:k]
                else:
                    # Sort by combined score
                    filtered_jobs.sort(key=lambda x: x['combined_score'], reverse=True)
                    return filtered_jobs[:k]
            else:
                # Return only semantic search results
                job_recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
                return job_recommendations[:k]
            
        except Exception as e:
            logger.error(f"Failed to find similar jobs: {e}")
            return []
    
    async def find_similar_candidates(
        self, 
        job_id: int, 
        db: AsyncSession, 
        k: int = 10,
        apply_filters: bool = True,
        strict_mode: bool = True,
        use_ml_ranking: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find similar candidates for a job using semantic search + filtering + ML ranking
        
        Args:
            job_id: Job ID
            db: Database session
            k: Number of results to return
            apply_filters: Whether to apply business rule filtering
            strict_mode: If True, enforce all constraints strictly
            use_ml_ranking: Whether to use ML-based ranking
            
        Returns:
            List of candidate recommendations with ML scores
        """
        try:
            # Get job with mandatory skills
            job = await job_crud.get_with_skills(db, job_id)
            if not job:
                return []
            
            # Generate job embedding
            job_embedding = self.embedding_service.generate_job_embedding(
                job_title=job.title,
                job_description=job.job_description or "",
                domain=job.domain or ""
            )
            
            # Search for similar candidates
            similar_candidates = self.faiss_manager.search(
                query_vector=job_embedding,
                k=k * 2,  # Get more results for filtering
                entity_type="candidate"
            )
            
            # Get candidate details
            candidate_recommendations = []
            for candidate_id, similarity_score in similar_candidates:
                candidate = await candidate_crud.get_with_experiences(db, candidate_id)
                if not candidate:
                    continue
                
                candidate_recommendations.append({
                    "candidate_id": candidate_id,
                    "candidate": candidate,
                    "similarity_score": similarity_score,
                    "explanation": self._generate_explanation(candidate, job, similarity_score)
                })
            
            # Apply business rule filtering if requested
            if apply_filters:
                filtered_candidates = await self.filtering_service.filter_candidates_for_job(
                    candidate_recommendations, job, db, strict_mode
                )
                
                # Combine semantic and filter scores
                for candidate_data in filtered_candidates:
                    semantic_score = candidate_data.get('similarity_score', 0)
                    filter_score = candidate_data.get('filter_score', 0)
                    # Combined score: 70% semantic + 30% filter
                    candidate_data['combined_score'] = (semantic_score * 0.7) + (filter_score * 0.3)
                
                # Apply ML-based ranking if requested
                if use_ml_ranking:
                    ranked_candidates = self.ranking_engine.rank_matches(filtered_candidates)
                    return ranked_candidates[:k]
                else:
                    # Sort by combined score
                    filtered_candidates.sort(key=lambda x: x['combined_score'], reverse=True)
                    return filtered_candidates[:k]
            else:
                # Return only semantic search results
                candidate_recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
                return candidate_recommendations[:k]
            
        except Exception as e:
            logger.error(f"Failed to find similar candidates: {e}")
            return []
    
    def _check_job_compatibility(self, candidate: Candidate, job: Job) -> bool:
        """Check if job is compatible with candidate using structured filters"""
        # Domain match
        if candidate.domain and job.domain and candidate.domain != job.domain:
            return False
        
        # Location match (simplified)
        if candidate.location and job.location:
            # Basic location matching - could be enhanced with geocoding
            if candidate.location.lower() not in job.location.lower() and job.location.lower() not in candidate.location.lower():
                return False
        
        # Salary compatibility
        if candidate.expected_salary_min and job.salary_min:
            if candidate.expected_salary_min > job.salary_max:
                return False
        
        if candidate.expected_salary_max and job.salary_max:
            if candidate.expected_salary_max < job.salary_min:
                return False
        
        # Experience requirements
        if job.total_years_required:
            total_experience = sum(exp.years for exp in candidate.experiences)
            if total_experience < job.total_years_required:
                return False
        
        # Mandatory skills check
        for mandatory_skill in job.mandatory_skills:
            candidate_has_skill = False
            for exp in candidate.experiences:
                if exp.skill.lower() == mandatory_skill.skill.lower() and exp.years >= mandatory_skill.min_experience:
                    candidate_has_skill = True
                    break
            
            if not candidate_has_skill:
                return False
        
        return True
    
    def _check_candidate_compatibility(self, candidate: Candidate, job: Job) -> bool:
        """Check if candidate is compatible with job using structured filters"""
        # Same logic as job compatibility check
        return self._check_job_compatibility(candidate, job)
    
    def _generate_explanation(self, candidate: Candidate, job: Job, similarity_score: float) -> str:
        """Generate explanation for recommendation"""
        explanations = []
        
        # Similarity score
        explanations.append(f"Profile similarity: {similarity_score:.1%}")
        
        # Domain match
        if candidate.domain and job.domain and candidate.domain == job.domain:
            explanations.append(f"Domain match: {candidate.domain}")
        
        # Skill matches
        skill_matches = []
        for exp in candidate.experiences:
            for mandatory_skill in job.mandatory_skills:
                if exp.skill.lower() == mandatory_skill.skill.lower():
                    skill_matches.append(f"{exp.skill} ({exp.years} years, required: {mandatory_skill.min_experience})")
        
        if skill_matches:
            explanations.append(f"Skill matches: {', '.join(skill_matches)}")
        
        return ". ".join(explanations)
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get FAISS index statistics"""
        return self.faiss_manager.get_index_stats()

# Global instance
semantic_search_service = SemanticSearchService()
