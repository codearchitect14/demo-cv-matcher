from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
import os
import asyncpg
from datetime import timedelta

from config.security import verify_password, get_password_hash, create_access_token, verify_token, SecurityConfig
from config.connection_pool import global_pool

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


async def _get_conn():
    from config.connection_pool import global_pool
    return global_pool.acquire()


async def super_admin_required(request: Request) -> SuperAdminProfile:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth_header.split(" ", 1)[1]
    token_data = verify_token(token)
    if token_data is None or (token_data.role or "").lower() != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")

    # Load profile from DB (id/email)
    async with _get_conn() as conn:
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

    conn = await _get_conn()
    try:
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
    finally:
        try:
            await conn.close()
        except Exception:
            pass


@router.get("/me", response_model=SuperAdminProfile)
async def super_admin_me(profile: SuperAdminProfile = Depends(super_admin_required)):
    return profile


# ===== Overview & Lists =====

class OverviewResponse(BaseModel):
    companies: int
    recruiters: int
    candidates: int
    jobs: int
    applications: int


@router.get("/overview", response_model=OverviewResponse)
async def super_admin_overview(_: SuperAdminProfile = Depends(super_admin_required)):
    conn = await _get_conn()
    try:
        # Use COALESCE to handle missing tables gracefully
        row = await conn.fetchrow(
            """
            SELECT 
              COALESCE((SELECT COUNT(*) FROM companies), 0) AS companies,
              COALESCE((SELECT COUNT(*) FROM recruiters), 0) AS recruiters,
              COALESCE((SELECT COUNT(*) FROM candidates), 0) AS candidates,
              COALESCE((SELECT COUNT(*) FROM jobs), 0) AS jobs,
              COALESCE((SELECT COUNT(*) FROM applications), 0) AS applications
            """
        )
        return OverviewResponse(
            companies=row["companies"],
            recruiters=row["recruiters"],
            candidates=row["candidates"],
            jobs=row["jobs"],
            applications=row["applications"],
        )
    finally:
        try:
            await conn.close()
        except Exception:
            pass


class PageParams(BaseModel):
    limit: int = 20
    offset: int = 0


@router.get("/companies")
async def list_companies(limit: int = 20, offset: int = 0, _: SuperAdminProfile = Depends(super_admin_required)):
    conn = await _get_conn()
    try:
        rows = await conn.fetch(
            """
            SELECT id, name, domain, created_at
            FROM companies
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset,
        )
        return {"items": [dict(r) for r in rows]}
    finally:
        try:
            await conn.close()
        except Exception:
            pass


@router.get("/admins")
async def list_admins(limit: int = 20, offset: int = 0, _: SuperAdminProfile = Depends(super_admin_required)):
    conn = await _get_conn()
    try:
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
    finally:
        try:
            await conn.close()
        except Exception:
            pass


# ===== Companies CRUD =====

from fastapi import Body


@router.post("/companies")
async def create_company(payload: dict = Body(...), _: SuperAdminProfile = Depends(super_admin_required)):
    name = str(payload.get("name", "")).strip()
    domain = str(payload.get("domain", "")).strip()
    description = payload.get("description")
    subscription_plan = str(payload.get("subscription_plan", "basic"))
    is_active = bool(payload.get("is_active", True))
    if not name or not domain:
        raise HTTPException(status_code=400, detail="name and domain are required")

    conn = await _get_conn()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO companies (name, domain, description, subscription_plan, is_active)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, domain, description, subscription_plan, is_active, created_at
            """,
            name, domain, description, subscription_plan, is_active,
        )
        return dict(row)
    finally:
        await conn.close()


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

    conn = await _get_conn()
    try:
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
    finally:
        await conn.close()


@router.delete("/companies/{company_id}")
async def delete_company(company_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    conn = await _get_conn()
    try:
        res = await conn.execute("DELETE FROM companies WHERE id = $1", company_id)
        if res == "DELETE 0":
            raise HTTPException(status_code=404, detail="Company not found")
        return {"deleted": True}
    finally:
        await conn.close()


