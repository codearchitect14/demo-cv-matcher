from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.crud.base import CRUDBase
from models.application import Application, ApplicationStatusEnum
from schemas.application import ApplicationCreate, ApplicationUpdate


class CRUDApplication(CRUDBase[Application, ApplicationCreate, ApplicationUpdate]):
    async def get_by_candidate_id(
        self, db: AsyncSession, candidate_id: int, skip: int = 0, limit: int = 100
    ) -> List[Application]:
        """Get applications by candidate ID with pagination and job details"""
        from sqlalchemy.orm import selectinload
        
        query = select(self.model).options(
            selectinload(self.model.job)
        ).where(self.model.candidate_id == candidate_id)
        query = query.offset(skip).limit(limit).order_by(self.model.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_candidate(self, db: AsyncSession, candidate_id: int, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Application]:
        """Get applications by candidate with optional filtering"""
        query = select(self.model).where(self.model.candidate_id == candidate_id)
        
        if status:
            query = query.where(self.model.status == status)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_job(self, db: AsyncSession, job_id: int, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Application]:
        """Get applications by job with optional filtering"""
        query = select(self.model).where(self.model.job_id == job_id)
        
        if status:
            query = query.where(self.model.status == status)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_status(self, db: AsyncSession, status: ApplicationStatusEnum) -> List[Application]:
        """Get applications by status"""
        result = await db.execute(
            select(self.model).where(self.model.status == status)
        )
        return result.scalars().all()

    async def get_by_candidate_and_job(
        self, db: AsyncSession, candidate_id: int, job_id: int
    ) -> Optional[Application]:
        """Get application by candidate and job (check if already applied)"""
        result = await db.execute(
            select(self.model).where(
                self.model.candidate_id == candidate_id,
                self.model.job_id == job_id
            )
        )
        return result.scalar_one_or_none()

    async def get_existing(
        self, db: AsyncSession, job_id: int, candidate_id: int
    ) -> Optional[Application]:
        """Check if application already exists (alias for get_by_candidate_and_job)"""
        return await self.get_by_candidate_and_job(db, candidate_id, job_id)

    async def count(self, db: AsyncSession) -> int:
        """Get total number of applications"""
        result = await db.execute(select(self.model))
        return len(result.scalars().all())

    async def count_recent(self, db: AsyncSession, days_back: int = 30) -> int:
        """Get count of recent applications"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        result = await db.execute(
            select(self.model).where(self.model.created_at >= cutoff_date)
        )
        return len(result.scalars().all())

    async def get_status_distribution(self, db: AsyncSession) -> dict:
        """Get distribution of application statuses"""
        result = await db.execute(select(self.model))
        applications = result.scalars().all()
        
        distribution = {}
        for app in applications:
            status = app.status.value if hasattr(app.status, 'value') else str(app.status)
            distribution[status] = distribution.get(status, 0) + 1
        
        return distribution


application = CRUDApplication(Application)
