from fastapi import APIRouter, HTTPException, Depends, status, Body, Request
from typing import Optional
import logging
import os
import asyncpg
from datetime import timedelta

from config.security import create_access_token, verify_password, verify_token
from config.connection_pool import global_pool
from pydantic import BaseModel, EmailStr

router = APIRouter()
logger = logging.getLogger(__name__)


class SuperAdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class SuperAdminProfile(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool


class OverviewResponse(BaseModel):
    companies: int
    recruiters: int
    candidates: int
    jobs: int
    applications: int


async def super_admin_required(request: Request) -> SuperAdminProfile:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = auth_header.split(" ")[1]
    token_data = verify_token(token)
    if token_data is None or (token_data.role or "").lower() != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")

    # Load profile from DB (id/email)
    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id::text as id, email, full_name, is_active
            FROM super_admins
            WHERE email = $1
            """,
            token_data.email,
        )
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not found")
        return SuperAdminProfile(
            id=row["id"], email=row["email"], full_name=row["full_name"], is_active=row["is_active"]
        )


# Simple in-memory rate limiter for login attempts (per email)
_login_attempts = {}


@router.post("/login")
async def super_admin_login(payload: SuperAdminLoginRequest):
    email = payload.email.lower().strip()

    # Basic rate limiting per email
    attempts = _login_attempts.get(email, 0)
    if attempts >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts. Try later.")

    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id::text as id, email, password_hash, full_name, is_active
            FROM super_admins
            WHERE email = $1
            """,
            email,
        )
        if not row:
            _login_attempts[email] = attempts + 1
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

        if not verify_password(payload.password, row["password_hash"]):
            _login_attempts[email] = attempts + 1
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # Success: clear attempts
        if email in _login_attempts:
            del _login_attempts[email]

        # Shorter expiry for super admin (30 minutes default)
        expires = timedelta(minutes=int(os.getenv("SUPER_ADMIN_ACCESS_EXPIRE_MINUTES", "30")))
        token = create_access_token(
            data={"sub": row["email"], "user_id": str(row["id"]), "role": "super_admin"},
            expires_delta=expires,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": row["id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "role": "super_admin",
            },
        }


@router.get("/me", response_model=SuperAdminProfile)
async def get_super_admin_me(current_user: SuperAdminProfile = Depends(super_admin_required)):
    return current_user


@router.get("/overview", response_model=OverviewResponse)
async def super_admin_overview(_: SuperAdminProfile = Depends(super_admin_required)):
    async with global_pool.acquire() as conn:
        # Get pending companies count and total companies
        row = await conn.fetchrow(
            """
            SELECT 
              COALESCE((SELECT COUNT(*) FROM companies WHERE status = 'PENDING'), 0) AS pending_companies,
              COALESCE((SELECT COUNT(*) FROM companies), 0) AS total_companies,
              COALESCE((SELECT COUNT(*) FROM recruiters), 0) AS recruiters,
              COALESCE((SELECT COUNT(*) FROM candidates), 0) AS candidates,
              COALESCE((SELECT COUNT(*) FROM jobs), 0) AS jobs,
              COALESCE((SELECT COUNT(*) FROM applications), 0) AS applications
            """
        )
        return OverviewResponse(
            companies=row["pending_companies"],  # Show pending companies count
            recruiters=row["recruiters"],
            candidates=row["candidates"],
            jobs=row["jobs"],
            applications=row["applications"],
        )


@router.get("/companies")
async def list_companies(
    limit: int = 20, 
    offset: int = 0, 
    status: Optional[str] = None,
    _: SuperAdminProfile = Depends(super_admin_required)
):
    async with global_pool.acquire() as conn:
        # Build query with optional status filter
        where_clause = ""
        params = [limit, offset]
        
        if status and status.lower() != "all":
            where_clause = "WHERE status = $3"
            params.append(status.upper())
        
        query = f"""
            SELECT c.id, c.name, c.domain, c.description, c.subscription_plan, 
                   c.status, c.created_at,
                   COUNT(DISTINCT r.id) as admin_count,
                   COUNT(DISTINCT j.id) as jobs_count,
                   COUNT(DISTINCT a.id) as applications_count,
                   COUNT(DISTINCT cand.id) as candidates_count,
                   cs.status as subscription_status,
                   op.plan_name as subscribed_plan_name,
                   op.price as subscribed_plan_price
            FROM companies c
            LEFT JOIN recruiters r ON c.id = r.company_id AND LOWER(r.role) = 'admin'
            LEFT JOIN jobs j ON c.id = j.company_id
            LEFT JOIN applications a ON j.id = a.job_id
            LEFT JOIN candidates cand ON a.candidate_id = cand.id
            LEFT JOIN company_subscriptions cs ON c.id = cs.company_id
            LEFT JOIN offer_plans op ON cs.offer_plan_id = op.id
            {where_clause}
            GROUP BY c.id, c.name, c.domain, c.description, c.subscription_plan, c.status, c.created_at,
                     cs.status, op.plan_name, op.price
            ORDER BY c.created_at DESC
            LIMIT $1 OFFSET $2
        """
        
        rows = await conn.fetch(query, *params)
        return {"items": [dict(r) for r in rows]}


@router.get("/admins")
async def list_admins(limit: int = 20, offset: int = 0, _: SuperAdminProfile = Depends(super_admin_required)):
    async with global_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, email, full_name, role, is_active, created_at
            FROM recruiters
            WHERE LOWER(role) = 'admin'
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset,
        )
        return {"items": [dict(r) for r in rows]}


@router.post("/companies")
async def create_company(payload: dict = Body(...), _: SuperAdminProfile = Depends(super_admin_required)):
    name = str(payload.get("name", "")).strip()
    domain = str(payload.get("domain", "")).strip()
    description = str(payload.get("description", "")).strip()
    subscription_plan = str(payload.get("subscription_plan", "basic"))
    is_active = bool(payload.get("is_active", True))
    if not name or not domain:
        raise HTTPException(status_code=400, detail="name and domain are required")

    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO companies (name, domain, description, subscription_plan, is_active)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, domain, description, subscription_plan, is_active, created_at
            """,
            name, domain, description, subscription_plan, is_active,
        )
        return dict(row)


@router.put("/companies/{company_id}")
async def update_company(company_id: int, payload: dict = Body(...), _: SuperAdminProfile = Depends(super_admin_required)):
    fields = []
    params = []
    idx = 1
    for key in ["name", "domain", "description", "subscription_plan", "is_active"]:
        if key in payload:
            idx += 1
            fields.append(f"{key} = ${idx}")
            params.append(payload[key])
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""
            UPDATE companies
            SET {', '.join(fields)}, updated_at = now()
            WHERE id = $1
            RETURNING id, name, domain, description, subscription_plan, is_active, updated_at
            """,
            company_id, *params,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Company not found")
        return dict(row)


@router.put("/companies/{company_id}/approve")
async def approve_company(company_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    """Approve a pending company"""
    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE companies 
            SET status = 'ACTIVE', updated_at = now()
            WHERE id = $1 AND status = 'PENDING'
            RETURNING id, name, status
            """,
            company_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Company not found or not pending")
        return {"message": "Company approved successfully", "company": dict(row)}


@router.put("/companies/{company_id}/reject")
async def reject_company(company_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    """Reject a pending company"""
    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE companies 
            SET status = 'REJECTED', updated_at = now()
            WHERE id = $1 AND status = 'PENDING'
            RETURNING id, name, status
            """,
            company_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Company not found or not pending")
        return {"message": "Company rejected", "company": dict(row)}


@router.put("/companies/{company_id}/suspend")
async def suspend_company(company_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    """Suspend an active company"""
    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE companies 
            SET status = 'SUSPENDED', updated_at = now()
            WHERE id = $1 AND status = 'ACTIVE'
            RETURNING id, name, status
            """,
            company_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Company not found or not active")
        return {"message": "Company suspended", "company": dict(row)}


@router.put("/companies/{company_id}/activate")
async def activate_company(company_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    """Activate a suspended company"""
    async with global_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE companies 
            SET status = 'ACTIVE', updated_at = now()
            WHERE id = $1 AND status = 'SUSPENDED'
            RETURNING id, name, status
            """,
            company_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Company not found or not suspended")
        return {"message": "Company activated", "company": dict(row)}


@router.get("/companies/{company_id}/details")
async def get_company_details(company_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    """Get company details with admin information (privacy-compliant)"""
    async with global_pool.acquire() as conn:
        # Get company basic info with admin details
        company_row = await conn.fetchrow(
            """
            SELECT c.id, c.name, c.domain, c.description, c.subscription_plan, 
                   c.status, c.created_at,
                   r.full_name as admin_name, r.email as admin_email
            FROM companies c
            LEFT JOIN recruiters r ON c.id = r.company_id AND LOWER(r.role) = 'admin'
            WHERE c.id = $1
            """,
            company_id
        )
        
        if not company_row:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get aggregate counts (privacy-compliant)
        counts_row = await conn.fetchrow(
            """
            SELECT 
                COUNT(DISTINCT j.id) as jobs_count,
                COUNT(DISTINCT a.id) as applications_count,
                COUNT(DISTINCT cand.id) as candidates_count,
                COUNT(DISTINCT r.id) as admin_count
            FROM companies c
            LEFT JOIN jobs j ON c.id = j.company_id
            LEFT JOIN applications a ON j.id = a.job_id
            LEFT JOIN candidates cand ON a.candidate_id = cand.id
            LEFT JOIN recruiters r ON c.id = r.company_id
            WHERE c.id = $1
            """,
            company_id
        )
        
        result = dict(company_row)
        result.update(dict(counts_row))
        return result


@router.delete("/companies/{company_id}")
async def delete_company(company_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    async with global_pool.acquire() as conn:
        res = await conn.execute("DELETE FROM companies WHERE id = $1", company_id)
        if res == "DELETE 0":
            raise HTTPException(status_code=404, detail="Company not found")
        return {"deleted": True}
