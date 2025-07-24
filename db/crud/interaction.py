# File: db/crud/interaction.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.crud.base import CRUDBase
from models.interaction import InteractionLog, InteractionTypeEnum
from schemas.interaction import InteractionLogCreate


class CRUDInteractionLog(CRUDBase[InteractionLog, InteractionLogCreate, None]):
    async def get_by_candidate(self, db: AsyncSession, candidate_id: int) -> List[InteractionLog]:
        """Get interactions by candidate"""
        result = await db.execute(
            select(self.model).where(self.model.candidate_id == candidate_id)
        )
        return result.scalars().all()

    async def get_by_job(self, db: AsyncSession, job_id: int) -> List[InteractionLog]:
        """Get interactions by job"""
        result = await db.execute(
            select(self.model).where(self.model.job_id == job_id)
        )
        return result.scalars().all()

    async def get_by_type(self, db: AsyncSession, interaction_type: InteractionTypeEnum) -> List[InteractionLog]:
        """Get interactions by type"""
        result = await db.execute(
            select(self.model).where(self.model.interaction_type == interaction_type)
        )
        return result.scalars().all()


interaction_log = CRUDInteractionLog(InteractionLog)