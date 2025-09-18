from fastapi import APIRouter, HTTPException, status
from typing import Optional
import logging
import asyncpg
import os
import hashlib
from pydantic import BaseModel

router = APIRouter(tags=["Recruiter Fast"])
logger = logging.getLogger(__name__)

# Mock data storage (in memory)
mock_recruiters_storage = [
    {
        "id": 1,
        "full_name": "John Smith",
        "email": "john@company.com",
        "company_name": "Test Company",
        "role": "admin",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 2,
        "full_name": "Sarah Johnson",
        "email": "sarah@company.com",
        "company_name": "Test Company",
        "role": "recruiter",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 3,
        "full_name": "Mike Wilson",
        "email": "mike@company.com",
        "company_name": "Test Company",
        "role": "recruiter",
        "is_active": False,
        "created_at": "2024-01-01T00:00:00"
    }
]

# Remove local hash function - will use the one from config.security

@router.post("/admin/create-fast")
async def create_recruiter_fast(request_data: dict):
    """Create a new recruiter - Now saves to real database"""
    try:
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from config.database import get_db_session
        from db.crud.recruiter import recruiter
        from config.security import get_password_hash
        
        # Use global connection pool to avoid prepared statement issues
        from config.connection_pool import global_pool
        
        # Check if email already exists
        existing_check = await global_pool.fetchrow(
            "SELECT id FROM recruiters WHERE email = $1",
            request_data.get('email')
        )
        if existing_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password (use default if not provided)
        password = request_data.get('password', 'defaultpass123')
        hashed_password = get_password_hash(password)
        
        # Insert recruiter directly using global pool
        insert_query = """
            INSERT INTO recruiters (
                full_name, email, phone_number, company_name, domain, company_size,
                company_description, role, is_active, email_verified, password_hash, company_id,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW()
            )
            RETURNING id, full_name, email, role, is_active, created_at
        """
        
        new_recruiter_row = await global_pool.fetchrow(
            insert_query,
            request_data.get('full_name', 'Test User'),
            request_data.get('email', 'test@company.com'),
            request_data.get('phone_number', ''),
            request_data.get('company_name', 'Test Company'),
            request_data.get('domain', 'IT'),
            request_data.get('company_size', '1-10'),
            request_data.get('company_description', ''),
            request_data.get('role', 'recruiter'),
            True,  # is_active
            True,  # email_verified
            hashed_password,
            1  # company_id
        )
        
        logger.info(f"Real recruiter creation successful: {new_recruiter_row['email']}")
        return {
            "id": new_recruiter_row['id'],
            "full_name": new_recruiter_row['full_name'],
            "email": new_recruiter_row['email'],
            "role": new_recruiter_row['role'],
            "is_active": new_recruiter_row['is_active'],
            "created_at": new_recruiter_row['created_at'].isoformat(),
            "message": "Recruiter created successfully in database"
        }
        
    except Exception as e:
        logger.error(f"Error in mock recruiter creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create recruiter"
        )

@router.get("/admin/list-fast")
async def list_recruiters_fast(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """Get recruiters list - Now shows real database records"""
    try:
        from config.database import SessionLocal
        from db.crud.recruiter import recruiter
        
        # Use global connection pool to avoid prepared statement issues
        from config.connection_pool import global_pool
        
        if search:
            # Simple search implementation
            query = """
                SELECT id, full_name, email, company_name, role, is_active, created_at
                FROM recruiters 
                WHERE LOWER(full_name) LIKE LOWER($1) 
                   OR LOWER(email) LIKE LOWER($1)
                   OR LOWER(company_name) LIKE LOWER($1)
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            rows = await global_pool.fetch(query, f"%{search}%", limit, skip)
        else:
            query = """
                SELECT id, full_name, email, company_name, role, is_active, created_at
                FROM recruiters 
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            rows = await global_pool.fetch(query, limit, skip)
        
        recruiters = []
        for row in rows:
            recruiters.append({
                "id": row['id'],
                "full_name": row['full_name'],
                "email": row['email'],
                "company_name": row['company_name'],
                "role": row['role'],
                "is_active": row['is_active'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else "2024-01-01T00:00:00"
            })
        
        logger.info(f"Real recruiter list successful: {len(recruiters)} recruiters")
        return recruiters
        
    except Exception as e:
        logger.error(f"Error in mock recruiter list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recruiters"
        )

@router.put("/admin/toggle-status-fast/{recruiter_id}")
async def toggle_recruiter_status_fast(recruiter_id: int):
    """Toggle recruiter status - Mock version"""
    try:
        # Mock response - works instantly
        logger.info(f"Mock status toggle successful for recruiter {recruiter_id}")
        return {
            "id": recruiter_id,
            "full_name": "Mock User",
            "email": "mock@company.com",
            "is_active": True,
            "message": "Recruiter status toggled successfully (mock)"
        }
        
    except Exception as e:
        logger.error(f"Error in mock status toggle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle status"
        )

@router.delete("/admin/delete-fast/{recruiter_id}")
async def delete_recruiter_fast(recruiter_id: int):
    """Delete recruiter - Mock version"""
    try:
        # Mock response - works instantly
        logger.info(f"Mock recruiter deletion successful for recruiter {recruiter_id}")
        return {
            "id": recruiter_id,
            "full_name": "Mock User",
            "email": "mock@company.com",
            "message": "Recruiter deleted successfully (mock)"
        }
        
    except Exception as e:
        logger.error(f"Error in mock recruiter deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete recruiter"
        )
