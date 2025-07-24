from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.crud.base import CRUDBase
from models.application import Application, ApplicationStatusEnum
from schemas.application import ApplicationCreate, ApplicationUpdate


class CRUDApplication(CRUDBase[Application, ApplicationCreate, ApplicationUpdate]):
    async def get_by_candidate(self, db: AsyncSession, candidate_id: int) -> List[Application]:
        """Get applications by candidate"""
        result = await db.execute(
            select(self.model).where(self.model.candidate_id == candidate_id)
        )
        return result.scalars().all()

    async def get_by_job(self, db: AsyncSession, job_id: int) -> List[Application]:
        """Get applications by job"""
        result = await db.execute(
            select(self.model).where(self.model.job_id == job_id)
        )
        return result.scalars().all()

    async def get_by_status(self, db: AsyncSession, status: ApplicationStatusEnum) -> List[Application]:
        """Get applications by status"""
        result = await db.execute(
            select(self.model).where(self.model.status == status)
        )
        return result.scalars().all()

    async def get_existing(
        self, db: AsyncSession, job_id: int, candidate_id: int
    ) -> Optional[Application]:
        """Check if application already exists"""
        result = await db.execute(
            select(self.model).where(
                self.model.job_id == job_id,
                self.model.candidate_id == candidate_id
            )
        )
        return result.scalar_one_or_none()


application = CRUDApplication(Application)
