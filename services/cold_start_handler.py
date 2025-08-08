import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from models.candidate import Candidate
from models.application import Application
# Interaction model not available - using placeholder
# CandidateExperience model not available - using placeholder
from models.job_skill import JobSkill
from models.skill import Skill
from models.job import Job
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

logger = logging.getLogger(__name__)

class ColdStartHandler:
    """Handles recommendations for new users and jobs with no interaction history"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.popular_jobs_cache = {}
        self.similar_users_cache = {}
        
    async def handle_new_user_recommendations(
        self, 
        db: AsyncSession, 
        candidate_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Provide recommendations for new users with no interaction history"""
        
        try:
            # Get candidate basic info
            candidate_result = await db.execute(
                select(Candidate)
                .where(Candidate.id == candidate_id)
            )
            candidate = candidate_result.scalar_one_or_none()
            
            if not candidate:
                return []
            
            recommendations = []
            
            # Method 1: Content-based recommendations based on candidate profile
            content_based = await self._get_content_based_recommendations(db, candidate, limit//2)
            recommendations.extend(content_based)
            
            # Method 2: Popular jobs in candidate's domain
            popular_jobs = await self._get_popular_jobs_by_domain(db, candidate.domain, limit//2)
            recommendations.extend(popular_jobs)
            
            # Method 3: Jobs similar to what similar users applied to
            similar_user_jobs = await self._get_similar_user_recommendations(db, candidate, limit//2)
            recommendations.extend(similar_user_jobs)
            
            # Remove duplicates and limit
            unique_recommendations = self._remove_duplicates(recommendations)
            
            logger.info(f"[INFO] Generated {len(unique_recommendations)} cold start recommendations for candidate {candidate_id}")
            return unique_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate cold start recommendations: {e}")
            return []
    
    async def handle_new_job_recommendations(
        self, 
        db: AsyncSession, 
        job_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Provide candidate recommendations for new jobs with no interaction history"""
        
        try:
            # Get job details
            job_result = await db.execute(
                select(Job)
                .where(Job.id == job_id)
            )
            job = job_result.scalar_one_or_none()
            
            if not job:
                return []
            
            recommendations = []
            
            # Method 1: Candidates with matching skills
            skill_based = await self._get_skill_based_candidates(db, job, limit//2)
            recommendations.extend(skill_based)
            
            # Method 2: Candidates in same location
            location_based = await self._get_location_based_candidates(db, job, limit//2)
            recommendations.extend(location_based)
            
            # Method 3: Candidates with similar domain experience
            domain_based = await self._get_domain_based_candidates(db, job, limit//2)
            recommendations.extend(domain_based)
            
            # Remove duplicates and limit
            unique_recommendations = self._remove_duplicates(recommendations)
            
            logger.info(f"[INFO] Generated {len(unique_recommendations)} candidate recommendations for new job {job_id}")
            return unique_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate candidate recommendations for new job: {e}")
            return []
    
    async def _get_content_based_recommendations(
        self, 
        db: AsyncSession, 
        candidate: Candidate, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get content-based recommendations based on candidate profile"""
        
        try:
            logger.info(f"[DEBUG] Getting content-based recommendations for candidate {candidate.id}")
            logger.info(f"[DEBUG] Candidate domain: {candidate.domain}")
            logger.info(f"[DEBUG] Candidate location: {candidate.location}")
            
            # First, let's check how many jobs exist in total
            total_jobs_result = await db.execute(
                select(func.count(Job.id))
            )
            total_jobs = total_jobs_result.scalar()
            logger.info(f"[DEBUG] Total jobs in database: {total_jobs}")
            
            # Check how many active jobs exist
            active_jobs_result = await db.execute(
                select(func.count(Job.id))
            )
            active_jobs = active_jobs_result.scalar()
            logger.info(f"[DEBUG] Jobs in database: {active_jobs}")
            
            # Find jobs that match candidate's domain and role
            jobs_result = await db.execute(
                select(Job)
                .where(Job.domain == candidate.domain)
                .order_by(Job.created_at.desc())
                .limit(limit * 2)  # Get more to filter
            )
            jobs = jobs_result.scalars().all()
            logger.info(f"[DEBUG] Found {len(jobs)} jobs matching domain '{candidate.domain}'")
            
            if not jobs:
                # Fallback: get any jobs
                logger.info(f"[DEBUG] No domain-specific jobs found, getting any jobs")
                jobs_result = await db.execute(
                    select(Job)
                    .order_by(Job.created_at.desc())
                    .limit(limit)
                )
                jobs = jobs_result.scalars().all()
                logger.info(f"[DEBUG] Found {len(jobs)} jobs as fallback")
            
            recommendations = []
            for job in jobs:
                # Calculate basic match score
                score = 0.0
                factors = []
                
                # Domain match
                if job.domain == candidate.domain:
                    score += 0.4
                    factors.append('domain_match')
                
                # Location match (if candidate has location)
                if candidate.location and job.location:
                    if candidate.location.lower() in job.location.lower() or job.location.lower() in candidate.location.lower():
                        score += 0.3
                        factors.append('location_match')
                
                # Role match (if candidate has role)
                if candidate.role and job.title:
                    if candidate.role.lower() in job.title.lower():
                        score += 0.3
                        factors.append('role_match')
                
                # Salary match
                if candidate.expected_salary_min and job.salary_max:
                    if candidate.expected_salary_min <= job.salary_max:
                        score += 0.2
                        factors.append('salary_match')
                
                if score > 0:
                    recommendations.append({
                        'job_id': job.id,
                        'job': self._job_to_dict(job),
                        'score': score,
                        'method': 'content_based',
                        'factors': factors,
                        'explanation': f"Based on your profile: {', '.join(factors)}"
                    })
            
            logger.info(f"[DEBUG] Generated {len(recommendations)} content-based recommendations")
            # Sort by score and return top results
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get content-based recommendations: {e}")
            return []
    
    async def _get_popular_jobs_by_domain(
        self, 
        db: AsyncSession, 
        domain: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get popular jobs in the candidate's domain"""
        
        try:
            # Get jobs with most applications in the domain
            popular_jobs_result = await db.execute(
                select(Job, func.count(Application.id).label('application_count'))
                .outerjoin(Application, Job.id == Application.job_id)
                .where(Job.domain == domain)
                .group_by(Job.id)
                .order_by(desc('application_count'))
                .limit(limit)
            )
            popular_jobs = popular_jobs_result.all()
            
            recommendations = []
            for job, app_count in popular_jobs:
                recommendations.append({
                    'job_id': job.id,
                    'job': self._job_to_dict(job),
                    'score': min(1.0, app_count / 10.0),  # Normalize score
                    'method': 'popular_jobs',
                    'factors': ['popularity'],
                    'explanation': f"Popular job in {domain} with {app_count} applications"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get popular jobs: {e}")
            return []
    
    async def _get_similar_user_recommendations(
        self, 
        db: AsyncSession, 
        candidate: Candidate, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on similar users"""
        
        try:
            # Find candidates with similar profiles (placeholder - CandidateExperience model not available)
            similar_candidates_result = await db.execute(
                select(Candidate)
                .where(
                    and_(
                        Candidate.domain == candidate.domain,
                        Candidate.id != candidate.id
                    )
                )
                .limit(10)
            )
            similar_candidates = similar_candidates_result.scalars().all()
            
            if not similar_candidates:
                return []
            
            # Get jobs that similar candidates applied to
            similar_candidate_ids = [c.id for c in similar_candidates]
            similar_jobs_result = await db.execute(
                select(Job, func.count(Application.id).label('similar_apps'))
                .join(Application, Job.id == Application.job_id)
                .where(Application.candidate_id.in_(similar_candidate_ids))
                .group_by(Job.id)
                .order_by(desc('similar_apps'))
                .limit(limit)
            )
            similar_jobs = similar_jobs_result.all()
            
            recommendations = []
            for job, similar_apps in similar_jobs:
                recommendations.append({
                    'job_id': job.id,
                    'job': self._job_to_dict(job),
                    'score': min(1.0, similar_apps / 5.0),  # Normalize score
                    'method': 'similar_users',
                    'factors': ['similar_users'],
                    'explanation': f"Applied by {similar_apps} similar users in {candidate.domain}"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get similar user recommendations: {e}")
            return []
    
    async def _get_skill_based_candidates(
        self, 
        db: AsyncSession, 
        job: Job, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get candidates with skills matching the job requirements"""
        
        try:
            # Get job skills
            job_skills_result = await db.execute(
                select(JobSkill)
                .where(JobSkill.job_id == job.id)
            )
            job_skills = job_skills_result.scalars().all()
            
            if not job_skills:
                return []
            
            skill_ids = [js.skill_id for js in job_skills]
            
            # Find candidates with matching skills (placeholder - CandidateExperience model not available)
            # For now, return candidates in the same domain
            candidates_result = await db.execute(
                select(Candidate)
                .where(Candidate.domain == job.domain)
                .limit(limit)
            )
            candidates = candidates_result.scalars().all()
            
            recommendations = []
            for candidate in candidates:
                # Calculate skill match score (placeholder)
                skill_match_score = 0.5  # Placeholder since we don't have candidate skills
                
                recommendations.append({
                    'candidate_id': candidate.id,
                    'candidate': candidate,
                    'score': skill_match_score,
                    'method': 'skill_based',
                    'factors': ['skill_match'],
                    'explanation': f"Skills match for {job.title} position"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get skill-based candidates: {e}")
            return []
    
    async def _get_location_based_candidates(
        self, 
        db: AsyncSession, 
        job: Job, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get candidates in the same location as the job"""
        
        try:
            if not job.location:
                return []
            
            # Find candidates in the same location
            candidates_result = await db.execute(
                select(Candidate)
                .where(
                    and_(
                        Candidate.location.contains(job.location),
                        Candidate.domain == job.domain
                    )
                )
                .limit(limit)
            )
            candidates = candidates_result.scalars().all()
            
            recommendations = []
            for candidate in candidates:
                recommendations.append({
                    'candidate_id': candidate.id,
                    'candidate': candidate,
                    'score': 0.7,  # Location match score
                    'method': 'location_based',
                    'factors': ['location_match'],
                    'explanation': f"Located in {job.location}"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get location-based candidates: {e}")
            return []
    
    async def _get_domain_based_candidates(
        self, 
        db: AsyncSession, 
        job: Job, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get candidates with experience in the same domain"""
        
        try:
            # Find candidates with domain experience
            candidates_result = await db.execute(
                select(Candidate)
                .where(Candidate.domain == job.domain)
                .limit(limit)
            )
            candidates = candidates_result.scalars().all()
            
            recommendations = []
            for candidate in candidates:
                recommendations.append({
                    'candidate_id': candidate.id,
                    'candidate': candidate,
                    'score': 0.6,  # Domain match score
                    'method': 'domain_based',
                    'factors': ['domain_match'],
                    'explanation': f"Experience in {job.domain}"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get domain-based candidates: {e}")
            return []
    
    def _job_to_dict(self, job: Job) -> Dict[str, Any]:
        """Convert a Job SQLAlchemy object to a dictionary"""
        return {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'domain': job.domain,
            'total_years_required': job.total_years_required,
            'job_description': job.job_description,
            'created_at': job.created_at,
            'updated_at': job.updated_at
        }
    
    def _remove_duplicates(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate recommendations based on ID"""
        
        seen_ids = set()
        unique_recommendations = []
        
        for rec in recommendations:
            rec_id = rec.get('job_id') or rec.get('candidate_id')
            if rec_id and rec_id not in seen_ids:
                seen_ids.add(rec_id)
                unique_recommendations.append(rec)
        
        return unique_recommendations

# Global instance
cold_start_handler = ColdStartHandler() 