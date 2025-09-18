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
from config.security import simulate_constant_time_verify
from middleware.rate_limiter import rate_limiter

router = APIRouter(tags=["Recruiter"])

logger = logging.getLogger(__name__)

# Lightweight asyncpg pool (initialized lazily)
_pool = None

async def _get_pool():
    global _pool
    if _pool is None:
        import os
        import asyncpg
        dsn = os.getenv('DATABASE_URL')
        if dsn and dsn.startswith('postgresql+asyncpg://'):
            dsn = dsn.replace('postgresql+asyncpg://', 'postgresql://', 1)
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=5,
            statement_cache_size=0,
            command_timeout=5
        )
    return _pool

async def _fetch_recruiter_by_email(email: str):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT id, full_name, email, password_hash, is_active, role
            FROM recruiters 
            WHERE email = $1
            """,
            email
        )

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
        
        # Set default company_id (for testing - should be 1)
        recruiter_dict["company_id"] = 1
        
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
    login_data: RecruiterLogin
):
    """Login recruiter - Optimized for performance with direct connection"""
    import time
    import asyncpg
    import asyncio
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    start_time = time.time()
    
    try:
        # Get recruiter by email using direct connection (working version)
        conn = None
        try:
            conn = await asyncpg.connect(
                os.getenv('DATABASE_URL'), 
                statement_cache_size=0,
                command_timeout=5
            )
            recruiter_obj = await conn.fetchrow("""
                SELECT id, full_name, email, password_hash, is_active, role
                FROM recruiters 
                WHERE email = $1
            """, login_data.email)
        finally:
            if conn:
                try:
                    await conn.close()
                except Exception as e:
                    logger.warning(f"Error closing recruiter login connection: {e}")
        if not recruiter_obj:
            # Burn comparable CPU to mitigate enumeration timing
            simulate_constant_time_verify()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password - this is the most expensive operation
        if not verify_password(login_data.password, recruiter_obj['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if recruiter is active (no additional DB query needed)
        if not recruiter_obj['is_active']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Create access token with proper email (not ID) as subject
        access_token = create_access_token(
            data={
                "sub": recruiter_obj['email'],  # Use email as subject for consistency
                "user_id": recruiter_obj['id'],
                "role": recruiter_obj['role'], 
                "type": "recruiter"
            }
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Recruiter logged in: {recruiter_obj['email']} (took {elapsed_time:.3f}s)")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": recruiter_obj['id'],
                "email": recruiter_obj['email'],
                "full_name": recruiter_obj['full_name'],
                "role": recruiter_obj['role'],
                "company_name": recruiter_obj.get('company_name', '')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error logging in recruiter: {e} (took {elapsed_time:.3f}s)")
        # Normalize backend errors to avoid leaking details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login temporarily unavailable. Please try again."
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

# ===== ADMIN ENDPOINTS FOR RECRUITER MANAGEMENT =====

@router.get("/admin/all", response_model=List[RecruiterResponse])
async def get_all_recruiters_admin(
    current_user: dict = Depends(lambda: {"id": 1, "role": "admin", "company_id": 1}),  # Placeholder
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    role_filter: Optional[str] = Query(None, description="Filter by role: admin, recruiter"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """Get all recruiters for current user's company - Company Admin only"""
    try:
        # TODO: Add proper admin authentication check
        # if current_user["role"] not in ["admin", "super_admin"]:
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Filter recruiters by company_id for company isolation
        recruiters = await recruiter.get_all_with_filters(
            db, 
            skip=skip, 
            limit=limit, 
            search=search, 
            role_filter=role_filter, 
            is_active=is_active,
            company_id=current_user.get("company_id")  # Add company filtering
        )
        return recruiters
        
    except Exception as e:
        logger.error(f"Error getting company recruiters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recruiters"
        )

@router.post("/admin/create", response_model=RecruiterResponse)
async def create_recruiter_admin(
    recruiter_data: RecruiterCreate,
    current_user: dict = Depends(lambda: {"id": 1, "role": "admin"}),  # Placeholder
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new recruiter - Admin only"""
    try:
        # TODO: Add proper admin authentication check
        # if current_user["role"] != "admin":
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
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
        
        # Set default company_id (for testing - should be 1)
        recruiter_dict["company_id"] = 1
        
        # Convert enum values to strings for SQLAlchemy
        if "domain" in recruiter_dict:
            recruiter_dict["domain"] = recruiter_dict["domain"].value
        if "company_size" in recruiter_dict:
            recruiter_dict["company_size"] = recruiter_dict["company_size"].value
        
        # Create recruiter
        new_recruiter = await recruiter.create(db, obj_in=recruiter_dict)
        
        logger.info(f"Admin created new recruiter: {new_recruiter.email}")
        return new_recruiter
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating recruiter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create recruiter"
        )

@router.put("/admin/{recruiter_id}", response_model=RecruiterResponse)
async def update_recruiter_admin(
    recruiter_id: int,
    recruiter_data: RecruiterUpdate,
    current_user: dict = Depends(lambda: {"id": 1, "role": "admin"}),  # Placeholder
    db: AsyncSession = Depends(get_db_session)
):
    """Update a recruiter - Admin only"""
    try:
        # TODO: Add proper admin authentication check
        # if current_user["role"] != "admin":
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Check if recruiter exists using global connection pool
        from config.connection_pool import global_pool
        
        existing_recruiter = await global_pool.fetchrow(
            "SELECT id FROM recruiters WHERE id = $1",
            recruiter_id
        )
        if not existing_recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found"
            )
        
        # Update recruiter using direct SQL for better performance and error handling
        update_data = recruiter_data.dict(exclude_unset=True)
        
        # Debug logging
        logger.info(f"Received update data: {update_data}")
        
        # Remove password_confirm if present
        if "password_confirm" in update_data:
            del update_data["password_confirm"]
        
        # Handle password update if provided
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = get_password_hash(update_data["password"])
            del update_data["password"]
        
        # Convert enum values to strings if they're enum objects
        if "domain" in update_data and hasattr(update_data["domain"], 'value'):
            update_data["domain"] = update_data["domain"].value
        if "company_size" in update_data and hasattr(update_data["company_size"], 'value'):
            update_data["company_size"] = update_data["company_size"].value
        
        # Debug logging after processing
        logger.info(f"Processed update data: {update_data}")
        
        # Use direct SQL update for better control (global_pool already imported above)
        
        # Build update query dynamically
        set_clauses = []
        params = [recruiter_id]
        param_count = 1
        
        for key, value in update_data.items():
            if value is not None:
                param_count += 1
                set_clauses.append(f"{key} = ${param_count}")
                params.append(value)
        
        if set_clauses:
            param_count += 1
            set_clauses.append(f"updated_at = NOW()")
            
            update_query = f"""
                UPDATE recruiters 
                SET {', '.join(set_clauses)}
                WHERE id = $1
                RETURNING id, full_name, email, phone_number, company_name, domain, 
                         company_size, role, is_active, email_verified, created_at, updated_at
            """
            
            updated_row = await global_pool.fetchrow(update_query, *params)
            
            if not updated_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recruiter not found"
                )
            
            # Convert to response format
            updated_recruiter = {
                "id": updated_row['id'],
                "full_name": updated_row['full_name'],
                "email": updated_row['email'],
                "phone_number": updated_row['phone_number'],
                "company_name": updated_row['company_name'],
                "domain": updated_row['domain'],
                "company_size": updated_row['company_size'],
                "role": updated_row['role'],
                "is_active": updated_row['is_active'],
                "email_verified": updated_row['email_verified'],
                "created_at": updated_row['created_at'].isoformat(),
                "updated_at": updated_row['updated_at'].isoformat()
            }
        else:
            # No fields to update - get current data
            current_row = await global_pool.fetchrow(
                "SELECT id, full_name, email, phone_number, company_name, domain, company_size, role, is_active, email_verified, created_at, updated_at FROM recruiters WHERE id = $1",
                recruiter_id
            )
            updated_recruiter = {
                "id": current_row['id'],
                "full_name": current_row['full_name'],
                "email": current_row['email'],
                "phone_number": current_row['phone_number'],
                "company_name": current_row['company_name'],
                "domain": current_row['domain'],
                "company_size": current_row['company_size'],
                "role": current_row['role'],
                "is_active": current_row['is_active'],
                "email_verified": current_row['email_verified'],
                "created_at": current_row['created_at'].isoformat(),
                "updated_at": current_row['updated_at'].isoformat()
            }
        
        logger.info(f"Admin updated recruiter: {updated_recruiter['email']} - Role changed to: {updated_recruiter['role']}")
        return updated_recruiter
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recruiter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update recruiter"
        )

@router.delete("/admin/{recruiter_id}")
async def delete_recruiter_admin(
    recruiter_id: int,
    current_user: dict = Depends(lambda: {"id": 1, "role": "admin"}),  # Placeholder
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a recruiter - Admin only"""
    try:
        # TODO: Add proper admin authentication check
        # if current_user["role"] != "admin":
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get existing recruiter
        existing_recruiter = await recruiter.get(db, recruiter_id)
        if not existing_recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found"
            )
        
        # Check if recruiter has active jobs
        active_jobs_count = await recruiter.count_active_jobs(db, recruiter_id)
        if active_jobs_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete recruiter with {active_jobs_count} active jobs. Please reassign or close jobs first."
            )
        
        # Delete recruiter
        await recruiter.remove(db, recruiter_id)
        
        logger.info(f"Admin deleted recruiter: {existing_recruiter.email}")
        return {"message": "Recruiter deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recruiter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete recruiter"
        )

@router.put("/admin/{recruiter_id}/toggle-status")
async def toggle_recruiter_status_admin(
    recruiter_id: int,
    current_user: dict = Depends(lambda: {"id": 1, "role": "admin"}),  # Placeholder
    db: AsyncSession = Depends(get_db_session)
):
    """Toggle recruiter active status - Admin only"""
    try:
        # TODO: Add proper admin authentication check
        # if current_user["role"] != "admin":
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get existing recruiter
        existing_recruiter = await recruiter.get(db, recruiter_id)
        if not existing_recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found"
            )
        
        # Toggle status
        new_status = not existing_recruiter.is_active
        updated_recruiter = await recruiter.update(
            db, 
            db_obj_id=recruiter_id, 
            obj_in={"is_active": new_status}
        )
        
        action = "activated" if new_status else "deactivated"
        logger.info(f"Admin {action} recruiter: {updated_recruiter.email}")
        
        return {
            "message": f"Recruiter {action} successfully",
            "recruiter": updated_recruiter
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling recruiter status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle recruiter status"
        ) 