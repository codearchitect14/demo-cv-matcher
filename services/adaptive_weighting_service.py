import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
# Interaction model not available - using placeholder
from models.application import Application
from models.job import Job
from models.candidate import Candidate
import numpy as np

logger = logging.getLogger(__name__)

class AdaptiveWeightingService:
    """Service for adaptive weighting based on user behavior and context"""
    
    def __init__(self):
        self.base_weights = {
            'semantic': 0.7,
            'filter': 0.3
        }
        self.adjustment_factors = {
            'user_engagement': 0.2,
            'job_popularity': 0.15,
            'skill_match': 0.25,
            'location_match': 0.1,
            'salary_match': 0.1,
            'domain_match': 0.2
        }
    
    async def get_adaptive_weights(
        self, 
        db: AsyncSession, 
        candidate_id: int, 
        job_id: int
    ) -> Dict[str, float]:
        """Get adaptive weights based on user behavior and job context"""
        
        try:
            # Get user behavior analysis
            user_behavior = await self._analyze_user_behavior(db, candidate_id)
            
            # Get job context analysis
            job_context = await self._analyze_job_context(db, job_id)
            
            # Get historical success rates
            success_rates = await self._get_historical_success_rates(db, candidate_id, job_id)
            
            # Calculate adaptive weights
            weights = self._calculate_adaptive_weights(
                user_behavior, job_context, success_rates
            )
            
            logger.info(f"[INFO] Calculated adaptive weights for candidate {candidate_id}, job {job_id}")
            return weights
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to calculate adaptive weights: {e}")
            return self.base_weights.copy()
    
    async def get_recommendation_weights(
        self, 
        db: AsyncSession, 
        candidate_id: int, 
        job_id: int,
        recommendation_type: str = 'job'
    ) -> Dict[str, float]:
        """Get weights for specific recommendation types"""
        
        try:
            base_weights = await self.get_adaptive_weights(db, candidate_id, job_id)
            
            if recommendation_type == 'job':
                # For job recommendations, emphasize semantic matching
                weights = {
                    'semantic': base_weights['semantic'] * 1.2,
                    'filter': base_weights['filter'] * 0.8,
                    'personalization': 0.2,
                    'context': 0.1
                }
            elif recommendation_type == 'candidate':
                # For candidate recommendations, emphasize filtering
                weights = {
                    'semantic': base_weights['semantic'] * 0.8,
                    'filter': base_weights['filter'] * 1.2,
                    'personalization': 0.15,
                    'context': 0.15
                }
            else:
                weights = base_weights.copy()
            
            # Normalize weights to sum to 1.0
            total = sum(weights.values())
            if total > 0:
                weights = {k: v / total for k, v in weights.items()}
            
            return weights
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to calculate recommendation weights: {e}")
            return self.base_weights.copy()
    
    async def _analyze_user_behavior(self, db: AsyncSession, candidate_id: int) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        
        try:
            # Get user interactions (placeholder - Interaction model not available)
            interactions = []
            
            # Get user applications
            applications_result = await db.execute(
                select(Application.job_id, Application.status, Application.created_at)
                .where(Application.candidate_id == candidate_id)
                .order_by(Application.created_at.desc())
                .limit(50)
            )
            applications = applications_result.scalars().all()
            
            # Calculate engagement metrics
            total_applications = len(applications)
            recent_applications = len([app for app in applications if app.created_at > datetime.now() - timedelta(days=30)])
            
            # Calculate success rate
            successful_apps = len([app for app in applications if app.status == 'accepted'])
            success_rate = successful_apps / total_applications if total_applications > 0 else 0
            
            # Calculate application frequency
            if applications:
                first_app = min(app.created_at for app in applications)
                last_app = max(app.created_at for app in applications)
                days_span = (last_app - first_app).days
                application_frequency = total_applications / max(days_span, 1)
            else:
                application_frequency = 0
            
            return {
                'total_applications': total_applications,
                'recent_applications': recent_applications,
                'success_rate': success_rate,
                'application_frequency': application_frequency,
                'engagement_level': 'high' if application_frequency > 0.1 else 'medium' if application_frequency > 0.05 else 'low'
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to analyze user behavior: {e}")
            return {
                'total_applications': 0,
                'recent_applications': 0,
                'success_rate': 0,
                'application_frequency': 0,
                'engagement_level': 'low'
            }
    
    async def _analyze_job_context(self, db: AsyncSession, job_id: int) -> Dict[str, Any]:
        """Analyze job context and popularity"""
        
        try:
            # Get job details
            job_result = await db.execute(
                select(Job)
                .where(Job.id == job_id)
            )
            job = job_result.scalar_one_or_none()
            
            if not job:
                return {}
            
            # Get applications for this job
            applications_result = await db.execute(
                select(func.count(Application.id))
                .where(Application.job_id == job_id)
            )
            application_count = applications_result.scalar()
            
            # Get interactions with this job (placeholder - Interaction model not available)
            interaction_count = 0
            
            # Calculate popularity score
            popularity_score = min(1.0, application_count / 10.0)
            
            # Calculate urgency score (newer jobs get higher score)
            days_since_posted = (datetime.now() - job.created_at).days
            urgency_score = max(0.1, 1.0 - (days_since_posted / 30.0))
            
            context = {
                'application_count': application_count,
                'interaction_count': interaction_count,
                'popularity_score': popularity_score,
                'urgency_score': urgency_score,
                'domain': job.domain,
                'location': job.location,
                'salary_range': (job.salary_min, job.salary_max) if job.salary_min and job.salary_max else None
            }
            
            return context
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to analyze job context: {e}")
            return {}
    
    async def _get_historical_success_rates(
        self, 
        db: AsyncSession, 
        candidate_id: int, 
        job_id: int
    ) -> Dict[str, float]:
        """Get historical success rates for similar scenarios"""
        
        try:
            # Get candidate's historical success rate
            candidate_apps_result = await db.execute(
                select(func.count(Application.id))
                .where(Application.candidate_id == candidate_id)
            )
            total_candidate_apps = candidate_apps_result.scalar()
            
            candidate_success_result = await db.execute(
                select(func.count(Application.id))
                .where(
                    and_(
                        Application.candidate_id == candidate_id,
                        Application.status == 'accepted'
                    )
                )
            )
            candidate_success_apps = candidate_success_result.scalar()
            
            candidate_success_rate = candidate_success_apps / total_candidate_apps if total_candidate_apps > 0 else 0
            
            # Get job's historical success rate
            job_apps_result = await db.execute(
                select(func.count(Application.id))
                .where(Application.job_id == job_id)
            )
            total_job_apps = job_apps_result.scalar()
            
            job_success_result = await db.execute(
                select(func.count(Application.id))
                .where(
                    and_(
                        Application.job_id == job_id,
                        Application.status == 'accepted'
                    )
                )
            )
            job_success_apps = job_success_result.scalar()
            
            job_success_rate = job_success_apps / total_job_apps if total_job_apps > 0 else 0
            
            return {
                'candidate_success_rate': candidate_success_rate,
                'job_success_rate': job_success_rate,
                'overall_success_rate': (candidate_success_rate + job_success_rate) / 2
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get historical success rates: {e}")
            return {
                'candidate_success_rate': 0.1,
                'job_success_rate': 0.1,
                'overall_success_rate': 0.1
            }
    
    def _calculate_adaptive_weights(
        self, 
        user_behavior: Dict[str, Any], 
        job_context: Dict[str, Any], 
        success_rates: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate adaptive weights based on analysis"""
        
        # Start with base weights
        weights = self.base_weights.copy()
        
        # Adjust based on user engagement
        engagement_level = user_behavior.get('engagement_level', 'low')
        if engagement_level == 'high':
            weights['semantic'] *= 1.2
            weights['filter'] *= 0.8
        elif engagement_level == 'low':
            weights['semantic'] *= 0.8
            weights['filter'] *= 1.2
        
        # Adjust based on job popularity
        popularity_score = job_context.get('popularity_score', 0.5)
        if popularity_score > 0.7:
            weights['semantic'] *= 0.9
            weights['filter'] *= 1.1
        elif popularity_score < 0.3:
            weights['semantic'] *= 1.1
            weights['filter'] *= 0.9
        
        # Adjust based on success rates
        overall_success_rate = success_rates.get('overall_success_rate', 0.1)
        if overall_success_rate > 0.5:
            weights['semantic'] *= 1.1
            weights['filter'] *= 0.9
        elif overall_success_rate < 0.2:
            weights['semantic'] *= 0.9
            weights['filter'] *= 1.1
        
        # Normalize weights to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights

# Global instance
adaptive_weighting_service = AdaptiveWeightingService() 