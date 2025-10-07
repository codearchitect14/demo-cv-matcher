from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import Optional, List
import logging
from pydantic import BaseModel
from datetime import datetime

from api.routers.super_admin_fast import super_admin_required, SuperAdminProfile
from config.connection_pool import global_pool

router = APIRouter()
logger = logging.getLogger(__name__)


class CompanySubscriptionResponse(BaseModel):
    id: str
    company_id: int
    company_name: str
    offer_plan_id: str
    plan_name: str
    plan_price: float
    status: str
    subscribed_at: str
    expires_at: Optional[str]


class AssignSubscriptionRequest(BaseModel):
    company_id: int
    offer_plan_id: str
    status: str = "Active"
    expires_at: Optional[str] = None


@router.get("/company-subscriptions", response_model=List[CompanySubscriptionResponse])
async def list_company_subscriptions(_: SuperAdminProfile = Depends(super_admin_required)):
    """List all company subscriptions with plan details"""
    async with global_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                cs.id::text as id,
                cs.company_id,
                c.name as company_name,
                cs.offer_plan_id::text as offer_plan_id,
                op.plan_name,
                op.price as plan_price,
                cs.status,
                cs.subscribed_at::text,
                cs.expires_at::text
            FROM company_subscriptions cs
            JOIN companies c ON cs.company_id = c.id
            JOIN offer_plans op ON cs.offer_plan_id = op.id
            ORDER BY c.name
            """
        )
        return [CompanySubscriptionResponse(**dict(row)) for row in rows]


@router.get("/companies/{company_id}/subscription")
async def get_company_subscription(company_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    """Get subscription details for a specific company"""
    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                cs.id::text as id,
                cs.company_id,
                c.name as company_name,
                cs.offer_plan_id::text as offer_plan_id,
                op.plan_name,
                op.price as plan_price,
                op.job_post_limit,
                op.recruiter_limit,
                op.candidate_views,
                op.analytics_level,
                op.support_level,
                cs.status,
                cs.subscribed_at::text,
                cs.expires_at::text
            FROM company_subscriptions cs
            JOIN companies c ON cs.company_id = c.id
            JOIN offer_plans op ON cs.offer_plan_id = op.id
            WHERE cs.company_id = $1
            """,
            company_id
        )
        
        if not row:
            return {"message": "No subscription found for this company"}
        
        return dict(row)


@router.post("/company-subscriptions")
async def assign_subscription(
    subscription_data: AssignSubscriptionRequest,
    _: SuperAdminProfile = Depends(super_admin_required)
):
    """Assign or update a company's subscription plan and send confirmation emails"""
    
    async with global_pool.acquire() as conn:
        # Check if company exists
        company = await conn.fetchrow("SELECT id, name FROM companies WHERE id = $1", subscription_data.company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Check if offer plan exists
        offer_plan = await conn.fetchrow("SELECT id, plan_name, price FROM offer_plans WHERE id = $1", subscription_data.offer_plan_id)
        if not offer_plan:
            raise HTTPException(status_code=404, detail="Offer plan not found")
        
        # Get company admin details for email
        admin_details = await conn.fetchrow(
            """
            SELECT full_name, email FROM recruiters 
            WHERE company_id = $1 AND LOWER(role) = 'admin'
            LIMIT 1
            """,
            subscription_data.company_id
        )
        
        # Check if company already has a subscription
        existing_subscription = await conn.fetchrow(
            "SELECT id FROM company_subscriptions WHERE company_id = $1",
            subscription_data.company_id
        )
        
        if existing_subscription:
            # Update existing subscription
            row = await conn.fetchrow(
                """
                UPDATE company_subscriptions
                SET offer_plan_id = $1, status = $2, expires_at = $3, updated_at = NOW()
                WHERE company_id = $4
                RETURNING id::text as id, company_id, status
                """,
                subscription_data.offer_plan_id,
                subscription_data.status,
                subscription_data.expires_at,
                subscription_data.company_id
            )
            message = f"Updated subscription for {company['name']} to {offer_plan['plan_name']}"
        else:
            # Create new subscription
            row = await conn.fetchrow(
                """
                INSERT INTO company_subscriptions (company_id, offer_plan_id, status, expires_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id::text as id, company_id, status
                """,
                subscription_data.company_id,
                subscription_data.offer_plan_id,
                subscription_data.status,
                subscription_data.expires_at
            )
            message = f"Assigned {offer_plan['plan_name']} plan to {company['name']}"
        
        # Send plan selection confirmation emails
        if admin_details and admin_details['email']:
            try:
                from services.email_service import email_service
                await email_service.send_plan_selection_confirmation(
                    company_name=company['name'],
                    admin_name=admin_details['full_name'] or 'Admin',
                    admin_email=admin_details['email'],
                    plan_name=offer_plan['plan_name'],
                    plan_price=float(offer_plan['price']),
                    super_admin_notify=True  # Also notify super admin
                )
                logger.info(f"✅ Plan selection emails sent for {company['name']}")
            except Exception as e:
                logger.error(f"❌ Failed to send plan selection emails: {e}")
        
        return {
            "message": message,
            "subscription": dict(row)
        }


@router.put("/company-subscriptions/{subscription_id}/status")
async def update_subscription_status(
    subscription_id: str,
    status_data: dict = Body(...),
    _: SuperAdminProfile = Depends(super_admin_required)
):
    """Update subscription status"""
    
    new_status = status_data.get("status")
    if not new_status or new_status not in ['Active', 'Inactive', 'Expired', 'Cancelled']:
        raise HTTPException(
            status_code=400,
            detail="status must be one of: Active, Inactive, Expired, Cancelled"
        )
    
    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE company_subscriptions
            SET status = $1, updated_at = NOW()
            WHERE id = $2
            RETURNING id::text as id, company_id, status
            """,
            new_status,
            subscription_id
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return {
            "message": f"Subscription status updated to {new_status}",
            "subscription": dict(row)
        }


@router.put("/company-subscriptions/{subscription_id}/approve")
async def approve_subscription_request(
    subscription_id: str,
    _: SuperAdminProfile = Depends(super_admin_required)
):
    """Approve a pending subscription request from company admin"""
    
    async with global_pool.acquire() as conn:
        # Get subscription details
        subscription = await conn.fetchrow(
            """
            SELECT cs.id, cs.company_id, cs.status,
                   c.name as company_name,
                   op.plan_name, op.price,
                   r.full_name as admin_name, r.email as admin_email
            FROM company_subscriptions cs
            JOIN companies c ON cs.company_id = c.id
            JOIN offer_plans op ON cs.offer_plan_id = op.id
            LEFT JOIN recruiters r ON c.id = r.company_id AND LOWER(r.role) = 'admin'
            WHERE cs.id = $1 AND cs.status = 'Pending'
            LIMIT 1
            """,
            subscription_id
        )
        
        if not subscription:
            raise HTTPException(
                status_code=404, 
                detail="Subscription not found or not pending"
            )
        
        # Update status to Active
        await conn.execute(
            """
            UPDATE company_subscriptions
            SET status = 'Active', updated_at = NOW()
            WHERE id = $1
            """,
            subscription_id
        )
        
        # Send approval email to company admin
        if subscription['admin_email']:
            try:
                from services.email_service import email_service
                
                await email_service.send_plan_approval_to_company_admin(
                    company_name=subscription['company_name'],
                    admin_name=subscription['admin_name'] or 'Admin',
                    admin_email=subscription['admin_email'],
                    plan_name=subscription['plan_name'],
                    plan_price=float(subscription['price'])
                )
                logger.info(f"✅ Plan approval email sent to {subscription['admin_email']}")
            except Exception as e:
                logger.error(f"❌ Failed to send approval email: {e}")
        
        return {
            "message": f"Subscription approved for {subscription['company_name']}",
            "plan": subscription['plan_name'],
            "status": "Active"
        }


@router.put("/company-subscriptions/{subscription_id}/reject")
async def reject_subscription_request(
    subscription_id: str,
    rejection_data: dict = Body(...),
    _: SuperAdminProfile = Depends(super_admin_required)
):
    """Reject a pending subscription request from company admin"""
    
    reason = rejection_data.get("reason", "")
    
    async with global_pool.acquire() as conn:
        # Get subscription details
        subscription = await conn.fetchrow(
            """
            SELECT cs.id, cs.company_id, cs.status,
                   c.name as company_name,
                   op.plan_name,
                   r.full_name as admin_name, r.email as admin_email
            FROM company_subscriptions cs
            JOIN companies c ON cs.company_id = c.id
            JOIN offer_plans op ON cs.offer_plan_id = op.id
            LEFT JOIN recruiters r ON c.id = r.company_id AND LOWER(r.role) = 'admin'
            WHERE cs.id = $1 AND cs.status = 'Pending'
            LIMIT 1
            """,
            subscription_id
        )
        
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="Subscription not found or not pending"
            )
        
        # Update status to Rejected or delete it
        await conn.execute(
            """
            DELETE FROM company_subscriptions WHERE id = $1
            """,
            subscription_id
        )
        
        # Send rejection email to company admin
        if subscription['admin_email']:
            try:
                from services.email_service import email_service
                
                await email_service.send_plan_rejection_to_company_admin(
                    company_name=subscription['company_name'],
                    admin_name=subscription['admin_name'] or 'Admin',
                    admin_email=subscription['admin_email'],
                    plan_name=subscription['plan_name'],
                    rejection_reason=reason
                )
                logger.info(f"✅ Plan rejection email sent to {subscription['admin_email']}")
            except Exception as e:
                logger.error(f"❌ Failed to send rejection email: {e}")
        
        return {
            "message": f"Subscription request rejected for {subscription['company_name']}",
            "plan": subscription['plan_name']
        }


@router.delete("/company-subscriptions/{subscription_id}")
async def cancel_subscription(subscription_id: str, _: SuperAdminProfile = Depends(super_admin_required)):
    """Cancel a company subscription"""
    
    async with global_pool.acquire() as conn:
        # Get subscription details before deletion
        subscription = await conn.fetchrow(
            """
            SELECT cs.id, c.name as company_name, op.plan_name
            FROM company_subscriptions cs
            JOIN companies c ON cs.company_id = c.id
            JOIN offer_plans op ON cs.offer_plan_id = op.id
            WHERE cs.id = $1
            """,
            subscription_id
        )
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Delete the subscription
        result = await conn.execute(
            "DELETE FROM company_subscriptions WHERE id = $1",
            subscription_id
        )
        
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return {
            "message": f"Cancelled {subscription['plan_name']} subscription for {subscription['company_name']}"
        }
