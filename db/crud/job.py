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

    async def get_with_mandatory_skills(self, db: AsyncSession, id: int) -> Optional[Job]:
        """Get job with mandatory skills (alias for get_with_skills)"""
        return await self.get_with_skills(db, id)

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

    async def get_by_recruiter(self, db: AsyncSession, recruiter_id: int) -> List[Job]:
        """Get jobs by recruiter ID"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .where(self.model.recruiter_id == recruiter_id)
            .order_by(self.model.created_at.desc())
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

    async def get_multi_with_filters(
        self, db: AsyncSession, filters: dict = None, skip: int = 0, limit: int = 100
    ) -> List[Job]:
        """Get multiple jobs with filters"""
        query = select(self.model).options(selectinload(self.model.mandatory_skills))
        
        if filters:
            conditions = []
            if filters.get("location"):
                conditions.append(self.model.location == filters["location"])
            if filters.get("domain"):
                conditions.append(self.model.domain == filters["domain"])
            if filters.get("salary_min") is not None:
                conditions.append(self.model.salary_min >= filters["salary_min"])
            if filters.get("salary_max") is not None:
                conditions.append(self.model.salary_max <= filters["salary_max"])
            
            if conditions:
                query = query.where(*conditions)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def add_mandatory_skill(
        self, db: AsyncSession, job_id: int, skill_data: dict
    ) -> JobMandatorySkill:
        """Add mandatory skill to job"""
        # Check if skill already exists for this job
        existing_skill = await db.execute(
            select(JobMandatorySkill).where(
                JobMandatorySkill.job_id == job_id,
                JobMandatorySkill.skill == skill_data.get("skill")
            )
        )
        if existing_skill.scalar_one_or_none():
            from core.exceptions import ValidationException
            raise ValidationException(f"Skill '{skill_data.get('skill')}' already exists for this job")

        # Create new mandatory skill
        new_skill = JobMandatorySkill(
            job_id=job_id,
            skill=skill_data.get("skill"),
            min_experience=skill_data.get("min_experience", 0)
        )
        db.add(new_skill)
        await db.commit()
        await db.refresh(new_skill)
        return new_skill

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

    async def get_active_jobs(self, db: AsyncSession, limit: int = 50) -> List[Job]:
        """Get jobs with mandatory skills"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_jobs_without_applicants(self, db: AsyncSession, days_threshold: int = 7, limit: int = 20) -> List[Job]:
        """Get jobs with no applicants in the last N days"""
        from datetime import datetime, timedelta
        from db.crud.application import application as application_crud
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        # Get all jobs created before cutoff date
        result = await db.execute(
            select(self.model).where(self.model.created_at <= cutoff_date).limit(limit)
        )
        jobs = result.scalars().all()
        
        # Filter jobs that have no applications
        jobs_without_applicants = []
        for job in jobs:
            applications = await application_crud.get_by_job(db, job.id)
            if not applications:
                jobs_without_applicants.append(job)
        
        return jobs_without_applicants

    async def get_performance_metrics(self, db: AsyncSession, days_back: int = 30) -> dict:
        """Get job performance metrics"""
        from datetime import datetime, timedelta
        from db.crud.application import application as application_crud
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get jobs created in the time period
        result = await db.execute(
            select(self.model).where(self.model.created_at >= cutoff_date)
        )
        jobs = result.scalars().all()
        
        total_jobs = len(jobs)
        total_applications = 0
        jobs_with_applications = 0
        
        for job in jobs:
            applications = await application_crud.get_by_job(db, job.id)
            if applications:
                total_applications += len(applications)
                jobs_with_applications += 1
        
        avg_applications_per_job = total_applications / total_jobs if total_jobs > 0 else 0
        application_rate = jobs_with_applications / total_jobs if total_jobs > 0 else 0
        
        return {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "jobs_with_applications": jobs_with_applications,
            "avg_applications_per_job": avg_applications_per_job,
            "application_rate": application_rate,
            "days_analyzed": days_back
        }

    async def count_recent(self, db: AsyncSession, days_back: int = 7) -> int:
        """Get count of recent jobs"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        result = await db.execute(
            select(self.model).where(self.model.created_at >= cutoff_date)
        )
        return len(result.scalars().all())


job = CRUDJob(Job)