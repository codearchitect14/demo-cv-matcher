from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from models.candidate_skill import CandidateSkill
from db.crud.base import CRUDBase

class CRUDCandidateSkill(CRUDBase[CandidateSkill, Dict[str, Any], Dict[str, Any]]):
    """CRUD operations for CandidateSkill model"""
    
    async def get_by_candidate_id(self, db: AsyncSession, candidate_id: int) -> List[CandidateSkill]:
        """Get all skills for a specific candidate"""
        result = await db.execute(
            select(CandidateSkill).where(CandidateSkill.candidate_id == candidate_id)
        )
        return result.scalars().all()
    
    async def get_by_skill_id(self, db: AsyncSession, skill_id: int) -> List[CandidateSkill]:
        """Get all candidates that have a specific skill"""
        result = await db.execute(
            select(CandidateSkill).where(CandidateSkill.skill_id == skill_id)
        )
        return result.scalars().all()
    
    async def get_by_proficiency_level(self, db: AsyncSession, candidate_id: int, level: str) -> List[CandidateSkill]:
        """Get skills by proficiency level for a specific candidate"""
        result = await db.execute(
            select(CandidateSkill).where(
                and_(CandidateSkill.candidate_id == candidate_id, CandidateSkill.proficiency_level == level)
            )
        )
        return result.scalars().all()
    
    async def get_experienced_candidates(self, db: AsyncSession, skill_id: int, min_years: float) -> List[CandidateSkill]:
        """Get candidates with minimum years of experience in a specific skill"""
        result = await db.execute(
            select(CandidateSkill).where(
                and_(
                    CandidateSkill.skill_id == skill_id,
                    CandidateSkill.years_experience >= min_years
                )
            )
        )
        return result.scalars().all()
    
    async def get_recent_skills(self, db: AsyncSession, candidate_id: int, days: int = 365) -> List[CandidateSkill]:
        """Get skills used within the last N days"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await db.execute(
            select(CandidateSkill).where(
                and_(
                    CandidateSkill.candidate_id == candidate_id,
                    CandidateSkill.last_used >= cutoff_date
                )
            )
        )
        return result.scalars().all()
    
    async def get_total_experience(self, db: AsyncSession, candidate_id: int) -> float:
        """Get total years of experience across all skills for a candidate"""
        result = await db.execute(
            select(CandidateSkill.years_experience).where(CandidateSkill.candidate_id == candidate_id)
        )
        experiences = result.scalars().all()
        return sum(experiences) if experiences else 0.0
    
    async def delete_by_candidate_id(self, db: AsyncSession, candidate_id: int) -> bool:
        """Delete all skills for a specific candidate"""
        result = await db.execute(
            select(CandidateSkill).where(CandidateSkill.candidate_id == candidate_id)
        )
        skills = result.scalars().all()
        for skill in skills:
            await db.delete(skill)
        await db.commit()
        return True

# Create candidate_skill CRUD instance
candidate_skill = CRUDCandidateSkill(CandidateSkill) 