#File: db/crud/candidate.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, Index
from db.crud.base import CRUDBase
from models.candidate import Candidate, CandidateExperience
from schemas.candidate import CandidateCreate, CandidateUpdate

class CRUDCandidate(CRUDBase[Candidate, CandidateCreate, CandidateUpdate]):
    async def get_with_experiences(self, db: AsyncSession, id: int) -> Optional[Candidate]:
        """Get candidate with all experiences, applications, and interactions using eager loading"""
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.experiences),
                selectinload(self.model.applications),
                selectinload(self.model.interactions)
            )
            .where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi_with_experiences(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Candidate]:
        """Get multiple candidates with experiences, applications, and interactions using eager loading"""
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.experiences),
                selectinload(self.model.applications),
                selectinload(self.model.interactions)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_domain(self, db: AsyncSession, domain: str) -> List[Candidate]:
        """Get candidates by domain"""
        result = await db.execute(
            select(self.model).where(self.model.domain == domain)
        )
        return result.scalars().all()

    async def get_by_location(self, db: AsyncSession, location: str) -> List[Candidate]:
        """Get candidates by location"""
        result = await db.execute(
            select(self.model).where(self.model.location == location)
        )
        return result.scalars().all()

    async def get_by_salary_range(
        self, db: AsyncSession, min_salary: int, max_salary: int
    ) -> List[Candidate]:
        """Get candidates within salary range"""
        result = await db.execute(
            select(self.model).where(
                self.model.expected_salary_min >= min_salary,
                self.model.expected_salary_max <= max_salary
            )
        )
        return result.scalars().all()

    async def create_with_experiences(
        self, db: AsyncSession, obj_in: CandidateCreate
    ) -> Candidate:
        """Create candidate with experiences"""
        # Create candidate first
        candidate_data = obj_in.dict(exclude={'experiences'})
        candidate = Candidate(**candidate_data)
        db.add(candidate)
        await db.flush()  # Get the ID without committing

        # Create experiences
        for exp_data in obj_in.experiences:
            experience = CandidateExperience(
                candidate_id=candidate.id,
                **exp_data.dict()
            )
            db.add(experience)

        await db.commit()
        # Re-query with eager loading to ensure all relationships are loaded
        return await self.get_with_experiences(db, candidate.id)

    async def search_candidates(
        self, db: AsyncSession, filters: 'CandidateSearchFilter', skip: int = 0, limit: int = 100
    ) -> List[Candidate]:
        """Search candidates with filters using CRUD abstraction (Issue #1)"""
        from models.candidate import CandidateExperience
        
        query = select(self.model).options(
            selectinload(self.model.experiences),
            selectinload(self.model.applications),
            selectinload(self.model.interactions)
        )  # Eager loading
        conditions = []

        # Apply filters
        if filters.location:
            conditions.append(self.model.location.ilike(f"%{filters.location}%"))
        
        if filters.domain:
            conditions.append(self.model.domain == filters.domain)
        
        if filters.expected_salary_min:
            conditions.append(self.model.expected_salary_min >= filters.expected_salary_min)
        
        if filters.expected_salary_max:
            conditions.append(self.model.expected_salary_max <= filters.expected_salary_max)

        # Skills filter - candidates who have any of the specified skills
        if filters.skills:
            skills_subquery = select(CandidateExperience.candidate_id).where(
                and_(
                    CandidateExperience.skill.in_(filters.skills),
                    CandidateExperience.years >= (filters.min_experience or 0)
                )
            ).distinct()
            conditions.append(self.model.id.in_(skills_subquery))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def add_experience(
        self, db: AsyncSession, candidate_id: int, experience_data: dict
    ) -> Candidate:
        """Add experience to candidate using experience data dictionary"""
        # Check if skill already exists
        existing_exp = await db.execute(
            select(CandidateExperience).where(
                and_(
                    CandidateExperience.candidate_id == candidate_id,
                    CandidateExperience.skill == experience_data.get('skill')
                )
            )
        )
        if existing_exp.scalar_one_or_none():
            from core.exceptions import ValidationException
            raise ValidationException(f"Experience for skill '{experience_data.get('skill')}' already exists")

        # Create new experience
        new_experience = CandidateExperience(
            candidate_id=candidate_id,
            skill=experience_data.get('skill'),
            years=experience_data.get('years'),
            description=experience_data.get('description')
        )
        db.add(new_experience)
        await db.commit()
        
        # Return updated candidate
        return await self.get_with_experiences(db, candidate_id)

    async def update_experience(
        self, db: AsyncSession, candidate_id: int, experience_id: int, experience_data: dict
    ) -> CandidateExperience:
        """Update existing experience using experience data dictionary"""
        experience = await db.execute(
            select(CandidateExperience).where(
                and_(
                    CandidateExperience.candidate_id == candidate_id,
                    CandidateExperience.id == experience_id
                )
            )
        )
        experience = experience.scalar_one_or_none()
        
        if not experience:
            from core.exceptions import NotFoundException
            raise NotFoundException(f"Experience with ID {experience_id} not found for candidate {candidate_id}")

        # Update experience fields
        if 'skill' in experience_data:
            experience.skill = experience_data['skill']
        if 'years' in experience_data:
            experience.years = experience_data['years']
        if 'description' in experience_data:
            experience.description = experience_data['description']
        
        await db.commit()
        await db.refresh(experience)
        return experience

    async def remove_experience(
        self, db: AsyncSession, candidate_id: int, experience_id: int
    ) -> None:
        """Remove experience from candidate via CRUD"""
        experience = await db.execute(
            select(CandidateExperience).where(
                and_(
                    CandidateExperience.candidate_id == candidate_id,
                    CandidateExperience.id == experience_id
                )
            )
        )
        experience = experience.scalar_one_or_none()
        
        if not experience:
            from core.exceptions import NotFoundException
            raise NotFoundException(f"Experience with ID {experience_id} not found for candidate {candidate_id}")

        await db.delete(experience)
        await db.commit()

    async def check_skill_requirements(
        self, db: AsyncSession, candidate_id: int, job_id: int
    ) -> dict:
        """Check skill requirements (moved from utils - Issue #6)"""
        from db.crud.job import job as job_crud
        
        # Get job requirements
        job = await job_crud.get(db, job_id)
        if not job:
            return {"meets_all_requirements": False, "error": "Job not found"}
        
        # Get candidate experiences
        candidate = await self.get_with_experiences(db, candidate_id)
        if not candidate:
            return {"meets_all_requirements": False, "error": "Candidate not found"}
        
        # Check skill requirements
        candidate_skills = {exp.skill: exp.years for exp in candidate.experiences}
        required_skills = job.required_skills  # Assuming this exists
        
        missing_skills = []
        insufficient_experience = []
        
        for skill_req in required_skills:
            skill_name = skill_req.get('skill')
            min_years = skill_req.get('years', 0)
            
            if skill_name not in candidate_skills:
                missing_skills.append(skill_name)
            elif candidate_skills[skill_name] < min_years:
                insufficient_experience.append({
                    'skill': skill_name,
                    'required': min_years,
                    'candidate_has': candidate_skills[skill_name]
                })
        
        meets_all = len(missing_skills) == 0 and len(insufficient_experience) == 0
        
        return {
            "meets_all_requirements": meets_all,
            "missing_skills": missing_skills,
            "insufficient_experience": insufficient_experience,
            "candidate_skills": candidate_skills
        }

    async def get_candidates_zero_visibility(self, db: AsyncSession, days_threshold: int = 30, limit: int = 20) -> List[Candidate]:
        """Get candidates with zero visibility/activity in the last N days"""
        from datetime import datetime, timedelta
        from db.crud.application import application as application_crud
        from services.interaction_service import interaction_service
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        # Get all candidates
        result = await db.execute(
            select(self.model).limit(limit)
        )
        candidates = result.scalars().all()
        
        # Filter candidates with no recent activity
        candidates_zero_visibility = []
        for candidate in candidates:
            # Check for recent applications
            applications = await application_crud.get_by_candidate(db, candidate.id)
            recent_applications = [app for app in applications if app.created_at >= cutoff_date]
            
            # Check for recent interactions
            interactions = await interaction_service.get_user_interactions(db, candidate.id, days_back=days_threshold)
            
            if not recent_applications and not interactions:
                candidates_zero_visibility.append(candidate)
        
        return candidates_zero_visibility

    async def count_recent(self, db: AsyncSession, days_back: int = 7) -> int:
        """Get count of recent candidates"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        result = await db.execute(
            select(self.model).where(self.model.created_at >= cutoff_date)
        )
        return len(result.scalars().all())

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Candidate]:
        """Get candidate by email"""
        result = await db.execute(
            select(self.model).where(self.model.email == email)
        )
        return result.scalar_one_or_none()


candidate = CRUDCandidate(Candidate)