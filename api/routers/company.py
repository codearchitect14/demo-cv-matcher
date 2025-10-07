from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from config.database import get_db_session
from db.crud.company import company
from schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyStats
from middleware.recruiter_auth import get_current_recruiter, RecruiterContext

router = APIRouter(tags=["Company"])
logger = logging.getLogger(__name__)

# ===== COMPANY MANAGEMENT ENDPOINTS =====

@router.get("/test")
async def test_company_endpoint():
    """Test endpoint to verify company router is working"""
    return {"message": "Company router is working", "status": "success"}

@router.get("/public/info")
async def get_public_company_info():
    """Public endpoint to get basic company information for testing"""
    return {
        "id": 1,
        "name": "Test Company",
        "domain": "IT",
        "description": "Test company for development",
        "is_active": True,
        "status": "ACTIVE",
        "subscription_plan": "basic",
        "max_recruiters": 10,
        "max_jobs": 100,
        "contact_email": None,
        "contact_phone": None,
        "address": None,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }

@router.get("/public/stats")
async def get_public_company_stats():
    """Public endpoint to get basic company statistics for testing"""
    return {
        "id": 1,
        "name": "Test Company",
        "total_recruiters": 5,
        "active_recruiters": 4,
        "total_jobs": 25,
        "active_jobs": 20,
        "total_applications": 150,
        "pending_applications": 30,
        "subscription_plan": "basic",
        "max_recruiters": 10,
        "max_jobs": 100
    }

@router.get("/", response_model=List[CompanyResponse])
async def get_all_companies(
    current_user: RecruiterContext = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by company name or domain"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """Get all companies - Super Admin only"""
    try:
        # Only super admins can see all companies
        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required"
            )
        
        companies = await company.get_all_with_filters(
            db, 
            skip=skip, 
            limit=limit, 
            search=search, 
            is_active=is_active
        )
        return companies
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all companies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get companies"
        )

@router.post("/", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    current_user: RecruiterContext = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new company - Super Admin only"""
    try:
        # Only super admins can create companies
        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required"
            )
        
        # Check if company name already exists
        existing_company = await company.get_by_name(db, company_data.name)
        if existing_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name already exists"
            )
        
        # Create company
        new_company = await company.create(db, obj_in=company_data.dict())
        
        logger.info(f"Super admin created new company: {new_company.name}")
        return new_company
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company"
        )

@router.get("/my-company", response_model=CompanyResponse)
async def get_my_company():
    """Get company information - Public endpoint for testing"""
    try:
        # Return default company data for public access
        return {
            "id": 1,
            "name": "Your Company",
            "domain": "IT",
            "description": "Your company for job management",
            "is_active": True,
            "status": "ACTIVE",
            "subscription_plan": "premium",
            "max_recruiters": 20,
            "max_jobs": 200,
            "contact_email": None,
            "contact_phone": None,
            "address": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
    except Exception as e:
        logger.error(f"Error getting company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company"
        )

@router.get("/my-company/stats", response_model=CompanyStats)
async def get_company_stats():
    """Get company statistics - Public endpoint for testing"""
    try:
        # Return default company stats for public access
        return {
            "id": 1,
            "name": "Your Company",
            "total_recruiters": 8,
            "active_recruiters": 7,
            "total_jobs": 45,
            "active_jobs": 38,
            "total_applications": 320,
            "pending_applications": 65,
            "subscription_plan": "premium",
            "max_recruiters": 20,
            "max_jobs": 200
        }
        
    except Exception as e:
        logger.error(f"Error getting company stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company statistics"
        )

@router.put("/my-company", response_model=CompanyResponse)
async def update_my_company(
    company_data: CompanyUpdate,
    current_user: RecruiterContext = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session)
):
    """Update current user's company - Company Admin only"""
    try:
        # Only company admins can update company info
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company admin access required"
            )
        
        # Update company
        update_data = company_data.dict(exclude_unset=True)
        updated_company = await company.update(
            db, 
            db_obj_id=current_user.company_id, 
            obj_in=update_data
        )
        
        logger.info(f"Company admin updated company: {updated_company.name}")
        return updated_company
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )

@router.get("/my-company/recruiters", response_model=List[dict])
async def get_company_recruiters(
    current_user: RecruiterContext = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name or email"),
    role_filter: Optional[str] = Query(None, description="Filter by role: admin, recruiter"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """Get recruiters for current user's company"""
    try:
        # Only company admins can see all recruiters
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company admin access required"
            )
        
        recruiters = await company.get_company_recruiters(
            db, 
            current_user.company_id,
            skip=skip,
            limit=limit,
            search=search,
            role_filter=role_filter,
            is_active=is_active
        )
        
        # Convert to response format
        return [
            {
                "id": r.id,
                "full_name": r.full_name,
                "email": r.email,
                "phone_number": r.phone_number,
                "role": r.role,
                "is_active": r.is_active,
                "email_verified": r.email_verified,
                "created_at": r.created_at,
                "updated_at": r.updated_at
            }
            for r in recruiters
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company recruiters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company recruiters"
        )

@router.get("/my-company/limits")
async def get_company_limits(
    current_user: RecruiterContext = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current company's limits and usage"""
    try:
        limits = await company.check_company_limits(db, current_user.company_id)
        return limits
        
    except Exception as e:
        logger.error(f"Error getting company limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company limits"
        )

# ===== SUPER ADMIN ENDPOINTS =====

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company_super_admin(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: RecruiterContext = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session)
):
    """Update any company - Super Admin only"""
    try:
        # Only super admins can update any company
        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required"
            )
        
        # Update company
        update_data = company_data.dict(exclude_unset=True)
        updated_company = await company.update(
            db, 
            db_obj_id=company_id, 
            obj_in=update_data
        )
        
        logger.info(f"Super admin updated company: {updated_company.name}")
        return updated_company
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )

@router.delete("/{company_id}")
async def delete_company_super_admin(
    company_id: int,
    current_user: RecruiterContext = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a company - Super Admin only"""
    try:
        # Only super admins can delete companies
        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required"
            )
        
        # Get company to check if it exists
        existing_company = await company.get(db, company_id)
        if not existing_company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Check if company has active recruiters or jobs
        limits = await company.check_company_limits(db, company_id)
        if limits["current_recruiters"] > 0 or limits["current_jobs"] > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete company with {limits['current_recruiters']} recruiters and {limits['current_jobs']} jobs. Please remove all recruiters and jobs first."
            )
        
        # Delete company
        await company.remove(db, company_id)
        
        logger.info(f"Super admin deleted company: {existing_company.name}")
        return {"message": "Company deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete company"
        )
