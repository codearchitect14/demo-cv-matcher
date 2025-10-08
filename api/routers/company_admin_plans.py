"""
Company Admin Subscription Plan Management

Allows company admins to:
- View available offer plans
- Request a subscription plan (goes to PENDING for super admin approval)
- View their current subscription status
"""

from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import List, Optional
import logging
from pydantic import BaseModel
from datetime import datetime

from middleware.recruiter_auth import get_current_recruiter, RecruiterContext
from config.connection_pool import global_pool

router = APIRouter()
logger = logging.getLogger(__name__)


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


class PlanRequestRequest(BaseModel):
    offer_plan_id: str


@router.get("/available-plans", response_model=List[OfferPlanResponse])
async def get_available_plans(
    current_recruiter: RecruiterContext = Depends(get_current_recruiter)
):
    """Get all available offer plans for company admin to choose from"""
    try:
        # Only company admins can view plans
        if not current_recruiter.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only company admins can view subscription plans"
            )
        
        async with global_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id::text, plan_name, price, job_post_limit, recruiter_limit,
                       candidate_views, analytics_level, support_level, status
                FROM offer_plans
                WHERE status = 'Active'
                ORDER BY price ASC
                """
            )
            
            plans = [OfferPlanResponse(**dict(row)) for row in rows]
            logger.info(f"[PLANS] Company admin {current_recruiter.email} viewed {len(plans)} available plans")
            return plans
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching available plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch available plans"
        )


@router.get("/my-subscription")
async def get_my_subscription(
    current_recruiter: RecruiterContext = Depends(get_current_recruiter)
):
    """Get current company's subscription status"""
    try:
        if not current_recruiter.company_id:
            return {"message": "No company associated with this account"}
        
        async with global_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    cs.id::text,
                    cs.company_id,
                    cs.offer_plan_id::text,
                    op.plan_name,
                    op.price,
                    op.job_post_limit,
                    op.recruiter_limit,
                    op.candidate_views,
                    op.analytics_level,
                    op.support_level,
                    cs.status,
                    cs.subscribed_at,
                    cs.expires_at
                FROM company_subscriptions cs
                JOIN offer_plans op ON cs.offer_plan_id = op.id
                WHERE cs.company_id = $1
                ORDER BY cs.subscribed_at DESC
                LIMIT 1
                """,
                current_recruiter.company_id
            )
            
            if row:
                return dict(row)
            else:
                return {"message": "No active subscription"}
                
    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription"
        )


@router.post("/request-plan")
async def request_subscription_plan(
    request_data: PlanRequestRequest,
    current_recruiter: RecruiterContext = Depends(get_current_recruiter)
):
    """
    Company admin requests a subscription plan
    Status will be PENDING until super admin approves
    """
    try:
        # Only company admins can request plans
        if not current_recruiter.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only company admins can request subscription plans"
            )
        
        if not current_recruiter.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No company associated with this account"
            )
        
        async with global_pool.acquire() as conn:
            # Get company details
            company = await conn.fetchrow(
                "SELECT id, name FROM companies WHERE id = $1",
                current_recruiter.company_id
            )
            
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Get plan details
            plan = await conn.fetchrow(
                "SELECT id, plan_name, price FROM offer_plans WHERE id = $1 AND status = 'Active'",
                request_data.offer_plan_id
            )
            
            if not plan:
                raise HTTPException(status_code=404, detail="Offer plan not found or inactive")
            
            # Check if company already has a subscription
            existing = await conn.fetchrow(
                "SELECT id, status FROM company_subscriptions WHERE company_id = $1",
                current_recruiter.company_id
            )
            
            if existing:
                # Update existing subscription to PENDING
                row = await conn.fetchrow(
                    """
                    UPDATE company_subscriptions
                    SET offer_plan_id = $1, status = 'Pending', updated_at = NOW()
                    WHERE company_id = $2
                    RETURNING id::text, status
                    """,
                    request_data.offer_plan_id,
                    current_recruiter.company_id
                )
                message = "Subscription plan updated. Awaiting super admin approval."
            else:
                # Create new subscription with PENDING status
                row = await conn.fetchrow(
                    """
                    INSERT INTO company_subscriptions (company_id, offer_plan_id, status, subscribed_at)
                    VALUES ($1, $2, 'Pending', NOW())
                    RETURNING id::text, status
                    """,
                    current_recruiter.company_id,
                    request_data.offer_plan_id
                )
                message = "Subscription plan requested. Awaiting super admin approval."
            
            # Send notification email to super admin
            try:
                from services.email_service import email_service
                
                await email_service.send_plan_request_to_super_admin(
                    company_name=company['name'],
                    admin_name=current_recruiter.name,
                    admin_email=current_recruiter.email,
                    plan_name=plan['plan_name'],
                    plan_price=float(plan['price']),
                    company_id=company['id']
                )
                logger.info(f"✅ Plan request notification sent to super admin for {company['name']}")
            except Exception as email_error:
                logger.error(f"❌ Failed to send super admin notification: {email_error}")
            
            return {
                "message": message,
                "subscription_id": row['id'],
                "status": row['status'],
                "plan_name": plan['plan_name'],
                "requires_approval": True
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting subscription plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request subscription plan"
        )

