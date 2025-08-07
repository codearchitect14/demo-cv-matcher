import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
# Interaction model not available - using placeholder
from models.application import Application
from models.job import Job
from models.candidate import Candidate
from models.candidate_skill import CandidateSkill
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

logger = logging.getLogger(__name__)

class PersonalizationEngine:
    """Personalization engine for user profiling and preference learning"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.user_profiles = {}  # Cache for user profiles
        self.preference_models = {}  # Cache for preference models
        
    async def get_user_profile(
        self, 
        db: AsyncSession, 
        candidate_id: int,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get comprehensive user profile with preferences"""
        
        cache_key = f"profile_{candidate_id}"
        if not force_refresh and cache_key in self.user_profiles:
            return self.user_profiles[cache_key]
        
        try:
            # Get candidate with skills
            candidate_result = await db.execute(
                select(Candidate)
                .where(Candidate.id == candidate_id)
            )
            candidate = candidate_result.scalar_one_or_none()
            
            if not candidate:
                return {}
            
            # Get user interactions (placeholder - Interaction model not available)
            interactions = []
            
            # Get user applications
            applications_result = await db.execute(
                select(Application.job_id, Application.status, Application.created_at)
                .where(Application.candidate_id == candidate_id)
                .order_by(Application.created_at.desc())
                .limit(100)
            )
            applications = applications_result.scalars().all()
            
            # Get candidate skills
            skills_result = await db.execute(
                select(CandidateSkill)
                .where(CandidateSkill.candidate_id == candidate_id)
            )
            candidate_skills = skills_result.scalars().all()
            
            # Build comprehensive profile
            profile = await self._build_user_profile(
                candidate, interactions, applications, candidate_skills, db
            )
            
            # Cache the profile
            self.user_profiles[cache_key] = profile
            
            logger.info(f"[INFO] Built user profile for candidate {candidate_id}")
            return profile
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to build user profile: {e}")
            return {}
    
    async def _build_user_profile(
        self, 
        candidate: Candidate, 
        interactions: List, 
        applications: List[Application],
        candidate_skills: List[CandidateSkill],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Build comprehensive user profile"""
        
        profile = {
            'basic_info': {
                'id': candidate.id,
                'name': candidate.name,
                'email': candidate.email,
                'location': candidate.location,
                'domain': candidate.domain,
                'role': candidate.role
            },
            'skills': await self._analyze_skills(candidate_skills),
            'preferences': await self._analyze_preferences(interactions, applications, db),
            'behavior': await self._analyze_behavior(interactions, applications),
            'engagement': await self._analyze_engagement(interactions, applications),
            'success_patterns': await self._analyze_success_patterns(applications, db),
            'recommendation_preferences': await self._analyze_recommendation_preferences(interactions, applications)
        }
        
        return profile
    
    async def _analyze_skills(self, candidate_skills: List[CandidateSkill]) -> Dict[str, Any]:
        """Analyze user skills and expertise"""
        
        if not candidate_skills:
            return {
                'primary_skills': [],
                'skill_levels': {},
                'expertise_areas': [],
                'total_skills': 0
            }
        
        # Group skills by name and calculate experience
        skill_years = {}
        for skill in candidate_skills:
            skill_name = skill.skill.lower()
            if skill_name not in skill_years:
                skill_years[skill_name] = []
            skill_years[skill_name].append(skill.years)
        
        # Calculate average experience per skill
        skill_levels = {}
        for skill, years_list in skill_years.items():
            skill_levels[skill] = {
                'avg_years': np.mean(years_list),
                'max_years': max(years_list),
                'total_years': sum(years_list)
            }
        
        # Identify primary skills (top 5 by total years)
        primary_skills = sorted(
            skill_levels.items(), 
            key=lambda x: x[1]['total_years'], 
            reverse=True
        )[:5]
        
        # Identify expertise areas (skills with 3+ years average)
        expertise_areas = [
            skill for skill, level in skill_levels.items() 
            if level['avg_years'] >= 3
        ]
        
        return {
            'primary_skills': [skill for skill, _ in primary_skills],
            'skill_levels': skill_levels,
            'expertise_areas': expertise_areas,
            'total_skills': len(skill_levels)
        }
    
    async def _analyze_preferences(
        self, 
        interactions: List, 
        applications: List[Application],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze user preferences from interactions and applications"""
        
        preferences = {
            'preferred_domains': [],
            'preferred_locations': [],
            'preferred_salary_range': {'min': 0, 'max': 0},
            'preferred_job_types': [],
            'preferred_companies': [],
            'preferred_skills': []
        }
        
        # Analyze from applications
        if applications:
            # Get job details for applications
            job_ids = [app.job_id for app in applications]
            jobs_result = await db.execute(
                select(Job)
                .where(Job.id.in_(job_ids))
            )
            jobs = jobs_result.scalars().all()
            
            # Extract preferences from applied jobs
            domains = [job.domain for job in jobs if job.domain]
            locations = [job.location for job in jobs if job.location]
            salaries = [job.salary_min for job in jobs if job.salary_min]
            companies = [job.company for job in jobs if job.company]
            
            if domains:
                preferences['preferred_domains'] = list(set(domains))
            if locations:
                preferences['preferred_locations'] = list(set(locations))
            if salaries:
                preferences['preferred_salary_range'] = {
                    'min': min(salaries),
                    'max': max(salaries)
                }
            if companies:
                preferences['preferred_companies'] = list(set(companies))
        
        return preferences
    
    async def _analyze_behavior(
        self, 
        interactions: List, 
        applications: List[Application]
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        
        behavior = {
            'total_interactions': len(interactions),
            'total_applications': len(applications),
            'interaction_rate': 0,
            'application_rate': 0,
            'avg_interaction_duration': 0,
            'preferred_interaction_times': [],
            'browsing_patterns': [],
            'decision_making_time': 0
        }
        
        if applications:
            # Calculate application rate
            if len(applications) > 1:
                first_app = min(app.created_at for app in applications)
                last_app = max(app.created_at for app in applications)
                days_span = (last_app - first_app).days
                if days_span > 0:
                    behavior['application_rate'] = len(applications) / days_span
        
        return behavior
    
    async def _analyze_engagement(
        self, 
        interactions: List, 
        applications: List[Application]
    ) -> Dict[str, Any]:
        """Analyze user engagement levels"""
        
        engagement = {
            'engagement_level': 'low',
            'activity_score': 0,
            'consistency_score': 0,
            'depth_score': 0
        }
        
        # Calculate activity score
        total_actions = len(interactions) + len(applications)
        if total_actions > 50:
            engagement['activity_score'] = 1.0
        elif total_actions > 20:
            engagement['activity_score'] = 0.7
        elif total_actions > 10:
            engagement['activity_score'] = 0.4
        else:
            engagement['activity_score'] = 0.1
        
        # Determine overall engagement level
        overall_score = engagement['activity_score']
        
        if overall_score > 0.7:
            engagement['engagement_level'] = 'high'
        elif overall_score > 0.4:
            engagement['engagement_level'] = 'medium'
        else:
            engagement['engagement_level'] = 'low'
        
        return engagement
    
    async def _analyze_success_patterns(
        self, 
        applications: List[Application], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze patterns in successful applications"""
        
        success_patterns = {
            'success_rate': 0,
            'successful_job_types': [],
            'successful_companies': [],
            'successful_locations': [],
            'successful_salary_ranges': [],
            'application_timing': {}
        }
        
        if not applications:
            return success_patterns
        
        # Calculate success rate
        successful_apps = [app for app in applications if app.status == 'accepted']
        success_patterns['success_rate'] = len(successful_apps) / len(applications)
        
        # Analyze successful applications
        if successful_apps:
            # Get job details for successful applications
            job_ids = [app.job_id for app in successful_apps]
            jobs_result = await db.execute(
                select(Job)
                .where(Job.id.in_(job_ids))
            )
            jobs = jobs_result.scalars().all()
            
            # Extract patterns from successful jobs
            domains = [job.domain for job in jobs if job.domain]
            companies = [job.company for job in jobs if job.company]
            locations = [job.location for job in jobs if job.location]
            salaries = [(job.salary_min, job.salary_max) for job in jobs if job.salary_min and job.salary_max]
            
            success_patterns['successful_job_types'] = list(set(domains))
            success_patterns['successful_companies'] = list(set(companies))
            success_patterns['successful_locations'] = list(set(locations))
            success_patterns['successful_salary_ranges'] = list(set(salaries))
        
        return success_patterns
    
    async def _analyze_recommendation_preferences(
        self, 
        interactions: List, 
        applications: List[Application]
    ) -> Dict[str, Any]:
        """Analyze user preferences for recommendation types"""
        
        preferences = {
            'prefers_semantic': 0.5,
            'prefers_filtered': 0.5,
            'prefers_popular': 0.5,
            'prefers_niche': 0.5,
            'prefers_recent': 0.5,
            'prefers_established': 0.5
        }
        
        return preferences
    
    async def get_personalized_recommendations(
        self, 
        db: AsyncSession, 
        candidate_id: int, 
        job_recommendations: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get personalized job recommendations based on user profile"""
        
        try:
            # Get user profile
            profile = await self.get_user_profile(db, candidate_id)
            if not profile:
                return job_recommendations[:limit]
            
            # Apply personalization scoring
            personalized_recommendations = []
            
            for job_rec in job_recommendations:
                job = job_rec.get('job')
                if not job:
                    continue
                
                # Calculate personalization score
                personalization_score = self._calculate_personalization_score(profile, job)
                
                # Add personalization score to recommendation
                job_rec['personalization_score'] = personalization_score
                job_rec['personalization_factors'] = self._get_personalization_factors(profile, job)
                
                personalized_recommendations.append(job_rec)
            
            # Sort by combined score (original + personalization)
            for rec in personalized_recommendations:
                original_score = rec.get('combined_score', 0)
                personalization_score = rec.get('personalization_score', 0)
                rec['final_score'] = (original_score * 0.7) + (personalization_score * 0.3)
            
            # Sort by final score
            personalized_recommendations.sort(key=lambda x: x['final_score'], reverse=True)
            
            return personalized_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to personalize recommendations: {e}")
            return job_recommendations[:limit]
    
    def _calculate_personalization_score(self, profile: Dict[str, Any], job: Job) -> float:
        """Calculate personalization score for a job"""
        
        score = 0.0
        factors = []
        
        # Location preference
        if profile.get('preferences', {}).get('preferred_locations'):
            if job.location in profile['preferences']['preferred_locations']:
                score += 0.2
                factors.append('location_match')
        
        # Domain preference
        if profile.get('preferences', {}).get('preferred_domains'):
            if job.domain in profile['preferences']['preferred_domains']:
                score += 0.2
                factors.append('domain_match')
        
        # Salary preference
        if profile.get('preferences', {}).get('preferred_salary_range'):
            pref_range = profile['preferences']['preferred_salary_range']
            if (pref_range['min'] <= job.salary_max and 
                pref_range['max'] >= job.salary_min):
                score += 0.15
                factors.append('salary_match')
        
        # Company preference
        if profile.get('preferences', {}).get('preferred_companies'):
            if job.company in profile['preferences']['preferred_companies']:
                score += 0.15
                factors.append('company_match')
        
        # Skill match
        if profile.get('skills', {}).get('expertise_areas'):
            job_skills = [skill.skill.lower() for skill in job.mandatory_skills] if hasattr(job, 'mandatory_skills') and job.mandatory_skills else []
            expertise_areas = profile['skills']['expertise_areas']
            
            skill_matches = len(set(job_skills).intersection(set(expertise_areas)))
            if skill_matches > 0:
                score += min(0.3, skill_matches * 0.1)
                factors.append(f'skill_match_{skill_matches}')
        
        return min(1.0, score)
    
    def _get_personalization_factors(self, profile: Dict[str, Any], job: Job) -> List[str]:
        """Get list of personalization factors that apply to this job"""
        
        factors = []
        
        # Check various preference matches
        if profile.get('preferences', {}).get('preferred_locations'):
            if job.location in profile['preferences']['preferred_locations']:
                factors.append('location_preference')
        
        if profile.get('preferences', {}).get('preferred_domains'):
            if job.domain in profile['preferences']['preferred_domains']:
                factors.append('domain_preference')
        
        if profile.get('skills', {}).get('expertise_areas'):
            job_skills = [skill.skill.lower() for skill in job.mandatory_skills] if hasattr(job, 'mandatory_skills') and job.mandatory_skills else []
            expertise_areas = profile['skills']['expertise_areas']
            
            if set(job_skills).intersection(set(expertise_areas)):
                factors.append('skill_expertise')
        
        return factors

# Global instance
personalization_engine = PersonalizationEngine() 