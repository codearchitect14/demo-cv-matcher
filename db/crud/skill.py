from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from models.skill import Skill
from db.crud.base import CRUDBase

class CRUDSkill(CRUDBase[Skill, Dict[str, Any], Dict[str, Any]]):
    """CRUD operations for Skill model"""
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Skill]:
        """Get skill by name"""
        result = await db.execute(
            select(Skill).where(Skill.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_category(self, db: AsyncSession, category: str) -> List[Skill]:
        """Get skills by category"""
        result = await db.execute(
            select(Skill).where(
                and_(Skill.category == category, Skill.is_active == True)
            )
        )
        return result.scalars().all()
    
    async def search_skills(self, db: AsyncSession, query: str, limit: int = 10) -> List[Skill]:
        """Search skills by name or description"""
        result = await db.execute(
            select(Skill).where(
                and_(
                    Skill.is_active == True,
                    (Skill.name.ilike(f"%{query}%") | Skill.description.ilike(f"%{query}%"))
                )
            ).limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_skills(self, db: AsyncSession, limit: int = 100) -> List[Skill]:
        """Get all active skills"""
        result = await db.execute(
            select(Skill).where(Skill.is_active == True).limit(limit)
        )
        return result.scalars().all()
    
    async def get_skill_hierarchy(self, db: AsyncSession, skill_id: int) -> List[Skill]:
        """Get skill hierarchy (parent and child skills)"""
        skill = await self.get(db, skill_id)
        if not skill:
            return []
        
        # Get parent skills
        parent_skills = []
        current_skill = skill
        while current_skill.parent_skill_id:
            parent = await self.get(db, current_skill.parent_skill_id)
            if parent:
                parent_skills.append(parent)
                current_skill = parent
            else:
                break
        
        # Get child skills
        child_skills = await self.get_by_parent(db, skill_id)
        
        return parent_skills + [skill] + child_skills
    
    async def get_by_parent(self, db: AsyncSession, parent_id: int) -> List[Skill]:
        """Get child skills by parent ID"""
        result = await db.execute(
            select(Skill).where(
                and_(Skill.parent_skill_id == parent_id, Skill.is_active == True)
            )
        )
        return result.scalars().all()

# Create skill CRUD instance
skill = CRUDSkill(Skill) 