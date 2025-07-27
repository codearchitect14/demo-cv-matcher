# Today's date: 25/07/2025
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.candidate import candidate as candidate_crud
from db.crud.job import job as job_crud  # Moved to top level (Issue #2)
from schemas.candidate import CandidateCreate, CandidateUpdate, CandidateResponse
from schemas.search import CandidateSearchFilter
from core.exceptions import NotFoundException, ValidationException


class CandidateService:
    def __init__(self):
        self.crud = candidate_crud
        self.job_crud = job_crud  # Inject dependency (Issue #2)

    async def create_candidate(
        self, db: AsyncSession, candidate_data: CandidateCreate
    ) -> CandidateResponse:
        """Create new candidate with experiences"""
        try:
            # Validate unique skills in experiences
            skills = [exp.skill for exp in candidate_data.experiences]
            if len(skills) != len(set(skills)):
                raise ValidationException("Duplicate skills are not allowed")
            
            candidate = await self.crud.create_with_experiences(db, candidate_data)
            return CandidateResponse.model_validate(candidate)  # Fixed deprecated method (Issue #4)
        except Exception as e:
            raise ValidationException(f"Failed to create candidate: {str(e)}")

    async def get_candidate(self, db: AsyncSession, candidate_id: int) -> CandidateResponse:
        """Get candidate by ID with experiences"""
        candidate = await self.crud.get_with_experiences(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")
        return CandidateResponse.model_validate(candidate)  # Fixed deprecated method (Issue #4)

    async def update_candidate(
        self, db: AsyncSession, candidate_id: int, update_data: CandidateUpdate
    ) -> CandidateResponse:
        """Update candidate information"""
        candidate = await self.crud.get(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")
        
        updated_candidate = await self.crud.update(db, candidate, update_data)
        return CandidateResponse.model_validate(updated_candidate)  # Fixed deprecated method (Issue #4)

    async def delete_candidate(self, db: AsyncSession, candidate_id: int) -> bool:
        """Delete candidate"""
        candidate = await self.crud.delete(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")
        return True

    async def get_candidates(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[CandidateResponse]:
        """Get all candidates with pagination"""
        candidates = await self.crud.get_multi_with_experiences(db, skip=skip, limit=limit)  # Use eager loading (Issue #8)
        return [CandidateResponse.model_validate(candidate) for candidate in candidates]  # Fixed deprecated method (Issue #4)

    async def search_candidates(
        self, db: AsyncSession, filters: CandidateSearchFilter, skip: int = 0, limit: int = 100
    ) -> List[CandidateResponse]:
        """Search candidates with filters using CRUD abstraction"""
        candidates = await self.crud.search_candidates(db, filters, skip, limit)  # Use CRUD method (Issue #1)
        return [CandidateResponse.model_validate(candidate) for candidate in candidates]  # Fixed deprecated method (Issue #4)

    async def get_candidates_by_domain(
        self, db: AsyncSession, domain: str
    ) -> List[CandidateResponse]:
        """Get candidates by domain"""
        candidates = await self.crud.get_by_domain(db, domain)
        return [CandidateResponse.model_validate(candidate) for candidate in candidates]  # Fixed deprecated method (Issue #4)

    async def add_experience(
        self, db: AsyncSession, candidate_id: int, skill: str, years: int, description: str = None
    ) -> CandidateResponse:
        """Add new experience to candidate using CRUD"""
        candidate = await self.crud.get(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")

        # Use CRUD method instead of direct DB operations (Issue #5)
        updated_candidate = await self.crud.add_experience(db, candidate_id, skill, years, description)
        return CandidateResponse.model_validate(updated_candidate)  # Fixed deprecated method (Issue #4)

    async def update_experience(
        self, db: AsyncSession, candidate_id: int, skill: str, years: int, description: str = None
    ) -> CandidateResponse:
        """Update existing experience using CRUD"""
        # Use CRUD method instead of direct DB operations (Issue #5)
        updated_candidate = await self.crud.update_experience(db, candidate_id, skill, years, description)
        return CandidateResponse.model_validate(updated_candidate)  # Fixed deprecated method (Issue #4)

    async def check_job_compatibility(
        self, db: AsyncSession, candidate_id: int, job_id: int
    ) -> Dict[str, Any]:
        """Check if candidate is compatible with job requirements"""
        candidate = await self.crud.get(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")

        # Use CRUD method for skill requirements (Issue #6)
        skill_check = await self.crud.check_skill_requirements(db, candidate_id, job_id)
        
        # Use injected job_crud instead of importing inside method (Issue #2)
        job = await self.job_crud.get(db, job_id)
        if not job:
            raise NotFoundException(f"Job with ID {job_id} not found")

        # Move salary compatibility logic to separate service (Issue #9)
        from services.salary_compatibility_service import SalaryCompatibilityService
        salary_service = SalaryCompatibilityService()
        salary_details = salary_service.check_compatibility(candidate, job)

        # Overall compatibility
        overall_compatible = (
            skill_check["meets_all_requirements"] and 
            salary_details["compatible"] and
            candidate.domain == job.domain
        )

        return {
            "compatible": overall_compatible,
            "skills": skill_check,
            "salary": salary_details,
            "domain_match": candidate.domain == job.domain,
            "location_match": candidate.location == job.location
        }

    async def get_candidate_stats(self, db: AsyncSession, candidate_id: int) -> Dict[str, Any]:
        """Get candidate statistics"""
        candidate = await self.crud.get_with_experiences(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")

        # Get application stats
        from db.crud.application import application as app_crud
        applications = await app_crud.get_by_candidate(db, candidate_id)
        
        # Get interaction stats
        from db.crud.interaction import interaction_log
        interactions = await interaction_log.get_by_candidate(db, candidate_id)

        return {
            "total_experiences": len(candidate.experiences),
            "total_skills": len(set([exp.skill for exp in candidate.experiences])),
            "max_experience_years": max([exp.years for exp in candidate.experiences]) if candidate.experiences else 0,
            "total_applications": len(applications),
            "total_interactions": len(interactions),
            "skills_list": [exp.skill for exp in candidate.experiences]
        }