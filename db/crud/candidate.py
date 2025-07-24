# File: db/crud/candidate.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from db.crud.base import CRUDBase
from models.candidate import Candidate, CandidateExperience
from schemas.candidate import CandidateCreate, CandidateUpdate


class CRUDCandidate(CRUDBase[Candidate, CandidateCreate, CandidateUpdate]):
    async def get_with_experiences(self, db: AsyncSession, id: int) -> Optional[Candidate]:
        """Get candidate with all experiences"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.experiences))
            .where(self.model.id == id)
        )
        return result.scalar_one_or_none()

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
        await db.refresh(candidate)
        return candidate


candidate = CRUDCandidate(Candidate)
