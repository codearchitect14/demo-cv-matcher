from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
import logging

from schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyStats

router = APIRouter(tags=["Company Public"])
logger = logging.getLogger(__name__)

# ===== PUBLIC COMPANY ENDPOINTS (NO AUTHENTICATION) =====

@router.get("/my-company", response_model=CompanyResponse)
async def get_my_company():
    """Get current user's company information - Public for testing"""
    try:
        # Return default company data for testing
        return {
            "id": 1,
            "name": "Your Company",
            "domain": "IT",
            "description": "Your company for job management",
            "is_active": True,
            "subscription_plan": "premium",
            "max_recruiters": 20,
            "max_jobs": 200,
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
    """Get current user's company statistics - Public for testing"""
    try:
        # Return default company stats for testing
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
            detail="Failed to get company stats"
        )

@router.put("/my-company", response_model=CompanyResponse)
async def update_my_company(company_data: CompanyUpdate):
    """Update current user's company - Public for testing"""
    try:
        # Return updated company data for testing
        return {
            "id": 1,
            "name": company_data.name or "Your Company",
            "domain": company_data.domain or "IT",
            "description": company_data.description or "Your company for job management",
            "is_active": company_data.is_active if company_data.is_active is not None else True,
            "subscription_plan": company_data.subscription_plan or "premium",
            "max_recruiters": company_data.max_recruiters or 20,
            "max_jobs": company_data.max_jobs or 200,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
    except Exception as e:
        logger.error(f"Error updating company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )

@router.get("/my-company/recruiters", response_model=List[dict])
async def get_company_recruiters(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role_filter: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """Get recruiters for current user's company - Public for testing"""
    try:
        # Return sample recruiters for testing
        sample_recruiters = [
            {
                "id": 1,
                "full_name": "John Smith",
                "email": "john@company.com",
                "role": "admin",
                "is_active": True,
                "company_id": 1,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            },
            {
                "id": 2,
                "full_name": "Sarah Johnson",
                "email": "sarah@company.com",
                "role": "recruiter",
                "is_active": True,
                "company_id": 1,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            },
            {
                "id": 3,
                "full_name": "Mike Wilson",
                "email": "mike@company.com",
                "role": "recruiter",
                "is_active": False,
                "company_id": 1,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        ]
        
        # Apply filters
        filtered_recruiters = sample_recruiters
        
        if search:
            search_lower = search.lower()
            filtered_recruiters = [
                r for r in filtered_recruiters 
                if search_lower in r["full_name"].lower() or search_lower in r["email"].lower()
            ]
        
        if role_filter:
            filtered_recruiters = [r for r in filtered_recruiters if r["role"] == role_filter]
        
        if is_active is not None:
            filtered_recruiters = [r for r in filtered_recruiters if r["is_active"] == is_active]
        
        # Apply pagination
        return filtered_recruiters[skip:skip + limit]
        
    except Exception as e:
        logger.error(f"Error getting company recruiters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company recruiters"
        )

@router.get("/my-company/limits")
async def get_company_limits():
    """Get current company's limits and usage - Public for testing"""
    try:
        # Return sample limits for testing
        return {
            "valid": True,
            "recruiters_limit_reached": False,
            "jobs_limit_reached": False,
            "current_recruiters": 8,
            "current_jobs": 45,
            "max_recruiters": 20,
            "max_jobs": 200
        }
    except Exception as e:
        logger.error(f"Error getting company limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company limits"
        )



