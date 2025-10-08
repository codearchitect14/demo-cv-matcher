from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import Optional, List, Dict, Any
import logging

from models.recruiter import Recruiter
from models.job import Job
from models.application import Application
from db.crud.base import CRUDBase
from schemas.recruiter import RecruiterCreate, RecruiterUpdate

logger = logging.getLogger(__name__)

class CRUDRecruiter(CRUDBase[Recruiter, RecruiterCreate, RecruiterUpdate]):
    """CRUD operations for Recruiter model"""
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Recruiter]:
        """Get recruiter by email"""
        result = await db.execute(
            select(Recruiter).where(Recruiter.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_with_stats(self, db: AsyncSession, recruiter_id: int) -> Optional[Dict[str, Any]]:
        """Get recruiter with job and application statistics"""
        # Get recruiter
        result = await db.execute(
            select(Recruiter).where(Recruiter.id == recruiter_id)
        )
        recruiter = result.scalar_one_or_none()
        
        if not recruiter:
            return None
        
        # Get job statistics
        jobs_result = await db.execute(
            select(func.count(Job.id)).where(Job.recruiter_id == recruiter_id)
        )
        total_jobs = jobs_result.scalar()
        
        active_jobs_result = await db.execute(
            select(func.count(Job.id)).where(
                Job.recruiter_id == recruiter_id,
                Job.is_active == True
            )
        )
        active_jobs = active_jobs_result.scalar()
        
        # Get application statistics
        applications_result = await db.execute(
            select(func.count(Application.id)).where(
                Application.recruiter_id == recruiter_id
            )
        )
        total_applications = applications_result.scalar()
        
        return {
            "recruiter": recruiter,
            "total_jobs_posted": total_jobs,
            "active_jobs": active_jobs,
            "total_applications_received": total_applications
        }
    
    async def get_by_domain(self, db: AsyncSession, domain: str) -> List[Recruiter]:
        """Get recruiters by domain"""
        result = await db.execute(
            select(Recruiter).where(Recruiter.domain == domain)
        )
        return result.scalars().all()
    
    async def get_by_company_size(self, db: AsyncSession, company_size: str) -> List[Recruiter]:
        """Get recruiters by company size"""
        result = await db.execute(
            select(Recruiter).where(Recruiter.company_size == company_size)
        )
        return result.scalars().all()
    
    async def search_recruiters(
        self, 
        db: AsyncSession, 
        domain: Optional[str] = None,
        company_size: Optional[str] = None,
        company_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Recruiter]:
        """Search recruiters with filters"""
        query = select(Recruiter)
        
        if domain:
            query = query.where(Recruiter.domain == domain)
        if company_size:
            query = query.where(Recruiter.company_size == company_size)
        if company_name:
            query = query.where(Recruiter.company_name.ilike(f"%{company_name}%"))
        
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_recruiter_jobs(
        self, 
        db: AsyncSession, 
        recruiter_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Job]:
        """Get all jobs posted by a recruiter"""
        result = await db.execute(
            select(Job)
            .where(Job.recruiter_id == recruiter_id)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def get_recruiter_applications(
        self, 
        db: AsyncSession, 
        recruiter_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Application]:
        """Get all applications for jobs posted by a recruiter"""
        result = await db.execute(
            select(Application)
            .join(Job, Application.job_id == Job.id)
            .where(Job.recruiter_id == recruiter_id)
            .order_by(Application.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    # ===== ADMIN METHODS =====
    
    async def get_all_with_filters(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role_filter: Optional[str] = None,
        is_active: Optional[bool] = None,
        company_id: Optional[int] = None
    ) -> List[Recruiter]:
        """Get all recruiters with filters - Company Admin only"""
        query = select(Recruiter)
        
        # Apply company filter for isolation
        if company_id is not None:
            query = query.where(Recruiter.company_id == company_id)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Recruiter.full_name.ilike(search_term)) |
                (Recruiter.email.ilike(search_term)) |
                (Recruiter.company_name.ilike(search_term))
            )
        
        if role_filter:
            query = query.where(Recruiter.role == role_filter)
        
        if is_active is not None:
            query = query.where(Recruiter.is_active == is_active)
        
        # Order and paginate
        query = query.order_by(Recruiter.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count_active_jobs(self, db: AsyncSession, recruiter_id: int) -> int:
        """Count active jobs for a recruiter"""
        result = await db.execute(
            select(func.count(Job.id)).where(
                Job.recruiter_id == recruiter_id,
                Job.is_active == True
            )
        )
        return result.scalar() or 0

# Create recruiter CRUD instance
recruiter = CRUDRecruiter(Recruiter) 