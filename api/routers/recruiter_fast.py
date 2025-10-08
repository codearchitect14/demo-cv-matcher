from fastapi import APIRouter, HTTPException, status
from typing import Optional
import logging
import asyncpg
import os
import hashlib
from pydantic import BaseModel
import asyncio

# Import enhanced services
from services.integrated_notification_service import integrated_notification_service

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
        
        # Send welcome email and create notification using integrated service (non-blocking)
        async def send_welcome_email_and_notification():
            try:
                recruiter_email = new_recruiter_row['email']
                recruiter_name = new_recruiter_row['full_name']
                company_name = request_data.get('company_name', 'Test Company')
                
                # Prepare login credentials for the email
                login_credentials = {
                    'email': recruiter_email,
                    'password': password,
                    'dashboard_url': 'http://localhost:3000/sub-recruiter/dashboard'
                }
                
                # Use integrated service for sub-recruiter welcome
                results = await integrated_notification_service.send_sub_recruiter_welcome(
                    recruiter_email=recruiter_email,
                    recruiter_name=recruiter_name,
                    company_name=company_name,
                    login_credentials=login_credentials,
                    admin_user_id=1,  # TODO: Get actual admin user ID
                    admin_name="Company Admin"
                )
                
                logger.info(f"Sub-recruiter welcome sent: email={results['email']}, notification={results['notification']}")
                
            except Exception as e:
                logger.error(f"Error sending welcome email/notification to sub-recruiter: {e}")
        
        # Send email and notification asynchronously (non-blocking)
        asyncio.create_task(send_welcome_email_and_notification())
        
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

@router.put("/admin/update-fast/{recruiter_id}")
async def update_recruiter_fast(recruiter_id: int, request_data: dict):
    """Update recruiter - Real database implementation"""
    try:
        from config.connection_pool import global_pool
        
        # Check if recruiter exists
        existing_recruiter = await global_pool.fetchrow(
            "SELECT id, full_name, email FROM recruiters WHERE id = $1",
            recruiter_id
        )
        
        if not existing_recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found"
            )
        
        # Check if email is being changed and if new email already exists
        if request_data.get('email') and request_data['email'] != existing_recruiter['email']:
            email_check = await global_pool.fetchrow(
                "SELECT id FROM recruiters WHERE email = $1 AND id != $2",
                request_data['email'], recruiter_id
            )
            if email_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Prepare update fields
        update_fields = []
        update_values = []
        param_count = 1
        
        # Handle password update if provided
        if request_data.get('password'):
            from config.security import get_password_hash
            hashed_password = get_password_hash(request_data['password'])
            update_fields.append(f"password_hash = ${param_count}")
            update_values.append(hashed_password)
            param_count += 1
        
        # Handle other fields
        field_mapping = {
            'full_name': 'full_name',
            'email': 'email', 
            'phone_number': 'phone_number',
            'company_name': 'company_name',
            'domain': 'domain',
            'company_size': 'company_size',
            'company_description': 'company_description',
            'role': 'role',
            'is_active': 'is_active'
        }
        
        for request_field, db_field in field_mapping.items():
            if request_field in request_data:
                update_fields.append(f"{db_field} = ${param_count}")
                update_values.append(request_data[request_field])
                param_count += 1
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Add updated_at
        update_fields.append(f"updated_at = ${param_count}")
        update_values.append("NOW()")
        param_count += 1
        
        # Add recruiter_id for WHERE clause
        update_values.append(recruiter_id)
        
        # Execute update
        update_query = f"""
            UPDATE recruiters 
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING id, full_name, email, role, is_active, updated_at
        """
        
        updated_recruiter = await global_pool.fetchrow(update_query, *update_values)
        
        logger.info(f"Recruiter updated: {updated_recruiter['email']}")
        
        return {
            "id": updated_recruiter['id'],
            "full_name": updated_recruiter['full_name'],
            "email": updated_recruiter['email'],
            "role": updated_recruiter['role'],
            "is_active": updated_recruiter['is_active'],
            "updated_at": updated_recruiter['updated_at'].isoformat(),
            "message": "Recruiter updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recruiter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update recruiter"
        )

@router.put("/admin/toggle-status-fast/{recruiter_id}")
async def toggle_recruiter_status_fast(recruiter_id: int):
    """Toggle recruiter status - Real database implementation"""
    try:
        from config.connection_pool import global_pool
        
        # Get current status
        current_recruiter = await global_pool.fetchrow(
            "SELECT id, full_name, email, is_active FROM recruiters WHERE id = $1",
            recruiter_id
        )
        
        if not current_recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found"
            )
        
        # Toggle status
        new_status = not current_recruiter['is_active']
        
        # Update in database
        await global_pool.execute(
            "UPDATE recruiters SET is_active = $1, updated_at = NOW() WHERE id = $2",
            new_status, recruiter_id
        )
        
        action = "activated" if new_status else "deactivated"
        logger.info(f"Recruiter {action}: {current_recruiter['email']}")
        
        return {
            "id": recruiter_id,
            "full_name": current_recruiter['full_name'],
            "email": current_recruiter['email'],
            "is_active": new_status,
            "message": f"Recruiter {action} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling recruiter status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle recruiter status"
        )

@router.delete("/admin/delete-fast/{recruiter_id}")
async def delete_recruiter_fast(recruiter_id: int):
    """Delete recruiter - Real database implementation"""
    try:
        from config.connection_pool import global_pool
        
        # Get recruiter info before deletion
        recruiter_info = await global_pool.fetchrow(
            "SELECT id, full_name, email FROM recruiters WHERE id = $1",
            recruiter_id
        )
        
        if not recruiter_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found"
            )
        
        # Delete from database
        await global_pool.execute(
            "DELETE FROM recruiters WHERE id = $1",
            recruiter_id
        )
        
        logger.info(f"Recruiter deleted: {recruiter_info['email']}")
        
        return {
            "id": recruiter_id,
            "full_name": recruiter_info['full_name'],
            "email": recruiter_info['email'],
            "message": "Recruiter deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recruiter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete recruiter"
        )
