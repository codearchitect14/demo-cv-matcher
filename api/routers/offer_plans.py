from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import Optional, List
import logging
from pydantic import BaseModel

from api.routers.super_admin_fast import super_admin_required, SuperAdminProfile
from config.connection_pool import global_pool

router = APIRouter()
logger = logging.getLogger(__name__)


class OfferPlanCreate(BaseModel):
    plan_name: str
    price: float
    job_post_limit: Optional[int] = None  # None means unlimited
    recruiter_limit: int
    candidate_views: Optional[int] = None  # None means unlimited
    analytics_level: str  # Basic, Standard, Advanced
    support_level: str
    status: str = "Active"  # Active, Inactive


class OfferPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    price: Optional[float] = None
    job_post_limit: Optional[int] = None
    recruiter_limit: Optional[int] = None
    candidate_views: Optional[int] = None
    analytics_level: Optional[str] = None
    support_level: Optional[str] = None
    status: Optional[str] = None


class OfferPlanResponse(BaseModel):
    id: str
    plan_name: str
    price: float
    job_post_limit: Optional[int]
    recruiter_limit: int
    candidate_views: Optional[int]
    analytics_level: str
    support_level: str
    status: str
    created_at: str
    updated_at: str


@router.get("/offer-plans", response_model=List[OfferPlanResponse])
async def list_offer_plans(_: SuperAdminProfile = Depends(super_admin_required)):
    """List all offer plans"""
    async with global_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id::text as id, plan_name, price, job_post_limit, recruiter_limit,
                   candidate_views, analytics_level, support_level, status,
                   created_at::text, updated_at::text
            FROM offer_plans
            ORDER BY price DESC
            """
        )
        return [OfferPlanResponse(**dict(row)) for row in rows]


@router.post("/offer-plans", response_model=OfferPlanResponse)
async def create_offer_plan(
    plan_data: OfferPlanCreate, 
    _: SuperAdminProfile = Depends(super_admin_required)
):
    """Create a new offer plan"""
    
    # Validate analytics level
    if plan_data.analytics_level not in ['Basic', 'Standard', 'Advanced']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="analytics_level must be one of: Basic, Standard, Advanced"
        )
    
    # Validate status
    if plan_data.status not in ['Active', 'Inactive']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be one of: Active, Inactive"
        )
    
    async with global_pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO offer_plans (
                    plan_name, price, job_post_limit, recruiter_limit,
                    candidate_views, analytics_level, support_level, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id::text as id, plan_name, price, job_post_limit, recruiter_limit,
                         candidate_views, analytics_level, support_level, status,
                         created_at::text, updated_at::text
                """,
                plan_data.plan_name,
                plan_data.price,
                plan_data.job_post_limit,
                plan_data.recruiter_limit,
                plan_data.candidate_views,
                plan_data.analytics_level,
                plan_data.support_level,
                plan_data.status
            )
            return OfferPlanResponse(**dict(row))
            
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan name already exists"
            )


@router.get("/offer-plans/{plan_id}", response_model=OfferPlanResponse)
async def get_offer_plan(plan_id: str, _: SuperAdminProfile = Depends(super_admin_required)):
    """Get a specific offer plan by ID"""
    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id::text as id, plan_name, price, job_post_limit, recruiter_limit,
                   candidate_views, analytics_level, support_level, status,
                   created_at::text, updated_at::text
            FROM offer_plans
            WHERE id = $1
            """,
            plan_id
        )
        
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        
        return OfferPlanResponse(**dict(row))


@router.put("/offer-plans/{plan_id}", response_model=OfferPlanResponse)
async def update_offer_plan(
    plan_id: str,
    plan_data: OfferPlanUpdate,
    _: SuperAdminProfile = Depends(super_admin_required)
):
    """Update an offer plan"""
    
    # Validate analytics level if provided
    if plan_data.analytics_level and plan_data.analytics_level not in ['Basic', 'Standard', 'Advanced']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="analytics_level must be one of: Basic, Standard, Advanced"
        )
    
    # Validate status if provided
    if plan_data.status and plan_data.status not in ['Active', 'Inactive']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be one of: Active, Inactive"
        )
    
    async with global_pool.acquire() as conn:
        # Build dynamic update query
        fields = []
        params = []
        idx = 1
        
        for field, value in plan_data.dict(exclude_unset=True).items():
            if value is not None:
                idx += 1
                fields.append(f"{field} = ${idx}")
                params.append(value)
        
        if not fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Always update updated_at
        fields.append("updated_at = NOW()")
        
        query = f"""
            UPDATE offer_plans
            SET {', '.join(fields)}
            WHERE id = $1
            RETURNING id::text as id, plan_name, price, job_post_limit, recruiter_limit,
                     candidate_views, analytics_level, support_level, status,
                     created_at::text, updated_at::text
        """
        
        try:
            row = await conn.fetchrow(query, plan_id, *params)
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
            
            return OfferPlanResponse(**dict(row))
            
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan name already exists"
            )


@router.delete("/offer-plans/{plan_id}")
async def delete_offer_plan(plan_id: str, _: SuperAdminProfile = Depends(super_admin_required)):
    """Delete an offer plan"""
    async with global_pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM offer_plans WHERE id = $1",
            plan_id
        )
        
        if result == "DELETE 0":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        
        return {"message": "Plan deleted successfully"}


@router.put("/offer-plans/{plan_id}/toggle-status")
async def toggle_plan_status(plan_id: str, _: SuperAdminProfile = Depends(super_admin_required)):
    """Toggle plan status between Active and Inactive"""
    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE offer_plans
            SET status = CASE 
                WHEN status = 'Active' THEN 'Inactive'
                ELSE 'Active'
            END,
            updated_at = NOW()
            WHERE id = $1
            RETURNING id::text as id, plan_name, status
            """,
            plan_id
        )
        
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        
        return {
            "message": f"Plan {row['plan_name']} status updated to {row['status']}",
            "plan": dict(row)
        }
