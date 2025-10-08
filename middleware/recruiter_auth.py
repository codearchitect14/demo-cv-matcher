"""
Recruiter Authentication and Role-Based Access Control Middleware
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from config.database import get_db_session
from jose import JWTError, jwt
import os
from datetime import datetime
from config.security import SecurityConfig

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()

class RecruiterContext:
    """Context class to hold recruiter information"""
    def __init__(self, recruiter_id: int, email: str, name: str, role: str, is_admin: bool = False, company_id: Optional[int] = None):
        self.recruiter_id = recruiter_id
        self.email = email
        self.name = name
        self.role = role
        self.is_admin = is_admin
        self.company_id = company_id

class RecruiterAuthMiddleware:
    """Middleware for recruiter authentication and authorization"""
    
    def __init__(self):
        self.secret_key = SecurityConfig.SECRET_KEY
        self.algorithm = SecurityConfig.ALGORITHM
    
    async def get_current_recruiter(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> RecruiterContext:
        """Extract and validate recruiter from JWT token"""
        try:
            # Decode JWT token
            payload = jwt.decode(
                credentials.credentials, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            recruiter_email = payload.get("sub")
            if recruiter_email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing recruiter email"
                )
            
            # Get recruiter details from database using connection pool (FAST!)
            from config.connection_pool import global_pool
            
            recruiter = await global_pool.fetchrow("""
                SELECT id, full_name, email, role, is_active, company_id
                FROM recruiters 
                WHERE email = $1
            """, recruiter_email)
            
            if not recruiter:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Recruiter not found"
                )
            
            if not recruiter['is_active']:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Recruiter account is inactive"
                )
            
            # Create recruiter context
            is_admin = recruiter['role'].lower() in ['admin', 'administrator', 'super_admin']
            
            return RecruiterContext(
                recruiter_id=recruiter['id'],
                email=recruiter['email'],
                name=recruiter['full_name'],
                role=recruiter['role'],
                is_admin=is_admin,
                company_id=recruiter['company_id']
            )
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Recruiter authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    async def check_job_access(
        self, 
        job_id: int, 
        recruiter_context: RecruiterContext
    ) -> bool:
        """Check if recruiter has access to a specific job"""
        try:
            # Admin users have access to all jobs
            if recruiter_context.is_admin:
                return True
            
            # Check if recruiter is assigned to this job using connection pool (FAST!)
            from config.connection_pool import global_pool
            
            job = await global_pool.fetchrow("""
                SELECT recruiter_id 
                FROM jobs 
                WHERE id = $1
            """, job_id)
            
            if not job:
                return False
            
            return job['recruiter_id'] == recruiter_context.recruiter_id
            
        except Exception as e:
            logger.error(f"Job access check error: {e}")
            return False
    
    async def check_application_access(
        self, 
        application_id: int, 
        recruiter_context: RecruiterContext
    ) -> bool:
        """Check if recruiter has access to a specific application"""
        try:
            # Admin users have access to all applications
            if recruiter_context.is_admin:
                return True
            
            # Check if recruiter is assigned to the job for this application using connection pool (FAST!)
            from config.connection_pool import global_pool
            
            job = await global_pool.fetchrow("""
                SELECT j.recruiter_id 
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                WHERE a.id = $1
            """, application_id)
            
            if not job:
                return False
            
            return job['recruiter_id'] == recruiter_context.recruiter_id
            
        except Exception as e:
            logger.error(f"Application access check error: {e}")
            return False
    
    def require_admin(self, recruiter_context: RecruiterContext):
        """Require admin role for access"""
        if not recruiter_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    
    def require_recruiter_or_admin(self, recruiter_context: RecruiterContext):
        """Require recruiter or admin role for access"""
        if recruiter_context.role.lower() not in ['recruiter', 'admin', 'administrator', 'super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Recruiter or admin access required"
            )

# Create global instance
recruiter_auth = RecruiterAuthMiddleware()

# Dependency functions for easy use in endpoints
async def get_current_recruiter(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> RecruiterContext:
    """Dependency to get current recruiter context"""
    return await recruiter_auth.get_current_recruiter(credentials)

async def require_job_access(
    job_id: int,
    recruiter_context: RecruiterContext = Depends(get_current_recruiter)
) -> RecruiterContext:
    """Dependency to require job access"""
    has_access = await recruiter_auth.check_job_access(job_id, recruiter_context)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't have permission to access this job"
        )
    return recruiter_context

async def require_application_access(
    application_id: int,
    recruiter_context: RecruiterContext = Depends(get_current_recruiter)
) -> RecruiterContext:
    """Dependency to require application access"""
    has_access = await recruiter_auth.check_application_access(application_id, recruiter_context)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't have permission to access this application"
        )
    return recruiter_context

async def require_admin_access(
    recruiter_context: RecruiterContext = Depends(get_current_recruiter)
) -> RecruiterContext:
    """Dependency to require admin access"""
    recruiter_auth.require_admin(recruiter_context)
    return recruiter_context
