from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import Optional
import logging
import os
import asyncpg

from api.routers.super_admin import super_admin_required, SuperAdminProfile, _get_conn
from config.security import get_password_hash

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/companies/{company_id}/admins")
async def list_company_admins(company_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    """List all admins/recruiters for a specific company"""
    conn = await _get_conn()
    try:
        rows = await conn.fetch(
            """
            SELECT id, full_name, email, phone_number, role, is_active, created_at
            FROM recruiters
            WHERE company_id = $1
            ORDER BY created_at DESC
            """,
            company_id,
        )
        return {"items": [dict(r) for r in rows]}
    finally:
        await conn.close()


@router.post("/companies/{company_id}/admins")
async def create_company_admin(company_id: int, payload: dict = Body(...), _: SuperAdminProfile = Depends(super_admin_required)):
    """Create a new admin/recruiter for a specific company"""
    full_name = str(payload.get("full_name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    phone_number = payload.get("phone_number")
    password = str(payload.get("password", ""))
    role = str(payload.get("role", "admin"))
    
    if not full_name or not email or not password:
        raise HTTPException(status_code=400, detail="full_name, email, and password are required")
    
    if role not in ["admin", "recruiter"]:
        raise HTTPException(status_code=400, detail="role must be 'admin' or 'recruiter'")
    
    conn = await _get_conn()
    try:
        # Check if company exists
        company = await conn.fetchrow("SELECT id FROM companies WHERE id = $1", company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Check if email already exists
        existing = await conn.fetchrow("SELECT id FROM recruiters WHERE email = $1", email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Create recruiter
        row = await conn.fetchrow(
            """
            INSERT INTO recruiters (full_name, email, phone_number, password_hash, role, company_id, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, true)
            RETURNING id, full_name, email, phone_number, role, is_active, created_at
            """,
            full_name, email, phone_number, hashed_password, role, company_id,
        )
        return dict(row)
    finally:
        await conn.close()


@router.put("/companies/{company_id}/admins/{admin_id}")
async def update_company_admin(
    company_id: int, 
    admin_id: int, 
    payload: dict = Body(...), 
    _: SuperAdminProfile = Depends(super_admin_required)
):
    """Update an admin/recruiter for a specific company"""
    fields = []
    params = []
    idx = 1
    
    for key in ["full_name", "phone_number", "role", "is_active"]:
        if key in payload:
            idx += 1
            fields.append(f"{key} = ${idx}")
            params.append(payload[key])
    
    # Handle password update separately
    if "password" in payload and payload["password"]:
        idx += 1
        fields.append(f"password_hash = ${idx}")
        params.append(get_password_hash(str(payload["password"])))
    
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    conn = await _get_conn()
    try:
        row = await conn.fetchrow(
            f"""
            UPDATE recruiters
            SET {', '.join(fields)}, updated_at = now()
            WHERE id = $1 AND company_id = $2
            RETURNING id, full_name, email, phone_number, role, is_active, updated_at
            """,
            admin_id, company_id, *params,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Admin not found in this company")
        return dict(row)
    finally:
        await conn.close()


@router.delete("/companies/{company_id}/admins/{admin_id}")
async def delete_company_admin(company_id: int, admin_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    """Delete an admin/recruiter from a specific company"""
    conn = await _get_conn()
    try:
        # Check if this is the last admin of the company
        admin_count = await conn.fetchval(
            "SELECT COUNT(*) FROM recruiters WHERE company_id = $1 AND LOWER(role) = 'admin' AND is_active = true",
            company_id
        )
        
        # Get the admin to check their role
        admin = await conn.fetchrow(
            "SELECT role FROM recruiters WHERE id = $1 AND company_id = $2",
            admin_id, company_id
        )
        
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found in this company")
        
        if admin["role"].lower() == "admin" and admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin of a company")
        
        res = await conn.execute(
            "DELETE FROM recruiters WHERE id = $1 AND company_id = $2",
            admin_id, company_id
        )
        if res == "DELETE 0":
            raise HTTPException(status_code=404, detail="Admin not found in this company")
        return {"deleted": True}
    finally:
        await conn.close()


@router.post("/companies/{company_id}/admins/{admin_id}/reset-password")
async def reset_admin_password(
    company_id: int, 
    admin_id: int, 
    payload: dict = Body(...), 
    _: SuperAdminProfile = Depends(super_admin_required)
):
    """Reset an admin's password"""
    new_password = str(payload.get("password", "")).strip()
    if not new_password:
        raise HTTPException(status_code=400, detail="password is required")
    
    conn = await _get_conn()
    try:
        row = await conn.fetchrow(
            """
            UPDATE recruiters
            SET password_hash = $1, updated_at = now()
            WHERE id = $2 AND company_id = $3
            RETURNING id, email, full_name
            """,
            get_password_hash(new_password), admin_id, company_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Admin not found in this company")
        return {"message": "Password reset successfully", "admin": dict(row)}
    finally:
        await conn.close()
