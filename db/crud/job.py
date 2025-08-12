# File: db/crud/job.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from sqlalchemy.orm import selectinload, joinedload
from models.job import Job, JobMandatorySkill
from models.base import BaseModel
from schemas.job import JobCreate, JobUpdate
from db.crud.base import CRUDBase
import logging

logger = logging.getLogger(__name__)

class CRUDJob(CRUDBase[Job, JobCreate, JobUpdate]):
    """Optimized CRUD operations for jobs with eager loading and bulk operations"""
    
    async def get_with_skills(self, db: AsyncSession, id: int) -> Optional[Job]:
        """Get job with mandatory skills using eager loading"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_with_mandatory_skills(self, db: AsyncSession, id: int) -> Optional[Job]:
        """Get job with mandatory skills (alias for get_with_skills)"""
        return await self.get_with_skills(db, id)

    async def get_multiple_with_skills(self, db: AsyncSession, job_ids: List[int]) -> List[Job]:
        """Get multiple jobs with skills in a single query - eliminates N+1 problem"""
        if not job_ids:
            return []
        
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .where(self.model.id.in_(job_ids))
        )
        return result.scalars().unique().all()

    async def get_by_domain(self, db: AsyncSession, domain: str) -> List[Job]:
        """Get jobs by domain with eager loading"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .where(self.model.domain == domain)
        )
        return result.scalars().all()

    async def get_by_location(self, db: AsyncSession, location: str) -> List[Job]:
        """Get jobs by location with eager loading"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .where(self.model.location == location)
        )
        return result.scalars().all()

    async def get_by_recruiter(self, db: AsyncSession, recruiter_id: int) -> List[Job]:
        """Get jobs by recruiter ID with eager loading"""
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
        """Get jobs within salary range with eager loading"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .where(
                self.model.salary_min >= min_salary,
                self.model.salary_max <= max_salary
            )
        )
        return result.scalars().all()

    async def get_multi_with_filters(
        self, db: AsyncSession, filters: dict = None, skip: int = 0, limit: int = 100
    ) -> List[Job]:
        """Get multiple jobs with filters and eager loading"""
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
        
        query = query.offset(skip).limit(limit).order_by(desc(self.model.created_at))
        result = await db.execute(query)
        return result.scalars().unique().all()

    async def bulk_create_with_skills(
        self, 
        db: AsyncSession, 
        jobs_data: List[Dict[str, Any]]
    ) -> List[Job]:
        """Bulk create jobs with skills in optimized batches"""
        created_jobs = []
        
        for job_data in jobs_data:
            skills_data = job_data.pop('mandatory_skills', [])
            job = Job(**job_data)
            db.add(job)
            await db.flush()  # Get the job ID
            
            # Add skills in batch
            for skill_data in skills_data:
                skill = JobMandatorySkill(
                    job_id=job.id,
                    skill=skill_data['skill'],
                    min_experience=skill_data.get('min_experience', 1)
                )
                db.add(skill)
            
            created_jobs.append(job)
        
        await db.commit()
        return created_jobs

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
            raise ValidationException(f"Skill {skill_data.get('skill')} already exists for job {job_id}")
        
        skill = JobMandatorySkill(
            job_id=job_id,
            skill=skill_data.get("skill"),
            min_experience=skill_data.get("min_experience", 1)
        )
        db.add(skill)
        await db.commit()
        await db.refresh(skill)
        return skill

    async def bulk_add_skills(
        self, 
        db: AsyncSession, 
        job_id: int, 
        skills_data: List[Dict[str, Any]]
    ) -> List[JobMandatorySkill]:
        """Bulk add skills to a job"""
        skills = []
        for skill_data in skills_data:
            skill = JobMandatorySkill(
                job_id=job_id,
                skill=skill_data.get("skill"),
                min_experience=skill_data.get("min_experience", 1)
            )
            skills.append(skill)
            db.add(skill)
        
        await db.commit()
        return skills

    async def create_with_skills(self, db: AsyncSession, obj_in: JobCreate) -> Job:
        """Create job with skills in a single transaction"""
        job_data = obj_in.dict()
        skills_data = job_data.pop('mandatory_skills', [])
        
        job = Job(**job_data)
        db.add(job)
        await db.flush()  # Get the job ID
        
        # Add skills
        for skill_data in skills_data:
            skill = JobMandatorySkill(
                job_id=job.id,
                skill=skill_data.get("skill"),
                min_experience=skill_data.get("min_experience", 1)
            )
            db.add(skill)
        
        await db.commit()
        await db.refresh(job)
        return job

    async def get_active_jobs(self, db: AsyncSession, limit: int = 50) -> List[Job]:
        """Get active jobs with eager loading"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .where(self.model.is_active == True)
            .order_by(desc(self.model.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_jobs_without_applicants(
        self, db: AsyncSession, days_threshold: int = 7, limit: int = 20
    ) -> List[Job]:
        """Get jobs without recent applicants"""
        from datetime import datetime, timedelta
        from models.application import Application
        
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        # Subquery to get jobs with recent applications
        recent_applications = (
            select(Application.job_id)
            .where(Application.created_at >= threshold_date)
            .distinct()
        )
        
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.mandatory_skills))
            .where(
                and_(
                    self.model.is_active == True,
                    ~self.model.id.in_(recent_applications)
                )
            )
            .order_by(desc(self.model.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_performance_metrics(self, db: AsyncSession, days_back: int = 30) -> dict:
        """Get job performance metrics with optimized queries"""
        from datetime import datetime, timedelta
        from models.application import Application
        
        start_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get total jobs created
        total_jobs_result = await db.execute(
            select(func.count(self.model.id))
            .where(self.model.created_at >= start_date)
        )
        total_jobs = total_jobs_result.scalar()
        
        # Get jobs with applications
        jobs_with_apps_result = await db.execute(
            select(func.count(func.distinct(self.model.id)))
            .join(Application, self.model.id == Application.job_id)
            .where(self.model.created_at >= start_date)
        )
        jobs_with_apps = jobs_with_apps_result.scalar()
        
        # Get average applications per job
        avg_apps_result = await db.execute(
            select(func.avg(func.count(Application.id)))
            .select_from(self.model)
            .join(Application, self.model.id == Application.job_id)
            .where(self.model.created_at >= start_date)
            .group_by(self.model.id)
        )
        avg_apps = avg_apps_result.scalar() or 0
        
        return {
            "total_jobs": total_jobs,
            "jobs_with_applications": jobs_with_apps,
            "average_applications_per_job": float(avg_apps),
            "application_rate": (jobs_with_apps / total_jobs * 100) if total_jobs > 0 else 0
        }

    async def count_recent(self, db: AsyncSession, days_back: int = 7) -> int:
        """Count recent jobs with optimized query"""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days_back)
        result = await db.execute(
            select(func.count(self.model.id))
            .where(self.model.created_at >= start_date)
        )
        return result.scalar()

    async def get_with_skills_raw_sql(self, db: AsyncSession, id: int) -> Optional[Dict]:
        """Get job with mandatory skills using raw SQL to avoid prepared statements"""
        try:
            # Use raw SQL to avoid prepared statements
            result = await db.execute(text("""
                SELECT j.*, jms.skill, jms.min_experience, jms.id as skill_id
                FROM jobs j
                LEFT JOIN job_mandatory_skills jms ON j.id = jms.job_id
                WHERE j.id = :job_id
            """), {"job_id": id})
            
            rows = result.fetchall()
            if not rows:
                return None
            
            # Build job object manually
            job_data = dict(rows[0])
            mandatory_skills = []
            
            for row in rows:
                if row.skill:
                    mandatory_skills.append({
                        "id": row.skill_id,
                        "skill": row.skill,
                        "min_experience": row.min_experience,
                        "job_id": row.id
                    })
            
            job_data["mandatory_skills"] = mandatory_skills
            return job_data
            
        except Exception as e:
            logger.error(f"Error in get_with_skills_raw_sql: {e}")
            return None

    async def get_multiple_with_skills_raw_sql(self, db: AsyncSession, job_ids: List[int]) -> List[Dict]:
        """Get multiple jobs with skills using raw SQL to avoid prepared statements"""
        if not job_ids:
            return []
        
        try:
            # Use raw SQL to avoid prepared statements
            placeholders = ",".join([f":id_{i}" for i in range(len(job_ids))])
            params = {f"id_{i}": job_id for i, job_id in enumerate(job_ids)}
            
            result = await db.execute(text(f"""
                SELECT j.*, jms.skill, jms.min_experience, jms.id as skill_id
                FROM jobs j
                LEFT JOIN job_mandatory_skills jms ON j.id = jms.job_id
                WHERE j.id IN ({placeholders})
                ORDER BY j.created_at DESC
            """), params)
            
            rows = result.fetchall()
            
            # Group by job
            jobs = {}
            for row in rows:
                job_id = row.id
                if job_id not in jobs:
                    jobs[job_id] = dict(row)
                    jobs[job_id]["mandatory_skills"] = []
                
                if row.skill:
                    jobs[job_id]["mandatory_skills"].append({
                        "id": row.skill_id,
                        "skill": row.skill,
                        "min_experience": row.min_experience,
                        "job_id": job_id
                    })
            
            return list(jobs.values())
            
        except Exception as e:
            logger.error(f"Error in get_multiple_with_skills_raw_sql: {e}")
            return []

# Create CRUD instance
job_crud = CRUDJob(Job)
job = job_crud  # Maintain backward compatibility