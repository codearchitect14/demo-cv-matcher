# File: db/crud/interaction.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.crud.base import CRUDBase
from models.interaction import InteractionLog, InteractionTypeEnum
from schemas.interaction import InteractionLogCreate


class CRUDInteractionLog(CRUDBase[InteractionLog, InteractionLogCreate, None]):
    async def log_interaction(self, db: AsyncSession, obj_in: InteractionLogCreate) -> InteractionLog:
        interaction = InteractionLog(
            user_id=obj_in.user_id,
            job_id=obj_in.job_id,
            interaction_type=obj_in.interaction_type
        )
        db.add(interaction)
        await db.commit()
        await db.refresh(interaction)
        return interaction

    async def get_by_candidate(self, db: AsyncSession, candidate_id: int) -> List[InteractionLog]:
        """Get interactions by candidate"""
        result = await db.execute(
            select(self.model).where(self.model.user_id == candidate_id)
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


interaction = CRUDInteractionLog(InteractionLog)