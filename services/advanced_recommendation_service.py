import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import asyncio

from models.candidate import Candidate, CandidateExperience
from models.job import Job, JobMandatorySkill
from models.recruiter import Recruiter
from models.application import Application
from models.interaction import InteractionLog, InteractionTypeEnum
from services.cv_parser_service import CVData, cv_parser_service
from embeddings.embedder import embedding_service
from embeddings.build_index import index_manager
from services.personalization_service import personalization_service

logger = logging.getLogger(__name__)

@dataclass
class MatchScore:
    """Detailed match score breakdown"""
    total_score: float
    skill_match: float
    experience_match: float
    location_match: float
    education_match: float
    soft_skills_match: float
    culture_match: float
    recent_activity_bonus: float
    explanation: str

@dataclass
class RecommendationResult:
    """Structured recommendation result"""
    id: int
    title: str
    company: str
    location: str
    match_score: MatchScore
    highlights: List[str]
    concerns: List[str]
    action_items: List[str]

class AdvancedRecommendationService:
    """Advanced recommendation service for both candidates and recruiters"""
    
    def __init__(self):
        """Initialize the recommendation service"""
        self.weights = {
            'skill_match': 0.35,
            'experience_match': 0.20,
            'location_match': 0.15,
            'education_match': 0.10,
            'soft_skills_match': 0.10,
            'culture_match': 0.05,
            'recent_activity': 0.05
        }
        
        # Skill similarity thresholds
        self.skill_thresholds = {
            'exact_match': 1.0,
            'close_match': 0.8,
            'partial_match': 0.6,
            'weak_match': 0.3
        }
    
    async def get_candidate_recommendations(
        self, 
        candidate_id: int, 
        db: AsyncSession,
        limit: int = 10,
        include_explanation: bool = True
    ) -> List[RecommendationResult]:
        """Get personalized job recommendations for a candidate"""
        try:
            # Get candidate with full profile
            candidate = await self._get_candidate_with_profile(candidate_id, db)
            if not candidate:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            # Get all active jobs
            jobs = await self._get_active_jobs(db)
            
            # Calculate match scores for each job
            recommendations = []
            for job in jobs:
                match_score = await self._calculate_candidate_job_match(candidate, job, db)
                
                if match_score.total_score > 0.3:  # Only include relevant matches
                    recommendation = await self._create_job_recommendation(job, match_score, include_explanation)
                    recommendations.append(recommendation)
            
            # Sort by match score and return top results
            recommendations.sort(key=lambda x: x.match_score.total_score, reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting candidate recommendations: {e}")
            raise
    
    async def get_recruiter_recommendations(
        self, 
        job_id: int, 
        db: AsyncSession,
        limit: int = 10,
        include_explanation: bool = True
    ) -> List[RecommendationResult]:
        """Get personalized candidate recommendations for a job"""
        try:
            # Get job with full details
            job = await self._get_job_with_details(job_id, db)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Get all active candidates
            candidates = await self._get_active_candidates(db)
            
            # Calculate match scores for each candidate
            recommendations = []
            for candidate in candidates:
                match_score = await self._calculate_job_candidate_match(job, candidate, db)
                
                if match_score.total_score > 0.3:  # Only include relevant matches
                    recommendation = await self._create_candidate_recommendation(candidate, match_score, include_explanation)
                    recommendations.append(recommendation)
            
            # Sort by match score and return top results
            recommendations.sort(key=lambda x: x.match_score.total_score, reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recruiter recommendations: {e}")
            raise
    
    async def _get_candidate_with_profile(self, candidate_id: int, db: AsyncSession) -> Optional[Candidate]:
        """Get candidate with full profile including experiences"""
        result = await db.execute(
            select(Candidate)
            .options(selectinload(Candidate.experiences))
            .where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_job_with_details(self, job_id: int, db: AsyncSession) -> Optional[Job]:
        """Get job with full details including mandatory skills"""
        result = await db.execute(
            select(Job)
            .options(selectinload(Job.mandatory_skills))
            .where(Job.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_active_jobs(self, db: AsyncSession) -> List[Job]:
        """Get all active jobs"""
        result = await db.execute(
            select(Job)
            .options(selectinload(Job.mandatory_skills))
            .where(Job.is_active == True)
        )
        return result.scalars().all()
    
    async def _get_active_candidates(self, db: AsyncSession) -> List[Candidate]:
        """Get all active candidates"""
        result = await db.execute(
            select(Candidate)
            .options(selectinload(Candidate.experiences))
            .where(Candidate.is_active == True)
        )
        return result.scalars().all()
    
    async def _calculate_candidate_job_match(
        self, 
        candidate: Candidate, 
        job: Job, 
        db: AsyncSession
    ) -> MatchScore:
        """Calculate detailed match score between candidate and job"""
        
        # Extract candidate skills
        candidate_skills = [exp.skill for exp in candidate.experiences]
        candidate_skill_years = {exp.skill: exp.years for exp in candidate.experiences}
        
        # Extract job requirements
        job_skills = [skill.skill for skill in job.mandatory_skills]
        job_skill_requirements = {skill.skill: skill.min_experience for skill in job.mandatory_skills}
        
        # Calculate skill match
        skill_match = self._calculate_skill_match(candidate_skills, job_skills, candidate_skill_years, job_skill_requirements)
        
        # Calculate experience match
        experience_match = self._calculate_experience_match(candidate, job)
        
        # Calculate location match
        location_match = self._calculate_location_match(candidate.location, job.location)
        
        # Calculate education match
        education_match = self._calculate_education_match(candidate, job)
        
        # Calculate soft skills match
        soft_skills_match = self._calculate_soft_skills_match(candidate, job)
        
        # Calculate culture match
        culture_match = self._calculate_culture_match(candidate, job)
        
        # Calculate recent activity bonus
        recent_activity = await self._calculate_recent_activity_bonus(candidate.id, db)
        
        # Calculate total score
        total_score = (
            skill_match * self.weights['skill_match'] +
            experience_match * self.weights['experience_match'] +
            location_match * self.weights['location_match'] +
            education_match * self.weights['education_match'] +
            soft_skills_match * self.weights['soft_skills_match'] +
            culture_match * self.weights['culture_match'] +
            recent_activity * self.weights['recent_activity']
        )
        
        # Generate explanation
        explanation = self._generate_match_explanation(
            skill_match, experience_match, location_match, 
            education_match, soft_skills_match, culture_match, recent_activity
        )
        
        return MatchScore(
            total_score=total_score,
            skill_match=skill_match,
            experience_match=experience_match,
            location_match=location_match,
            education_match=education_match,
            soft_skills_match=soft_skills_match,
            culture_match=culture_match,
            recent_activity_bonus=recent_activity,
            explanation=explanation
        )
    
    async def _calculate_job_candidate_match(
        self, 
        job: Job, 
        candidate: Candidate, 
        db: AsyncSession
    ) -> MatchScore:
        """Calculate detailed match score between job and candidate"""
        # This is similar to candidate-job match but from job perspective
        return await self._calculate_candidate_job_match(candidate, job, db)
    
    def _calculate_skill_match(
        self, 
        candidate_skills: List[str], 
        job_skills: List[str],
        candidate_skill_years: Dict[str, float],
        job_skill_requirements: Dict[str, float]
    ) -> float:
        """Calculate skill match score"""
        if not job_skills:
            return 0.0
        
        matched_skills = 0
        total_skill_score = 0
        
        for job_skill in job_skills:
            best_match_score = 0
            
            for candidate_skill in candidate_skills:
                # Calculate skill similarity
                similarity = self._calculate_skill_similarity(job_skill, candidate_skill)
                
                if similarity > best_match_score:
                    best_match_score = similarity
                    
                    # Check experience requirements
                    if job_skill in job_skill_requirements and candidate_skill in candidate_skill_years:
                        required_years = job_skill_requirements[job_skill]
                        actual_years = candidate_skill_years[candidate_skill]
                        
                        if actual_years >= required_years:
                            best_match_score *= 1.2  # Bonus for meeting experience requirement
                        elif actual_years >= required_years * 0.8:
                            best_match_score *= 0.9  # Slight penalty for being close
                        else:
                            best_match_score *= 0.6  # Significant penalty for insufficient experience
            
            total_skill_score += best_match_score
            if best_match_score > self.skill_thresholds['partial_match']:
                matched_skills += 1
        
        # Calculate final skill match score
        skill_coverage = matched_skills / len(job_skills)
        skill_quality = total_skill_score / len(job_skills)
        
        return (skill_coverage * 0.6) + (skill_quality * 0.4)
    
    def _calculate_skill_similarity(self, skill1: str, skill2: str) -> float:
        """Calculate similarity between two skills"""
        skill1_lower = skill1.lower()
        skill2_lower = skill2.lower()
        
        # Exact match
        if skill1_lower == skill2_lower:
            return 1.0
        
        # Partial match (one skill contains the other)
        if skill1_lower in skill2_lower or skill2_lower in skill1_lower:
            return 0.8
        
        # Synonym matching (could be expanded with a thesaurus)
        synonyms = {
            'python': ['py', 'python3'],
            'javascript': ['js', 'ecmascript'],
            'react': ['reactjs', 'react.js'],
            'node': ['nodejs', 'node.js'],
            'aws': ['amazon web services', 'amazon'],
            'azure': ['microsoft azure', 'ms azure'],
            'gcp': ['google cloud', 'google cloud platform']
        }
        
        for skill_group, syn_list in synonyms.items():
            if skill1_lower in syn_list and skill2_lower == skill_group:
                return 0.9
            if skill2_lower in syn_list and skill1_lower == skill_group:
                return 0.9
        
        return 0.0
    
    def _calculate_experience_match(self, candidate: Candidate, job: Job) -> float:
        """Calculate experience match score"""
        if not job.total_years_required:
            return 0.5  # Neutral score if no requirement specified
        
        candidate_years = candidate.total_years_experience or 0
        
        if candidate_years >= job.total_years_required:
            return 1.0
        elif candidate_years >= job.total_years_required * 0.8:
            return 0.8
        elif candidate_years >= job.total_years_required * 0.6:
            return 0.6
        else:
            return 0.3
    
    def _calculate_location_match(self, candidate_location: str, job_location: str) -> float:
        """Calculate location match score"""
        if not candidate_location or not job_location:
            return 0.5  # Neutral score if location not specified
        
        candidate_loc_lower = candidate_location.lower()
        job_loc_lower = job_location.lower()
        
        # Exact match
        if candidate_loc_lower == job_loc_lower:
            return 1.0
        
        # Same city
        if candidate_loc_lower.split(',')[0] == job_loc_lower.split(',')[0]:
            return 0.9
        
        # Same country
        if candidate_loc_lower.split(',')[-1].strip() == job_loc_lower.split(',')[-1].strip():
            return 0.7
        
        # Remote work consideration
        if 'remote' in job_loc_lower or 'remote' in candidate_loc_lower:
            return 0.8
        
        return 0.3
    
    def _calculate_education_match(self, candidate: Candidate, job: Job) -> float:
        """Calculate education match score"""
        # This is a simplified version - could be enhanced with education requirements
        return 0.7  # Default neutral score
    
    def _calculate_soft_skills_match(self, candidate: Candidate, job: Job) -> float:
        """Calculate soft skills match score"""
        # This would require job soft skills requirements and candidate soft skills
        # For now, return a neutral score
        return 0.6
    
    def _calculate_culture_match(self, candidate: Candidate, job: Job) -> float:
        """Calculate culture match score"""
        # This would require company culture data and candidate preferences
        # For now, return a neutral score
        return 0.5
    
    async def _calculate_recent_activity_bonus(self, candidate_id: int, db: AsyncSession) -> float:
        """Calculate recent activity bonus"""
        # Check recent interactions
        result = await db.execute(
            select(InteractionLog)
            .where(InteractionLog.user_id == candidate_id)
            .where(InteractionLog.user_type == "candidate")
            .order_by(InteractionLog.timestamp.desc())
            .limit(10)
        )
        
        recent_interactions = result.scalars().all()
        
        if not recent_interactions:
            return 0.0
        
        # Calculate activity score based on recent interactions
        activity_score = min(1.0, len(recent_interactions) * 0.1)
        return activity_score
    
    def _generate_match_explanation(
        self, 
        skill_match: float, 
        experience_match: float, 
        location_match: float,
        education_match: float, 
        soft_skills_match: float, 
        culture_match: float, 
        recent_activity: float
    ) -> str:
        """Generate human-readable match explanation"""
        explanations = []
        
        if skill_match > 0.8:
            explanations.append("Excellent skill match")
        elif skill_match > 0.6:
            explanations.append("Good skill match")
        elif skill_match > 0.4:
            explanations.append("Partial skill match")
        else:
            explanations.append("Limited skill match")
        
        if experience_match > 0.8:
            explanations.append("Experience requirements met")
        elif experience_match > 0.6:
            explanations.append("Close to experience requirements")
        else:
            explanations.append("Below experience requirements")
        
        if location_match > 0.8:
            explanations.append("Location match")
        elif location_match > 0.6:
            explanations.append("Nearby location")
        else:
            explanations.append("Location mismatch")
        
        if recent_activity > 0.5:
            explanations.append("Recently active")
        
        return ". ".join(explanations) + "."
    
    async def _create_job_recommendation(
        self, 
        job: Job, 
        match_score: MatchScore, 
        include_explanation: bool
    ) -> RecommendationResult:
        """Create job recommendation result"""
        highlights = []
        concerns = []
        action_items = []
        
        # Generate highlights
        if match_score.skill_match > 0.7:
            highlights.append("Strong skill alignment")
        if match_score.experience_match > 0.8:
            highlights.append("Experience requirements met")
        if match_score.location_match > 0.8:
            highlights.append("Location match")
        
        # Generate concerns
        if match_score.skill_match < 0.5:
            concerns.append("Limited skill overlap")
        if match_score.experience_match < 0.6:
            concerns.append("Below experience requirements")
        if match_score.location_match < 0.5:
            concerns.append("Location mismatch")
        
        # Generate action items
        if match_score.skill_match < 0.6:
            action_items.append("Consider upskilling in required areas")
        if match_score.experience_match < 0.7:
            action_items.append("Gain more experience in relevant areas")
        
        return RecommendationResult(
            id=job.id,
            title=job.title,
            company=job.company or "Unknown",
            location=job.location,
            match_score=match_score,
            highlights=highlights,
            concerns=concerns,
            action_items=action_items
        )
    
    async def _create_candidate_recommendation(
        self, 
        candidate: Candidate, 
        match_score: MatchScore, 
        include_explanation: bool
    ) -> RecommendationResult:
        """Create candidate recommendation result"""
        highlights = []
        concerns = []
        action_items = []
        
        # Generate highlights
        if match_score.skill_match > 0.7:
            highlights.append("Strong technical skills")
        if match_score.experience_match > 0.8:
            highlights.append("Adequate experience level")
        if match_score.location_match > 0.8:
            highlights.append("Location suitable")
        
        # Generate concerns
        if match_score.skill_match < 0.5:
            concerns.append("Limited required skills")
        if match_score.experience_match < 0.6:
            concerns.append("Below experience requirements")
        
        # Generate action items
        if match_score.skill_match < 0.6:
            action_items.append("Consider additional training")
        if match_score.experience_match < 0.7:
            action_items.append("Look for more experienced candidates")
        
        return RecommendationResult(
            id=candidate.id,
            title=candidate.name,
            company=candidate.location,  # Using location as company for candidates
            location=candidate.location,
            match_score=match_score,
            highlights=highlights,
            concerns=concerns,
            action_items=action_items
        )
    
    async def process_cv_and_get_recommendations(
        self, 
        cv_file_path: str, 
        db: AsyncSession,
        limit: int = 10
    ) -> Tuple[CVData, List[RecommendationResult]]:
        """Process CV and get immediate recommendations"""
        try:
            # Parse CV
            cv_data = await cv_parser_service.parse_cv(cv_file_path)
            
            # Get active jobs
            jobs = await self._get_active_jobs(db)
            
            # Calculate matches
            recommendations = []
            for job in jobs:
                # Create temporary candidate object from CV data
                temp_candidate = self._create_temp_candidate_from_cv(cv_data)
                
                match_score = await self._calculate_candidate_job_match(temp_candidate, job, db)
                
                if match_score.total_score > 0.3:
                    recommendation = await self._create_job_recommendation(job, match_score, True)
                    recommendations.append(recommendation)
            
            # Sort by match score
            recommendations.sort(key=lambda x: x.match_score.total_score, reverse=True)
            
            return cv_data, recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error processing CV and getting recommendations: {e}")
            raise
    
    def _create_temp_candidate_from_cv(self, cv_data: CVData) -> Candidate:
        """Create temporary candidate object from CV data"""
        # Create a temporary candidate object for matching
        temp_candidate = Candidate()
        temp_candidate.total_years_experience = cv_data.total_years_experience
        temp_candidate.location = cv_data.location or "Unknown"
        
        # Add experiences from CV data
        temp_candidate.experiences = []
        for skill in cv_data.skills:
            if skill.years_experience:
                exp = CandidateExperience()
                exp.skill = skill.skill
                exp.years = skill.years_experience
                temp_candidate.experiences.append(exp)
        
        return temp_candidate

# Create global instance
advanced_recommendation_service = AdvancedRecommendationService() 