# File: db/crud/job.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from db.crud.base import CRUDBase
from models.job import Job, JobMandatorySkill
from schemas.job import JobCreate, JobUpdate


class CRUDJob(CRUDBase[Job, JobCreate, JobUpdate]):
    async def get_with_skills(self, db: AsyncSession, id: int) -> Optional[Job]:
        """Get job with mandatory skills"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_domain(self, db: AsyncSession, domain: str) -> List[Job]:
        """Get jobs by domain"""
        result = await db.execute(
            select(self.model).where(self.model.domain == domain)
        )
        return result.scalars().all()

    async def get_by_location(self, db: AsyncSession, location: str) -> List[Job]:
        """Get jobs by location"""
        result = await db.execute(
            select(self.model).where(self.model.location == location)
        )
        return result.scalars().all()

    async def get_by_salary_range(
        self, db: AsyncSession, min_salary: int, max_salary: int
    ) -> List[Job]:
        """Get jobs within salary range"""
        result = await db.execute(
            select(self.model).where(
                self.model.salary_min >= min_salary,
                self.model.salary_max <= max_salary
            )
        )
        return result.scalars().all()

    async def create_with_skills(self, db: AsyncSession, obj_in: JobCreate) -> Job:
        """Create job with mandatory skills"""
        # Create job first
        job_data = obj_in.dict(exclude={'mandatory_skills'})
        job = Job(**job_data)
        db.add(job)
        await db.flush()  # Get the ID without committing

        # Create mandatory skills
        for skill_data in obj_in.mandatory_skills:
            skill = JobMandatorySkill(
                job_id=job.id,
                **skill_data.dict()
            )
            db.add(skill)

        await db.commit()
        await db.refresh(job)
        return job


job = CRUDJob(Job)