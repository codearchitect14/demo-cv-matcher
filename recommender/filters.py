from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models.candidate import Candidate, CandidateExperience
from models.job import Job, JobMandatorySkill
from models.application import Application
from models.application import ApplicationStatusEnum
import logging

logger = logging.getLogger(__name__)

class FilteringService:
    """Service for enforcing strict business rules and constraints"""
    
    def __init__(self):
        """Initialize filtering service"""
        self.logger = logging.getLogger(__name__)
    
    async def filter_candidates_for_job(
        self, 
        candidates: List[Dict[str, Any]], 
        job: Job, 
        db: AsyncSession,
        strict_mode: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter candidates based on job requirements
        
        Args:
            candidates: List of candidate recommendations from semantic search
            job: Job object with requirements
            db: Database session
            strict_mode: If True, enforce all constraints strictly
            
        Returns:
            Filtered list of candidates with validation results
        """
        filtered_candidates = []
        
        for candidate_data in candidates:
            candidate = candidate_data.get('candidate')
            if not candidate:
                continue
            
            # Get candidate with full details
            candidate = await self._get_candidate_with_details(db, candidate.id)
            if not candidate:
                continue
            
            # Apply all filters
            validation_result = await self._validate_candidate_for_job(
                candidate, job, db, strict_mode
            )
            
            if validation_result['is_valid']:
                # Add validation details to candidate data
                candidate_data['validation'] = validation_result
                candidate_data['filter_score'] = validation_result['filter_score']
                filtered_candidates.append(candidate_data)
            else:
                self.logger.info(f"Candidate {candidate.id} filtered out: {validation_result['reasons']}")
        
        # Sort by filter score (higher = better match)
        filtered_candidates.sort(key=lambda x: x['filter_score'], reverse=True)
        
        return filtered_candidates
    
    async def filter_jobs_for_candidate(
        self, 
        jobs: List[Dict[str, Any]], 
        candidate: Candidate, 
        db: AsyncSession,
        strict_mode: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter jobs based on candidate preferences
        
        Args:
            jobs: List of job recommendations from semantic search
            candidate: Candidate object with preferences
            db: Database session
            strict_mode: If True, enforce all constraints strictly
            
        Returns:
            Filtered list of jobs with validation results
        """
        filtered_jobs = []
        
        for job_data in jobs:
            job = job_data.get('job')
            if not job:
                continue
            
            # Get job with full details
            job = await self._get_job_with_details(db, job.id)
            if not job:
                continue
            
            # Apply all filters
            validation_result = await self._validate_job_for_candidate(
                job, candidate, db, strict_mode
            )
            
            if validation_result['is_valid']:
                # Add validation details to job data
                job_data['validation'] = validation_result
                job_data['filter_score'] = validation_result['filter_score']
                filtered_jobs.append(job_data)
            else:
                self.logger.info(f"Job {job.id} filtered out: {validation_result['reasons']}")
        
        # Sort by filter score (higher = better match)
        filtered_jobs.sort(key=lambda x: x['filter_score'], reverse=True)
        
        return filtered_jobs
    
    async def _validate_candidate_for_job(
        self, 
        candidate: Candidate, 
        job: Job, 
        db: AsyncSession,
        strict_mode: bool
    ) -> Dict[str, Any]:
        """Validate candidate against job requirements"""
        validation_result = {
            'is_valid': True,
            'filter_score': 0.0,
            'reasons': [],
            'details': {}
        }
        
        # 1. Domain Match
        domain_match = self._check_domain_match(candidate.domain, job.domain)
        validation_result['details']['domain_match'] = domain_match
        if not domain_match['is_valid'] and strict_mode:
            validation_result['is_valid'] = False
            validation_result['reasons'].append(domain_match['reason'])
        else:
            validation_result['filter_score'] += domain_match['score']
        
        # 2. Location Match
        location_match = self._check_location_match(candidate.location, job.location)
        validation_result['details']['location_match'] = location_match
        if not location_match['is_valid'] and strict_mode:
            validation_result['is_valid'] = False
            validation_result['reasons'].append(location_match['reason'])
        else:
            validation_result['filter_score'] += location_match['score']
        
        # 3. Salary Compatibility
        salary_match = self._check_salary_compatibility(
            candidate.expected_salary_min, 
            candidate.expected_salary_max,
            job.salary_min,
            job.salary_max
        )
        validation_result['details']['salary_match'] = salary_match
        if not salary_match['is_valid'] and strict_mode:
            validation_result['is_valid'] = False
            validation_result['reasons'].append(salary_match['reason'])
        else:
            validation_result['filter_score'] += salary_match['score']
        
        # 4. Experience Requirements
        experience_match = await self._check_experience_requirements(
            candidate, job, db
        )
        validation_result['details']['experience_match'] = experience_match
        if not experience_match['is_valid'] and strict_mode:
            validation_result['is_valid'] = False
            validation_result['reasons'].append(experience_match['reason'])
        else:
            validation_result['filter_score'] += experience_match['score']
        
        # 5. Mandatory Skills Check
        skills_match = await self._check_mandatory_skills(
            candidate, job, db
        )
        validation_result['details']['skills_match'] = skills_match
        if not skills_match['is_valid'] and strict_mode:
            validation_result['is_valid'] = False
            validation_result['reasons'].append(skills_match['reason'])
        else:
            validation_result['filter_score'] += skills_match['score']
        
        # 6. Application History (avoid duplicates)
        application_check = await self._check_application_history(
            candidate.id, job.id, db
        )
        validation_result['details']['application_check'] = application_check
        if not application_check['is_valid']:
            validation_result['is_valid'] = False
            validation_result['reasons'].append(application_check['reason'])
        
        return validation_result
    
    async def _validate_job_for_candidate(
        self, 
        job: Job, 
        candidate: Candidate, 
        db: AsyncSession,
        strict_mode: bool
    ) -> Dict[str, Any]:
        """Validate job against candidate preferences (reverse validation)"""
        # Use the same validation logic but from job perspective
        return await self._validate_candidate_for_job(candidate, job, db, strict_mode)
    
    def _check_domain_match(self, candidate_domain: str, job_domain: str) -> Dict[str, Any]:
        """Check if candidate and job domains match"""
        if not candidate_domain or not job_domain:
            return {
                'is_valid': False,
                'score': 0.0,
                'reason': 'Missing domain information'
            }
        
        # Exact match
        if candidate_domain.lower() == job_domain.lower():
            return {
                'is_valid': True,
                'score': 1.0,
                'reason': f'Domain match: {candidate_domain}'
            }
        
        # Partial match (e.g., "Software Development" vs "Web Development")
        candidate_words = set(candidate_domain.lower().split())
        job_words = set(job_domain.lower().split())
        overlap = candidate_words.intersection(job_words)
        
        if overlap:
            return {
                'is_valid': True,
                'score': 0.7,
                'reason': f'Partial domain match: {overlap}'
            }
        
        return {
            'is_valid': False,
            'score': 0.0,
            'reason': f'Domain mismatch: {candidate_domain} vs {job_domain}'
        }
    
    def _check_location_match(self, candidate_location: str, job_location: str) -> Dict[str, Any]:
        """Check if candidate and job locations are compatible"""
        if not candidate_location or not job_location:
            return {
                'is_valid': False,
                'score': 0.0,
                'reason': 'Missing location information'
            }
        
        # Exact match
        if candidate_location.lower() == job_location.lower():
            return {
                'is_valid': True,
                'score': 1.0,
                'reason': f'Location match: {candidate_location}'
            }
        
        # Remote work check
        if 'remote' in job_location.lower() or 'remote' in candidate_location.lower():
            return {
                'is_valid': True,
                'score': 0.8,
                'reason': 'Remote work compatible'
            }
        
        # Partial match (e.g., "Lahore" vs "Lahore, Pakistan")
        if candidate_location.lower() in job_location.lower() or job_location.lower() in candidate_location.lower():
            return {
                'is_valid': True,
                'score': 0.9,
                'reason': f'Location compatible: {candidate_location}'
            }
        
        return {
            'is_valid': False,
            'score': 0.0,
            'reason': f'Location mismatch: {candidate_location} vs {job_location}'
        }
    
    def _check_salary_compatibility(
        self, 
        candidate_min: Optional[int], 
        candidate_max: Optional[int],
        job_min: Optional[int], 
        job_max: Optional[int]
    ) -> Dict[str, Any]:
        """Check if salary expectations are compatible"""
        
        # If no salary info, assume compatible
        if not candidate_min and not candidate_max and not job_min and not job_max:
            return {
                'is_valid': True,
                'score': 0.5,
                'reason': 'No salary information available'
            }
        
        # Check if candidate's expected salary overlaps with job salary range
        if candidate_min and job_max and candidate_min > job_max:
            return {
                'is_valid': False,
                'score': 0.0,
                'reason': f'Candidate minimum salary ({candidate_min}) exceeds job maximum ({job_max})'
            }
        
        if candidate_max and job_min and candidate_max < job_min:
            return {
                'is_valid': False,
                'score': 0.0,
                'reason': f'Candidate maximum salary ({candidate_max}) below job minimum ({job_min})'
            }
        
        # Calculate overlap score
        if candidate_min and candidate_max and job_min and job_max:
            overlap_min = max(candidate_min, job_min)
            overlap_max = min(candidate_max, job_max)
            
            if overlap_min <= overlap_max:
                overlap_ratio = (overlap_max - overlap_min) / max(candidate_max - candidate_min, job_max - job_min)
                return {
                    'is_valid': True,
                    'score': 0.5 + (overlap_ratio * 0.5),
                    'reason': f'Salary overlap: {overlap_min}-{overlap_max}'
                }
        
        return {
            'is_valid': True,
            'score': 0.7,
            'reason': 'Salary ranges compatible'
        }
    
    async def _check_experience_requirements(
        self, 
        candidate: Candidate, 
        job: Job, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Check if candidate meets total experience requirements"""
        
        if not job.total_years_required:
            return {
                'is_valid': True,
                'score': 1.0,
                'reason': 'No total experience requirement'
            }
        
        # Calculate total experience from candidate's experiences
        total_experience = sum(exp.years for exp in candidate.experiences)
        
        if total_experience >= job.total_years_required:
            return {
                'is_valid': True,
                'score': 1.0,
                'reason': f'Total experience: {total_experience} years (required: {job.total_years_required})'
            }
        else:
            return {
                'is_valid': False,
                'score': 0.0,
                'reason': f'Insufficient total experience: {total_experience} years (required: {job.total_years_required})'
            }
    
    async def _check_mandatory_skills(
        self, 
        candidate: Candidate, 
        job: Job, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Check if candidate has all mandatory skills with required experience using advanced matching"""
        
        if not job.mandatory_skills:
            return {
                'is_valid': True,
                'score': 1.0,
                'reason': 'No mandatory skills required'
            }
        
        from services.skill_matcher import skill_matcher
        
        # Convert experiences to format expected by skill matcher
        candidate_skills = []
        for exp in candidate.experiences:
            candidate_skills.append({
                'skill': exp.skill,
                'years': exp.years,
                'description': exp.description or ""
            })
        
        # Convert mandatory skills to format expected by skill matcher
        job_skills = []
        for skill in job.mandatory_skills:
            job_skills.append({
                'skill': skill.skill,
                'min_experience': skill.min_experience
            })
        
        # Use advanced skill matcher
        validation_results = skill_matcher.validate_skill_requirements(job_skills, candidate_skills)
        
        missing_skills = []
        skill_matches = []
        partial_matches = []
        
        for skill_name, result in validation_results.items():
            if result['is_met']:
                skill_matches.append(f"{skill_name} ({result['best_match']['years']} years, required: {result['required_years']})")
            elif result['best_match'] and result['best_match']['match_score'] >= 0.7:
                partial_matches.append(f"{skill_name} (partial match: {result['best_match']['skill']}, score: {result['best_match']['match_score']:.2f})")
            else:
                missing_skills.append(f"{skill_name} (not found)")
        
        # Calculate overall score
        overall_score = skill_matcher.calculate_overall_match_score(validation_results)
        
        if missing_skills and not skill_matches:
            return {
                'is_valid': False,
                'score': overall_score,
                'reason': f'Missing skills: {", ".join(missing_skills)}'
            }
        elif skill_matches:
            reason_parts = []
            if skill_matches:
                reason_parts.append(f"Matched: {', '.join(skill_matches)}")
            if partial_matches:
                reason_parts.append(f"Partial matches: {', '.join(partial_matches)}")
            if missing_skills:
                reason_parts.append(f"Missing: {', '.join(missing_skills)}")
            
            return {
                'is_valid': len(missing_skills) == 0,
                'score': overall_score,
                'reason': '; '.join(reason_parts)
            }
        else:
            return {
                'is_valid': False,
                'score': overall_score,
                'reason': f'No skill matches found: {", ".join(missing_skills)}'
            }
    
    async def _check_application_history(
        self, 
        candidate_id: int, 
        job_id: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Check if candidate has already applied to this job"""
        
        result = await db.execute(
            select(Application).where(
                Application.candidate_id == candidate_id,
                Application.job_id == job_id
            )
        )
        existing_application = result.scalar_one_or_none()
        
        if existing_application:
            return {
                'is_valid': False,
                'score': 0.0,
                'reason': f'Already applied with status: {existing_application.status}'
            }
        
        return {
            'is_valid': True,
            'score': 1.0,
            'reason': 'No previous application'
        }
    
    async def _get_candidate_with_details(self, db: AsyncSession, candidate_id: int) -> Optional[Candidate]:
        """Get candidate with all related data"""
        result = await db.execute(
            select(Candidate)
            .options(selectinload(Candidate.experiences))
            .where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_job_with_details(self, db: AsyncSession, job_id: int) -> Optional[Job]:
        """Get job with all related data"""
        result = await db.execute(
            select(Job)
            .options(selectinload(Job.mandatory_skills))
            .where(Job.id == job_id)
        )
        return result.scalar_one_or_none()

# Global instance
filtering_service = FilteringService()
