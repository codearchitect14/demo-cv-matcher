from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import Optional, List, Dict, Any
import logging

from models.company import Company
from models.recruiter import Recruiter
from models.job import Job
from models.application import Application
from db.crud.base import CRUDBase
from schemas.company import CompanyCreate, CompanyUpdate

logger = logging.getLogger(__name__)

class CRUDCompany(CRUDBase[Company, CompanyCreate, CompanyUpdate]):
    """CRUD operations for Company model"""
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Company]:
        """Get company by name"""
        result = await db.execute(
            select(Company).where(Company.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_all_with_filters(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Company]:
        """Get all companies with filters - Super Admin only"""
        query = select(Company)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Company.name.ilike(search_term)) |
                (Company.domain.ilike(search_term))
            )
        
        if is_active is not None:
            query = query.where(Company.is_active == is_active)
        
        # Order and paginate
        query = query.order_by(Company.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_stats(self, db: AsyncSession, company_id: int) -> Optional[Dict[str, Any]]:
        """Get company with statistics"""
        # Get company
        result = await db.execute(
            select(Company).where(Company.id == company_id)
        )
        company = result.scalar_one_or_none()
        
        if not company:
            return None
        
        # Get recruiter statistics
        recruiters_result = await db.execute(
            select(func.count(Recruiter.id)).where(Recruiter.company_id == company_id)
        )
        total_recruiters = recruiters_result.scalar() or 0
        
        active_recruiters_result = await db.execute(
            select(func.count(Recruiter.id)).where(
                Recruiter.company_id == company_id,
                Recruiter.is_active == True
            )
        )
        active_recruiters = active_recruiters_result.scalar() or 0
        
        # Get job statistics
        jobs_result = await db.execute(
            select(func.count(Job.id)).where(Job.company_id == company_id)
        )
        total_jobs = jobs_result.scalar() or 0
        
        active_jobs_result = await db.execute(
            select(func.count(Job.id)).where(
                Job.company_id == company_id,
                Job.is_active == True
            )
        )
        active_jobs = active_jobs_result.scalar() or 0
        
        # Get application statistics
        applications_result = await db.execute(
            select(func.count(Application.id))
            .join(Job, Application.job_id == Job.id)
            .where(Job.company_id == company_id)
        )
        total_applications = applications_result.scalar() or 0
        
        pending_applications_result = await db.execute(
            select(func.count(Application.id))
            .join(Job, Application.job_id == Job.id)
            .where(
                Job.company_id == company_id,
                Application.status == "PENDING"
            )
        )
        pending_applications = pending_applications_result.scalar() or 0
        
        return {
            "company": company,
            "total_recruiters": total_recruiters,
            "active_recruiters": active_recruiters,
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "total_applications": total_applications,
            "pending_applications": pending_applications
        }
    
    async def get_company_recruiters(
        self, 
        db: AsyncSession, 
        company_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role_filter: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Recruiter]:
        """Get recruiters for a specific company with filters"""
        query = select(Recruiter).where(Recruiter.company_id == company_id)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Recruiter.full_name.ilike(search_term)) |
                (Recruiter.email.ilike(search_term))
            )
        
        if role_filter:
            query = query.where(Recruiter.role == role_filter)
        
        if is_active is not None:
            query = query.where(Recruiter.is_active == is_active)
        
        # Order and paginate
        query = query.order_by(Recruiter.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_company_jobs(
        self, 
        db: AsyncSession, 
        company_id: int,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Job]:
        """Get jobs for a specific company"""
        query = select(Job).where(Job.company_id == company_id)
        
        if is_active is not None:
            query = query.where(Job.is_active == is_active)
        
        query = query.order_by(Job.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def check_company_limits(self, db: AsyncSession, company_id: int) -> Dict[str, bool]:
        """Check if company has reached its limits"""
        company = await self.get(db, company_id)
        if not company:
            return {"valid": False, "reason": "Company not found"}
        
        # Check recruiter limit
        recruiters_count = await db.execute(
            select(func.count(Recruiter.id)).where(Recruiter.company_id == company_id)
        )
        recruiters_count = recruiters_count.scalar() or 0
        
        # Check job limit
        jobs_count = await db.execute(
            select(func.count(Job.id)).where(
                Job.company_id == company_id,
                Job.is_active == True
            )
        )
        jobs_count = jobs_count.scalar() or 0
        
        return {
            "valid": True,
            "recruiters_limit_reached": recruiters_count >= company.max_recruiters,
            "jobs_limit_reached": jobs_count >= company.max_jobs,
            "current_recruiters": recruiters_count,
            "current_jobs": jobs_count,
            "max_recruiters": company.max_recruiters,
            "max_jobs": company.max_jobs
        }

# Create company CRUD instance
company = CRUDCompany(Company)
