import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta

from db.crud import candidate, job, skill, job_skill, candidate_skill
from services.enhanced_cv_parser import EnhancedCVParser, EnhancedCVData
from services.skill_matcher import skill_matcher
from models.candidate import Candidate
from models.job import Job
from models.skill import Skill
from models.job_skill import JobSkill
from models.candidate_skill import CandidateSkill

import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class SkillMatchResult:
    """Result of skill matching between job and candidate"""
    skill_name: str
    required_years: float
    candidate_years: float
    match_score: float
    proficiency_level: str
    last_used: Optional[datetime]
    meets_requirement: bool

@dataclass
class EnhancedRecommendationResult:
    """Enhanced recommendation result with skill-specific details"""
    candidate_id: int
    candidate_name: str
    job_id: int
    overall_match_score: float
    skill_matches: List[SkillMatchResult]
    missing_skills: List[str]
    experience_gaps: List[str]
    strengths: List[str]
    explanation: str

class EnhancedRecommendationService:
    """Enhanced recommendation service with skill-specific experience matching"""
    
    def __init__(self):
        """Initialize the enhanced recommendation service"""
        self.cv_parser = EnhancedCVParser()
        self.skill_matcher = skill_matcher
        logger.info("[SUCCESS] Enhanced recommendation service initialized")
    
    async def get_candidate_job_recommendations(
        self, 
        db: AsyncSession, 
        candidate_id: int, 
        limit: int = 10,
        include_explanation: bool = True
    ) -> List[EnhancedRecommendationResult]:
        """Get job recommendations for a candidate based on skill-specific experience"""
        try:
            # Get candidate with skills
            candidate_data = await candidate.get_with_skills(db, candidate_id)
            if not candidate_data:
                logger.warning(f"⚠️ Candidate {candidate_id} not found")
                return []
            
            # Get all active jobs with skill requirements (fallback to simple getter)
            try:
                jobs = await job.get_active_jobs_with_skills(db, limit=100)  # type: ignore[attr-defined]
            except Exception:
                jobs = await job.get_multi_with_filters(db, filters=None, skip=0, limit=100)
            
            recommendations = []
            for job_data in jobs:
                # Calculate skill-specific match
                match_result = await self._calculate_job_candidate_match(
                    db, candidate_data, job_data
                )
                
                if match_result.overall_match_score > 0.1:  # Minimum threshold
                    recommendations.append(match_result)
            
            # Sort by match score
            recommendations.sort(key=lambda x: x.overall_match_score, reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"[ERROR] Error getting candidate recommendations: {e}")
            return []
    
    async def get_recruiter_candidate_recommendations(
        self, 
        db: AsyncSession, 
        job_id: int, 
        limit: int = 10,
        include_explanation: bool = True
    ) -> List[EnhancedRecommendationResult]:
        """Get candidate recommendations for a job based on skill-specific requirements"""
        try:
            # Get job with skill requirements
            job_data = await job.get_with_skills(db, job_id)
            if not job_data:
                logger.warning(f"⚠️ Job {job_id} not found")
                return []
            
            # Get all active candidates with skills
            candidates = await candidate.get_active_candidates_with_skills(db, limit=100)
            
            recommendations = []
            for cand in candidates:
                # Calculate skill-specific match (no DB I/O inside loop)
                match_result = await self._calculate_job_candidate_match(
                    db, cand, job_data
                )
                if match_result.overall_match_score > 0.1:
                    recommendations.append(match_result)
            
            # Sort by match score
            recommendations.sort(key=lambda x: x.overall_match_score, reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"[ERROR] Error getting recruiter recommendations: {e}")
            return []
    
    async def _calculate_job_candidate_match(
        self, 
        db: AsyncSession, 
        candidate_data: Dict, 
        job_data: Dict
    ) -> EnhancedRecommendationResult:
        """Calculate detailed match between job and candidate"""
        
        # Extract skill requirements and experience
        # Normalize ORM objects to dicts when necessary
        def _to_list(skills_obj):
            if isinstance(skills_obj, list):
                return skills_obj
            return []

        # Support ORM object attributes as well as dicts
        if isinstance(job_data, dict):
            job_skills = job_data.get('skills', []) or job_data.get('mandatory_skills', [])
        else:
            # Prefer normalized job_skills (Skill relation) when available; fallback to mandatory_skills (string based)
            job_skills = getattr(job_data, 'job_skills', None) or getattr(job_data, 'mandatory_skills', [])
        # Prefer candidate_skills when present; otherwise fall back to experiences
        if isinstance(candidate_data, dict):
            candidate_skills = candidate_data.get('skills', [])
        else:
            cs_list = getattr(candidate_data, 'candidate_skills', []) or []
            if cs_list:
                candidate_skills = [
                    {
                        'name': (cs.skill.name if getattr(cs, 'skill', None) else getattr(cs, 'name', '')),
                        'years_experience': getattr(cs, 'years_experience', getattr(cs, 'years', 0)),
                        'proficiency_level': getattr(cs, 'proficiency_level', 'beginner'),
                        'last_used': getattr(cs, 'last_used', None)
                    }
                    for cs in cs_list
                ]
            else:
                # Fallback to CandidateExperience rows
                exp_list = getattr(candidate_data, 'experiences', []) or []
                candidate_skills = [
                    {
                        'name': getattr(exp, 'skill', ''),
                        'years_experience': float(getattr(exp, 'years', 0)),
                        'proficiency_level': 'intermediate',
                        'last_used': None
                    }
                    for exp in exp_list
                ]
        
        # Calculate skill-specific matches
        skill_matches = []
        missing_skills = []
        experience_gaps = []
        strengths = []
        
        total_match_score = 0.0
        total_skills = len(job_skills)
        
        for job_skill in job_skills:
            # job_skill can be dict, ORM JobSkill (with Skill relation), or ORM JobMandatorySkill (string field)
            if isinstance(job_skill, dict):
                skill_name = job_skill.get('skill') or job_skill.get('name') or ''
            else:
                # ORM object path
                if hasattr(job_skill, 'skill'):
                    value = getattr(job_skill, 'skill')
                    # If this is joined Skill entity
                    try:
                        skill_name = value.name  # type: ignore[attr-defined]
                    except Exception:
                        # If value is a plain string (JobMandatorySkill)
                        skill_name = str(value)
                else:
                    skill_name = getattr(job_skill, 'name', '')
            if isinstance(job_skill, dict):
                required_years = job_skill.get('min_years_experience')
                if required_years is None:
                    required_years = job_skill.get('min_experience', 0)
            else:
                # ORM JobSkill or JobMandatorySkill
                required_years = getattr(job_skill, 'min_years_experience', None)
                if required_years is None:
                    required_years = getattr(job_skill, 'min_experience', 0)
            
            # Find matching candidate skill
            candidate_skill = self._find_matching_candidate_skill(skill_name, candidate_skills)
            
            if candidate_skill:
                candidate_years = candidate_skill.get('years_experience', 0)
                proficiency_level = candidate_skill.get('proficiency_level', 'beginner')
                last_used = candidate_skill.get('last_used')
                
                # Calculate match score
                if candidate_years >= required_years:
                    match_score = min(candidate_years / max(required_years, 1), 1.0)
                    meets_requirement = True
                    
                    if candidate_years > required_years * 1.5:
                        strengths.append(f"Strong {skill_name} experience ({candidate_years} years)")
                else:
                    match_score = candidate_years / max(required_years, 1)
                    meets_requirement = False
                    experience_gaps.append(f"{skill_name}: {candidate_years}/{required_years} years")
                
                skill_matches.append(SkillMatchResult(
                    skill_name=skill_name,
                    required_years=required_years,
                    candidate_years=candidate_years,
                    match_score=match_score,
                    proficiency_level=proficiency_level,
                    last_used=last_used,
                    meets_requirement=meets_requirement
                ))
                
                total_match_score += match_score
            else:
                missing_skills.append(skill_name)
                skill_matches.append(SkillMatchResult(
                    skill_name=skill_name,
                    required_years=required_years,
                    candidate_years=0.0,
                    match_score=0.0,
                    proficiency_level='none',
                    last_used=None,
                    meets_requirement=False
                ))
        
        # Calculate overall match score
        overall_score = total_match_score / max(total_skills, 1)
        
        # Generate explanation
        explanation = self._generate_match_explanation(
            skill_matches, missing_skills, experience_gaps, strengths, overall_score
        )
        
        # Resolve ids for both dicts and ORM instances
        cand_id = candidate_data['id'] if isinstance(candidate_data, dict) else getattr(candidate_data, 'id', 0)
        cand_name = candidate_data.get('name', f"Candidate #{cand_id}") if isinstance(candidate_data, dict) else getattr(candidate_data, 'name', f"Candidate #{cand_id}")
        job_id_val = job_data['id'] if isinstance(job_data, dict) else getattr(job_data, 'id', 0)

        return EnhancedRecommendationResult(
            candidate_id=cand_id,
            candidate_name=cand_name,
            job_id=job_id_val,
            overall_match_score=overall_score,
            skill_matches=skill_matches,
            missing_skills=missing_skills,
            experience_gaps=experience_gaps,
            strengths=strengths,
            explanation=explanation
        )
    
    def _find_matching_candidate_skill(self, job_skill_name: str, candidate_skills: List[Dict]) -> Optional[Dict]:
        """Find matching candidate skill using semantic similarity"""
        normalized_job_skill = self.skill_matcher.normalize_skill_name(job_skill_name)
        
        for candidate_skill in candidate_skills:
            normalized_candidate_skill = self.skill_matcher.normalize_skill_name(candidate_skill['name'])
            
            # Exact match
            if normalized_job_skill.lower() == normalized_candidate_skill.lower():
                return candidate_skill
            
            # Semantic match
            matches = self.skill_matcher.find_skill_matches(normalized_job_skill, threshold=0.5)
            for matched_skill, similarity in matches:
                if matched_skill.lower() == normalized_candidate_skill.lower():
                    return candidate_skill
        
        return None
    
    def _generate_match_explanation(
        self, 
        skill_matches: List[SkillMatchResult],
        missing_skills: List[str],
        experience_gaps: List[str],
        strengths: List[str],
        overall_score: float
    ) -> str:
        """Generate detailed explanation of the match"""
        explanation_parts = []
        
        # Overall score
        if overall_score >= 0.8:
            explanation_parts.append("Excellent match with strong skill alignment.")
        elif overall_score >= 0.6:
            explanation_parts.append("Good match with solid skill coverage.")
        elif overall_score >= 0.4:
            explanation_parts.append("Moderate match with some skill gaps.")
        else:
            explanation_parts.append("Limited match with significant skill gaps.")
        
        # Strengths
        if strengths:
            explanation_parts.append(f"Strengths: {', '.join(strengths[:3])}")
        
        # Missing skills
        if missing_skills:
            explanation_parts.append(f"Missing skills: {', '.join(missing_skills[:3])}")
        
        # Experience gaps
        if experience_gaps:
            explanation_parts.append(f"Experience gaps: {', '.join(experience_gaps[:3])}")
        
        # Skill breakdown
        matching_skills = [sm for sm in skill_matches if sm.meets_requirement]
        if matching_skills:
            explanation_parts.append(f"Meets requirements for {len(matching_skills)}/{len(skill_matches)} skills.")
        
        return " ".join(explanation_parts)
    
    async def parse_cv_and_create_candidate_skills(
        self, 
        db: AsyncSession, 
        candidate_id: int, 
        cv_file_path: str
    ) -> Dict:
        """Parse CV and create candidate skills with experience duration"""
        try:
            # Parse CV
            cv_data = self.cv_parser.parse_cv(cv_file_path)
            
            # Create candidate skills
            created_skills = []
            for skill in cv_data.skills:
                # Find or create skill in database
                db_skill = await skill.get_by_name(db, skill.name)
                if not db_skill:
                    # Create new skill
                    skill_data = {
                        'name': skill.name,
                        'category': skill.category,
                        'description': skill.description,
                        'aliases': skill.experience_description
                    }
                    db_skill = await skill.create(db, obj_in=skill_data)
                
                # Create candidate skill
                candidate_skill_data = {
                    'candidate_id': candidate_id,
                    'skill_id': db_skill.id,
                    'years_experience': skill.years_experience,
                    'proficiency_level': skill.proficiency_level,
                    'last_used': skill.last_used,
                    'experience_description': skill.experience_description,
                    'projects_worked': json.dumps(skill.projects_worked)
                }
                
                created_skill = await candidate_skill.create(db, obj_in=candidate_skill_data)
                created_skills.append(created_skill)
            
            # Update candidate's total experience
            total_experience = sum(skill.years_experience for skill in cv_data.skills)
            await candidate.update(db, db_obj=candidate_id, obj_in={'total_years_experience': total_experience})
            
            return {
                'success': True,
                'skills_created': len(created_skills),
                'total_experience': total_experience,
                'cv_analysis': {
                    'full_name': cv_data.full_name,
                    'email': cv_data.email,
                    'location': cv_data.location,
                    'skills': [skill.name for skill in cv_data.skills],
                    'experiences': len(cv_data.experiences),
                    'education': len(cv_data.education),
                    'certifications': cv_data.certifications,
                    'languages': cv_data.languages
                }
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Error parsing CV: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_job_with_skill_requirements(
        self, 
        db: AsyncSession, 
        job_data: Dict,
        skill_requirements: List[Dict]
    ) -> Dict:
        """Create job with detailed skill requirements"""
        try:
            # Create job
            job = await job.create(db, obj_in=job_data)
            
            # Create job skills
            created_skills = []
            for skill_req in skill_requirements:
                # Find or create skill
                db_skill = await skill.get_by_name(db, skill_req['name'])
                if not db_skill:
                    skill_data = {
                        'name': skill_req['name'],
                        'category': skill_req.get('category', 'other'),
                        'description': skill_req.get('description', '')
                    }
                    db_skill = await skill.create(db, obj_in=skill_data)
                
                # Create job skill requirement
                job_skill_data = {
                    'job_id': job.id,
                    'skill_id': db_skill.id,
                    'min_years_experience': skill_req.get('min_years_experience', 0),
                    'priority': skill_req.get('priority', 'required'),
                    'description': skill_req.get('description', '')
                }
                
                created_job_skill = await job_skill.create(db, obj_in=job_skill_data)
                created_skills.append(created_job_skill)
            
            return {
                'success': True,
                'job_id': job.id,
                'skills_created': len(created_skills)
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Error creating job with skills: {e}")
            return {
                'success': False,
                'error': str(e)
            } 