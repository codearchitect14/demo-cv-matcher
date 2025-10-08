from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from models.job_skill import JobSkill
from db.crud.base import CRUDBase

class CRUDJobSkill(CRUDBase[JobSkill, Dict[str, Any], Dict[str, Any]]):
    """CRUD operations for JobSkill model"""
    
    async def get_by_job_id(self, db: AsyncSession, job_id: int) -> List[JobSkill]:
        """Get all skills for a specific job"""
        result = await db.execute(
            select(JobSkill).where(JobSkill.job_id == job_id)
        )
        return result.scalars().all()
    
    async def get_by_skill_id(self, db: AsyncSession, skill_id: int) -> List[JobSkill]:
        """Get all jobs that require a specific skill"""
        result = await db.execute(
            select(JobSkill).where(JobSkill.skill_id == skill_id)
        )
        return result.scalars().all()
    
    async def get_by_priority(self, db: AsyncSession, job_id: int, priority: str) -> List[JobSkill]:
        """Get skills by priority for a specific job"""
        result = await db.execute(
            select(JobSkill).where(
                and_(JobSkill.job_id == job_id, JobSkill.priority == priority)
            )
        )
        return result.scalars().all()
    
    async def get_required_skills(self, db: AsyncSession, job_id: int) -> List[JobSkill]:
        """Get required skills for a specific job"""
        return await self.get_by_priority(db, job_id, "required")
    
    async def get_preferred_skills(self, db: AsyncSession, job_id: int) -> List[JobSkill]:
        """Get preferred skills for a specific job"""
        return await self.get_by_priority(db, job_id, "preferred")
    
    async def get_nice_to_have_skills(self, db: AsyncSession, job_id: int) -> List[JobSkill]:
        """Get nice-to-have skills for a specific job"""
        return await self.get_by_priority(db, job_id, "nice_to_have")
    
    async def delete_by_job_id(self, db: AsyncSession, job_id: int) -> bool:
        """Delete all skills for a specific job"""
        result = await db.execute(
            select(JobSkill).where(JobSkill.job_id == job_id)
        )
        skills = result.scalars().all()
        for skill in skills:
            await db.delete(skill)
        await db.commit()
        return True

# Create job_skill CRUD instance
job_skill = CRUDJobSkill(JobSkill) 