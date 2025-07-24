# File: services/candidate_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from db.crud.candidate import candidate as candidate_crud
from db.utils import check_skill_requirements
from schemas.candidate import CandidateCreate, CandidateUpdate, CandidateResponse
from schemas.search import CandidateSearchFilter
from models.candidate import Candidate, CandidateExperience
from core.exceptions import NotFoundException, ValidationException


class CandidateService:
    def __init__(self):
        self.crud = candidate_crud

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
            return CandidateResponse.from_orm(candidate)
        except Exception as e:
            raise ValidationException(f"Failed to create candidate: {str(e)}")

    async def get_candidate(self, db: AsyncSession, candidate_id: int) -> CandidateResponse:
        """Get candidate by ID with experiences"""
        candidate = await self.crud.get_with_experiences(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")
        return CandidateResponse.from_orm(candidate)

    async def update_candidate(
        self, db: AsyncSession, candidate_id: int, update_data: CandidateUpdate
    ) -> CandidateResponse:
        """Update candidate information"""
        candidate = await self.crud.get(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")
        
        updated_candidate = await self.crud.update(db, candidate, update_data)
        return CandidateResponse.from_orm(updated_candidate)

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
        candidates = await self.crud.get_multi(db, skip=skip, limit=limit)
        return [CandidateResponse.from_orm(candidate) for candidate in candidates]

    async def search_candidates(
        self, db: AsyncSession, filters: CandidateSearchFilter, skip: int = 0, limit: int = 100
    ) -> List[CandidateResponse]:
        """Search candidates with filters"""
        query = select(Candidate)
        conditions = []

        # Apply filters
        if filters.location:
            conditions.append(Candidate.location.ilike(f"%{filters.location}%"))
        
        if filters.domain:
            conditions.append(Candidate.domain == filters.domain)
        
        if filters.expected_salary_min:
            conditions.append(Candidate.expected_salary_min >= filters.expected_salary_min)
        
        if filters.expected_salary_max:
            conditions.append(Candidate.expected_salary_max <= filters.expected_salary_max)

        # Skills filter - candidates who have any of the specified skills
        if filters.skills:
            skills_subquery = select(CandidateExperience.candidate_id).where(
                and_(
                    CandidateExperience.skill.in_(filters.skills),
                    CandidateExperience.years >= (filters.min_experience or 0)
                )
            ).distinct()
            conditions.append(Candidate.id.in_(skills_subquery))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        candidates = result.scalars().all()
        
        return [CandidateResponse.from_orm(candidate) for candidate in candidates]

    async def get_candidates_by_domain(
        self, db: AsyncSession, domain: str
    ) -> List[CandidateResponse]:
        """Get candidates by domain"""
        candidates = await self.crud.get_by_domain(db, domain)
        return [CandidateResponse.from_orm(candidate) for candidate in candidates]

    async def add_experience(
        self, db: AsyncSession, candidate_id: int, skill: str, years: int, description: str = None
    ) -> CandidateResponse:
        """Add new experience to candidate"""
        candidate = await self.crud.get(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")

        # Check if skill already exists
        existing_exp = await db.execute(
            select(CandidateExperience).where(
                and_(
                    CandidateExperience.candidate_id == candidate_id,
                    CandidateExperience.skill == skill
                )
            )
        )
        if existing_exp.scalar_one_or_none():
            raise ValidationException(f"Experience for skill '{skill}' already exists")

        # Create new experience
        new_experience = CandidateExperience(
            candidate_id=candidate_id,
            skill=skill,
            years=years,
            description=description
        )
        db.add(new_experience)
        await db.commit()

        # Return updated candidate
        return await self.get_candidate(db, candidate_id)

    async def update_experience(
        self, db: AsyncSession, candidate_id: int, skill: str, years: int, description: str = None
    ) -> CandidateResponse:
        """Update existing experience"""
        experience = await db.execute(
            select(CandidateExperience).where(
                and_(
                    CandidateExperience.candidate_id == candidate_id,
                    CandidateExperience.skill == skill
                )
            )
        )
        experience = experience.scalar_one_or_none()
        
        if not experience:
            raise NotFoundException(f"Experience for skill '{skill}' not found")

        experience.years = years
        if description is not None:
            experience.description = description
        
        await db.commit()
        return await self.get_candidate(db, candidate_id)

    async def check_job_compatibility(
        self, db: AsyncSession, candidate_id: int, job_id: int
    ) -> Dict[str, Any]:
        """Check if candidate is compatible with job requirements"""
        candidate = await self.crud.get(db, candidate_id)
        if not candidate:
            raise NotFoundException(f"Candidate with ID {candidate_id} not found")

        # Check skill requirements
        skill_check = await check_skill_requirements(db, candidate_id, job_id)
        
        # Get job details for salary comparison
        from db.crud.job import job as job_crud
        job = await job_crud.get(db, job_id)
        if not job:
            raise NotFoundException(f"Job with ID {job_id} not found")

        # Check salary compatibility
        salary_compatible = True
        salary_details = {}
        
        if candidate.expected_salary_min and job.salary_max:
            if candidate.expected_salary_min > job.salary_max:
                salary_compatible = False
        
        if candidate.expected_salary_max and job.salary_min:
            if candidate.expected_salary_max < job.salary_min:
                salary_compatible = False

        salary_details = {
            "compatible": salary_compatible,
            "candidate_min": candidate.expected_salary_min,
            "candidate_max": candidate.expected_salary_max,
            "job_min": job.salary_min,
            "job_max": job.salary_max
        }

        # Overall compatibility
        overall_compatible = (
            skill_check["meets_all_requirements"] and 
            salary_compatible and
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


