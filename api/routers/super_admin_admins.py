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
    async with _get_conn() as conn:
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
    
    async with _get_conn() as conn:
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


@router.put("/companies/{company_id}/admins/{admin_id}")
async def update_company_admin(
    company_id: int, 
    admin_id: int, 
    payload: dict = Body(...), 
    _: SuperAdminProfile = Depends(super_admin_required)
):
    """Update an admin/recruiter for a specific company and send email notification"""
    fields = []
    params = []
    # Start at 2 because $1 and $2 are reserved for WHERE clause (admin_id, company_id)
    idx = 2
    
    # Track if is_active is being changed for email notification
    is_active_changed = "is_active" in payload
    new_is_active = bool(payload.get("is_active")) if is_active_changed else None
    
    for key in ["full_name", "phone_number", "role", "is_active"]:
        if key in payload:
            idx += 1
            # Convert is_active to boolean explicitly - handle all cases
            if key == "is_active":
                value = payload[key]
                # Handle various input types: bool, int, str
                if isinstance(value, bool):
                    boolean_value = value
                elif isinstance(value, int):
                    boolean_value = value != 0
                elif isinstance(value, str):
                    boolean_value = value.lower() in ['true', '1', 'yes']
                else:
                    boolean_value = bool(value)
                fields.append(f"{key} = ${idx}")
                params.append(boolean_value)
            else:
                fields.append(f"{key} = ${idx}")
                params.append(payload[key])
    
    # Handle password update separately
    if "password" in payload and payload["password"]:
        idx += 1
        fields.append(f"password_hash = ${idx}")
        params.append(get_password_hash(str(payload["password"])))
    
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    async with _get_conn() as conn:
        # Get old values before update for email notification
        old_admin = await conn.fetchrow(
            "SELECT full_name, email, is_active FROM recruiters WHERE id = $1 AND company_id = $2",
            admin_id, company_id
        )
        
        if not old_admin:
            raise HTTPException(status_code=404, detail="Admin not found in this company")
        
        # Update the admin
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
        
        # Send email notification if is_active status changed
        if is_active_changed and old_admin['is_active'] != new_is_active:
            try:
                from services.email_service import email_service
                
                status_text = "Activated" if new_is_active else "Deactivated"
                old_status_text = "Active" if old_admin['is_active'] else "Inactive"
                
                await email_service.send_admin_status_change_email(
                    admin_name=row['full_name'],
                    admin_email=row['email'],
                    new_status=status_text,
                    old_status=old_status_text
                )
                logger.info(f"✅ Admin status change email sent to {row['email']}")
            except Exception as e:
                logger.error(f"❌ Failed to send admin status change email: {e}")
        
        return dict(row)


@router.delete("/companies/{company_id}/admins/{admin_id}")
async def delete_company_admin(company_id: int, admin_id: int, _: SuperAdminProfile = Depends(super_admin_required)):
    """Delete an admin/recruiter from a specific company"""
    async with _get_conn() as conn:
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
    
    async with _get_conn() as conn:
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
