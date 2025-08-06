from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from config.database import get_db_session
from db.crud.recruiter import recruiter
from schemas.recruiter import (
    RecruiterCreate, 
    RecruiterResponse, 
    RecruiterLogin, 
    RecruiterUpdate, 
    RecruiterProfile,
    CompanySize,
    Domain
)
from api.routers.auth import create_access_token, get_password_hash, verify_password
from middleware.rate_limiter import rate_limiter

router = APIRouter(tags=["Recruiter"])

logger = logging.getLogger(__name__)

@router.post("/register", response_model=RecruiterResponse)
async def register_recruiter(
    recruiter_data: RecruiterCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new recruiter"""
    try:
        # Check if email already exists
        existing_recruiter = await recruiter.get_by_email(db, recruiter_data.email)
        if existing_recruiter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(recruiter_data.password)
        
        # Create recruiter data
        recruiter_dict = recruiter_data.dict()
        recruiter_dict.pop("password")
        recruiter_dict.pop("password_confirm")
        recruiter_dict["password_hash"] = hashed_password
        
        # Convert enum values to strings for SQLAlchemy
        if "domain" in recruiter_dict:
            recruiter_dict["domain"] = recruiter_dict["domain"].value
        if "company_size" in recruiter_dict:
            recruiter_dict["company_size"] = recruiter_dict["company_size"].value
        
        # Create recruiter
        new_recruiter = await recruiter.create(db, obj_in=recruiter_dict)
        
        logger.info(f"New recruiter registered: {new_recruiter.email}")
        return new_recruiter
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering recruiter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register recruiter"
        )

@router.post("/login")
async def login_recruiter(
    login_data: RecruiterLogin,
    db: AsyncSession = Depends(get_db_session)
):
    """Login recruiter"""
    try:
        # Get recruiter by email
        recruiter_obj = await recruiter.get_by_email(db, login_data.email)
        if not recruiter_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, recruiter_obj.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if recruiter is active
        if not recruiter_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(recruiter_obj.id), "role": recruiter_obj.role, "type": "recruiter"}
        )
        
        logger.info(f"Recruiter logged in: {recruiter_obj.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": recruiter_obj.id,
                "email": recruiter_obj.email,
                "full_name": recruiter_obj.full_name,
                "role": recruiter_obj.role,
                "company_name": recruiter_obj.company_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in recruiter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login"
        )

@router.get("/profile", response_model=RecruiterProfile)
async def get_recruiter_profile(
    current_user: dict = Depends(lambda: {"id": 1, "role": "recruiter"}),  # Placeholder
    db: AsyncSession = Depends(get_db_session)
):
    """Get recruiter profile with statistics"""
    try:
        recruiter_id = current_user["id"]
        
        # Get recruiter with stats
        recruiter_data = await recruiter.get_with_stats(db, recruiter_id)
        if not recruiter_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found"
            )
        
        recruiter_obj = recruiter_data["recruiter"]
        
        return RecruiterProfile(
            id=recruiter_obj.id,
            full_name=recruiter_obj.full_name,
            email=recruiter_obj.email,
            phone_number=recruiter_obj.phone_number,
            company_name=recruiter_obj.company_name,
            domain=recruiter_obj.domain,
            company_size=recruiter_obj.company_size,
            company_description=recruiter_obj.company_description,
            role=recruiter_obj.role,
            is_active=recruiter_obj.is_active,
            email_verified=recruiter_obj.email_verified,
            total_jobs_posted=recruiter_data["total_jobs_posted"],
            total_applications_received=recruiter_data["total_applications_received"],
            active_jobs=recruiter_data["active_jobs"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recruiter profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )

@router.put("/profile", response_model=RecruiterResponse)
async def update_recruiter_profile(
    profile_data: RecruiterUpdate,
    current_user: dict = Depends(lambda: {"id": 1, "role": "recruiter"}),  # Placeholder
    db: AsyncSession = Depends(get_db_session)
):
    """Update recruiter profile"""
    try:
        recruiter_id = current_user["id"]
        
        # Update recruiter
        updated_recruiter = await recruiter.update(
            db, 
            db_obj_id=recruiter_id, 
            obj_in=profile_data.dict(exclude_unset=True)
        )
        
        if not updated_recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found"
            )
        
        logger.info(f"Recruiter profile updated: {updated_recruiter.email}")
        return updated_recruiter
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recruiter profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.get("/domains")
async def get_domains():
    """Get available domains"""
    return [{"value": domain.value, "label": domain.value} for domain in Domain]

@router.get("/company-sizes")
async def get_company_sizes():
    """Get available company sizes"""
    return [{"value": size.value, "label": size.value} for size in CompanySize]

@router.get("/jobs")
async def get_recruiter_jobs(
    current_user: dict = Depends(lambda: {"id": 1, "role": "recruiter"}),  # Placeholder
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get all jobs posted by the recruiter"""
    try:
        recruiter_id = current_user["id"]
        jobs = await recruiter.get_recruiter_jobs(db, recruiter_id, limit, offset)
        return jobs
        
    except Exception as e:
        logger.error(f"Error getting recruiter jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get jobs"
        )

@router.get("/applications")
async def get_recruiter_applications(
    current_user: dict = Depends(lambda: {"id": 1, "role": "recruiter"}),  # Placeholder
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get all applications for jobs posted by the recruiter"""
    try:
        recruiter_id = current_user["id"]
        applications = await recruiter.get_recruiter_applications(db, recruiter_id, limit, offset)
        return applications
        
    except Exception as e:
        logger.error(f"Error getting recruiter applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get applications"
        ) 