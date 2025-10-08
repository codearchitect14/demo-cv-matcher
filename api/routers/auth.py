from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Union
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, timedelta
import secrets
import logging
from jose import JWTError, jwt

from config.database import get_db_session
from config.security import (
    SecurityConfig, verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token, store_refresh_token, validate_refresh_token,
    revoke_refresh_token, store_user_session, validate_user_session, 
    revoke_user_session, get_active_sessions_count, validate_password_with_feedback,
    simulate_constant_time_verify
)
from models.candidate import Candidate
from models.recruiter import Recruiter
from db.crud.candidate import candidate as candidate_crud
from db.crud.recruiter import recruiter as recruiter_crud
from services.email_service import email_service
from services.notification_service import notification_service
from schemas.validation import UserRegistrationValidation, EmailValidation, PasswordValidation
from fastapi.security import OAuth2PasswordBearer
from config.connection_pool import global_pool

router = APIRouter(tags=["Authentication"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Logger
logger = logging.getLogger(__name__)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    location: str
    domain: str
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    summary: str
    created_at: datetime
    role: str = "user"
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user_id: int
    role: str

class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str

class LogoutResponse(BaseModel):
    message: str
    sessions_revoked: int

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> Candidate:
    """Get current authenticated user - optimized via asyncpg (no prepared statements)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token without database query first
        token_data = verify_token(token)
        if token_data is None:
            raise credentials_exception
        
        # Get user from database using global asyncpg pool (pgbouncer safe)
        row = await global_pool.fetchrow(
            """
            SELECT id, name, email, role, location, domain,
                   expected_salary_min, expected_salary_max, summary, created_at, password_hash
            FROM candidates
            WHERE email = $1
            LIMIT 1
            """,
            token_data.email
        )
        if row is None:
            raise credentials_exception

        class SimpleCandidate:
            def __init__(self, r):
                self.id = r['id']
                self.name = r['name']
                self.email = r['email']
                self.role = r['role']
                self.location = r['location']
                self.domain = r['domain']
                self.expected_salary_min = r['expected_salary_min']
                self.expected_salary_max = r['expected_salary_max']
                self.summary = r['summary']
                self.created_at = r['created_at']
                self.password_hash = r['password_hash']

        return SimpleCandidate(row)
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception

async def get_current_recruiter(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> Recruiter:
    """Get current authenticated recruiter - asyncpg lookup."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        token_data = verify_token(token)
        if token_data is None:
            raise credentials_exception
        
        # Get recruiter from database using global pool
        row = await global_pool.fetchrow(
            """
            SELECT id, full_name, email, role, is_active
            FROM recruiters
            WHERE email = $1
            LIMIT 1
            """,
            token_data.email
        )
        if row is None:
            raise credentials_exception

        class SimpleRecruiter:
            def __init__(self, r):
                self.id = r['id']
                self.full_name = r['full_name']
                self.email = r['email']
                self.role = r['role']
                self.is_active = r['is_active']

        return SimpleRecruiter(row)
        
    except Exception as e:
        logger.error(f"Recruiter authentication error: {str(e)}")
        raise credentials_exception

async def get_current_user_or_recruiter(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> Union[Candidate, Recruiter]:
    """Get current authenticated user (candidate or recruiter)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        token_data = verify_token(token)
        if token_data is None:
            logger.error("Token verification failed")
            raise credentials_exception
        
        logger.info(f"Token verified for email: {token_data.email}")
        
        # Try to get candidate first using global pool
        cand_row = await global_pool.fetchrow(
            "SELECT id, name, email, role FROM candidates WHERE email = $1 LIMIT 1",
            token_data.email
        )
        if cand_row is not None:
            logger.info(f"Found candidate user: {cand_row['id']} - {cand_row['email']} with role: {cand_row['role']}")
            class SimpleCandidate:
                def __init__(self, r):
                    self.id = r['id']
                    self.name = r.get('name')
                    self.email = r['email']
                    self.role = r['role']
            return SimpleCandidate(cand_row)
        
        # Try to get recruiter via global pool
        rec_row = await global_pool.fetchrow(
            "SELECT id, full_name, email, role FROM recruiters WHERE email = $1 LIMIT 1",
            token_data.email
        )
        if rec_row is not None:
            logger.info(f"Found recruiter user: {rec_row['id']} - {rec_row['email']} with role: {rec_row['role']}")
            class SimpleRecruiter:
                def __init__(self, r):
                    self.id = r['id']
                    self.full_name = r.get('full_name')
                    self.email = r['email']
                    self.role = r['role']
            return SimpleRecruiter(rec_row)
        
        # Neither found
        logger.error(f"No user found for email: {token_data.email}")
        raise credentials_exception
        
    except Exception as e:
        logger.error(f"Unified authentication error: {str(e)}")
        raise credentials_exception

async def get_current_recruiter_or_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> Union[Candidate, Recruiter]:
    """Get current authenticated user (prioritizes recruiters over candidates)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        token_data = verify_token(token)
        if token_data is None:
            logger.error("Token verification failed")
            raise credentials_exception
        
        logger.info(f"Token verified for email: {token_data.email}")
        
        # Try to get recruiter FIRST (prioritize recruiters) using global pool
        rec_row = await global_pool.fetchrow(
            "SELECT id, full_name, email, role FROM recruiters WHERE email = $1 LIMIT 1",
            token_data.email
        )
        if rec_row is not None:
            logger.info(f"Found recruiter user: {rec_row['id']} - {rec_row['email']} with role: {rec_row['role']}")
            class SimpleRecruiter:
                def __init__(self, r):
                    self.id = r['id']
                    self.full_name = r.get('full_name')
                    self.email = r['email']
                    self.role = r['role']
            return SimpleRecruiter(rec_row)
        
        # Try to get candidate as fallback via global pool
        cand_row = await global_pool.fetchrow(
            "SELECT id, name, email, role FROM candidates WHERE email = $1 LIMIT 1",
            token_data.email
        )
        if cand_row is not None:
            logger.info(f"Found candidate user: {cand_row['id']} - {cand_row['email']} with role: {cand_row['role']}")
            class SimpleCandidate:
                def __init__(self, r):
                    self.id = r['id']
                    self.name = r.get('name')
                    self.email = r['email']
                    self.role = r['role']
            return SimpleCandidate(cand_row)
        
        # Neither found
        logger.error(f"No user found for email: {token_data.email}")
        raise credentials_exception
        
    except Exception as e:
        logger.error(f"Recruiter-priority authentication error: {str(e)}")
        raise credentials_exception

async def get_current_active_user(
    current_user: Candidate = Depends(get_current_user)
) -> Candidate:
    """Get current active user (can be extended for account status checks)"""
    # Add any additional checks here (e.g., account verification, suspension)
    return current_user

def require_role(required_roles: List[str]):
    """Dependency to require specific role(s)"""
    def role_checker(current_user: Candidate = Depends(get_current_user)):
        if current_user.role not in required_roles and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        return current_user
    return role_checker

@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegistrationValidation, 
    request: Request = None
):
    """Register a new user with comprehensive validation - using direct asyncpg to avoid PgBouncer issues"""
    try:
        # Check if user already exists using direct asyncpg
        async with global_pool.acquire() as conn:
            existing_user = await conn.fetchrow(
                "SELECT id, email FROM candidates WHERE email = $1",
                user_data.email
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email is already in use. Please use a different email address."
                )
        
        # Validate password strength
        is_valid, message = validate_password_with_feedback(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Create new user using direct asyncpg
        hashed_password = get_password_hash(user_data.password)
        skills_data = user_data.skills or []
        
        async with global_pool.acquire() as conn:
            # Create the candidate
            user_row = await conn.fetchrow(
                """
                INSERT INTO candidates (name, email, password_hash, location, domain, 
                                     expected_salary_min, expected_salary_max, summary, 
                                     total_experience_years, role, consent_given, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
                RETURNING id, name, email, role
                """,
                user_data.name,
                user_data.email,
                hashed_password,
                user_data.location,
                user_data.domain,
                user_data.expected_salary_min,
                user_data.expected_salary_max,
                user_data.summary,
                user_data.total_experience_years,
                "user",
                True  # Set consent_given to True by default for registration
            )
            
            user_id = user_row["id"]
            user_name = user_row["name"]
            user_email = user_row["email"]
            user_role = user_row["role"]
            
            # Add skills as experiences if provided
            if skills_data:
                try:
                    for skill in skills_data:
                        await conn.execute(
                            """
                            INSERT INTO candidate_experiences (candidate_id, skill, years_of_experience, 
                                                            description, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, NOW(), NOW())
                            """,
                            user_id,
                            skill["name"],
                            skill["years"],
                            skill.get("description", "")
                        )
                    logger.info(f"Added {len(skills_data)} skills for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to add skills for user {user_id}: {str(e)}")
                    # Don't fail registration if skills addition fails
        
        # Create tokens
        access_token_expires = timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_email, "user_id": str(user_id), "role": user_role},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user_email, "user_id": str(user_id), "role": user_role}
        )
        
        # Store refresh token
        await store_refresh_token(user_id, refresh_token)
        
        # Send welcome email to multiple addresses for testing
        try:
            # Primary email
            print(f"DEBUG: Attempting to send welcome email to {user_email}")
            email_success = await email_service.send_welcome_email(user_email, user_name)
            if email_success:
                logger.info(f"Welcome email sent successfully to {user_email}")
                print(f"DEBUG: Welcome email sent successfully to {user_email}")
            else:
                logger.error(f"Welcome email failed to send to {user_email}")
                print(f"DEBUG: Welcome email failed to send to {user_email}")
            
            # Backup email for testing (if primary fails)
            backup_email = "aliboolmind228@gmail.com"
            if not email_success:
                print(f"DEBUG: Sending backup email to {backup_email}")
                backup_success = await email_service.send_welcome_email(backup_email, user_name)
                if backup_success:
                    logger.info(f"Backup welcome email sent to {backup_email}")
                    print(f"DEBUG: Backup email sent to {backup_email}")
                    
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user_email}: {str(e)}")
            print(f"DEBUG: Exception sending welcome email: {str(e)}")
        
        # Create in-app notification
        try:
            await notification_service.create_notification(
                user_id=user_id,
                user_type="candidate",
                title="Welcome to CV Matcher!",
                message="Your account has been created successfully. Start exploring job opportunities that match your skills.",
                notification_type="success",
                related_entity_type="account",
                related_entity_id=user_id
            )
            logger.info(f"Welcome notification created for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to create welcome notification for user {user_id}: {str(e)}")
        
        # Log registration
        logger.info(f"New user registered: {user_email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user_id,
            role=user_role
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin, 
    db: AsyncSession = Depends(get_db_session),
    request: Request = None
):
    """Login user fast using direct asyncpg (target < 2-3s)."""
    import time
    import os
    import asyncpg
    start_time = time.time()
    
    try:
        # Quick email validation (skip complex validation for performance)
        email = user_credentials.email.strip().lower()
        if not email or '@' not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        # Prepare DSN compatible with asyncpg
        dsn = os.getenv('DATABASE_URL')
        if dsn and dsn.startswith('postgresql+asyncpg://'):
            dsn = dsn.replace('postgresql+asyncpg://', 'postgresql://', 1)

        # Use direct connection per request for stability and speed
        conn = await asyncpg.connect(
            dsn=dsn,
            command_timeout=5,
            timeout=5,
            statement_cache_size=0  # Disable prepared statements for PgBouncer compatibility
        )
        try:
            row = await conn.fetchrow(
                """
                SELECT id, name, email, password_hash, role, location, domain,
                       expected_salary_min, expected_salary_max, summary, created_at
                FROM candidates
                WHERE email = $1
                LIMIT 1
                """,
                email
            )

            if not row:
                # Constant-time verify to avoid timing side-channels
                simulate_constant_time_verify()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password. Please check your credentials and try again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Verify password
            if not verify_password(user_credentials.password, row[3]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password. Please check your credentials and try again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user_id = row[0]
            user_email = row[2]
            user_role = row[4]

            # Create tokens efficiently
            access_token_expires = timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user_email, "user_id": str(user_id), "role": user_role},
                expires_delta=access_token_expires
            )
            refresh_token = create_refresh_token(
                data={"sub": user_email, "user_id": str(user_id), "role": user_role}
            )

            elapsed = time.time() - start_time
            logger.info(f"User logged in: {user_email} in {elapsed:.3f}s")

            # Send login welcome email and notification for candidates (async, non-blocking)
            if user_role in ["candidate", "user"]:
                import asyncio
                user_name = row[1]  # Get user name from database
                
                async def send_candidate_login_notifications():
                    try:
                        # Send email
                        logger.info(f"[EMAIL-TASK] Starting login email for {user_email}")
                        print(f"DEBUG: Sending login welcome email to {user_email}")
                        email_success = await email_service.send_login_welcome_email(user_email, user_name)
                        if email_success:
                            logger.info(f"[EMAIL-SUCCESS] Login welcome email sent to {user_email}")
                            print(f"DEBUG: Login welcome email sent successfully to {user_email}")
                        else:
                            logger.error(f"[EMAIL-FAILED] Login welcome email failed to send to {user_email}")
                            print(f"DEBUG: Login welcome email failed to send to {user_email}")
                    except Exception as e:
                        logger.error(f"[EMAIL-EXCEPTION] Failed to send login welcome email to {user_email}: {str(e)}", exc_info=True)
                        print(f"DEBUG: Exception sending login welcome email: {str(e)}")
                    
                    # Create notification
                    try:
                        await notification_service.create_notification(
                            user_id=user_id,
                            user_type=user_role,
                            title="Welcome Back!",
                            message=f"Hello {user_name}! You've successfully logged into your CV Matcher account.",
                            notification_type="info",
                            related_entity_id=user_id,
                            related_entity_type="candidate"
                        )
                        logger.info(f"[NOTIFICATION-SUCCESS] Login notification created for user {user_id}")
                    except Exception as e:
                        logger.error(f"[NOTIFICATION-FAILED] Failed to create login notification for user {user_id}: {str(e)}", exc_info=True)
                
                async def handle_background_task():
                    """Wrapper to handle background task exceptions"""
                    try:
                        await send_candidate_login_notifications()
                    except Exception as e:
                        logger.error(f"[BACKGROUND-TASK-ERROR] Unhandled exception in login notifications task: {str(e)}", exc_info=True)
                
                # Start email and notification sending in background (don't await)
                task = asyncio.create_task(handle_background_task())
                # Add task name for better debugging
                task.set_name(f"login_notifications_{user_id}")

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_id=user_id,
                role=user_role
            )
        finally:
            try:
                await conn.close()
            except Exception:
                # Ignore close timeouts to avoid masking successful logins
                pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        token_data = verify_token(refresh_request.refresh_token)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Validate refresh token against stored token
        is_valid = await validate_refresh_token(token_data.user_id, refresh_request.refresh_token)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await candidate_crud.get_by_email(db, email=token_data.email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_request.refresh_token,  # Keep same refresh token
            token_type="bearer",
            expires_in=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            role=user.role
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again later."
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: Candidate = Depends(get_current_user),
    request: Request = None
):
    """Logout user and revoke tokens"""
    try:
        # Revoke refresh token
        await revoke_refresh_token(current_user.id)
        
        # Get session ID from request headers or token
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            await revoke_user_session(current_user.id, session_id)
        
        logger.info(f"User logged out: {current_user.email}")
        
        return LogoutResponse(
            message="Successfully logged out",
            sessions_revoked=1
        )
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again later."
        )

@router.post("/logout-all", response_model=LogoutResponse)
async def logout_all_sessions(
    current_user: Candidate = Depends(get_current_user)
):
    """Logout user from all sessions"""
    try:
        # Revoke refresh token
        await revoke_refresh_token(current_user.id)
        
        # Simple session management without Redis
        # For now, just log the logout action
        session_keys = []  # No Redis sessions to manage
        
        logger.info(f"User logged out from all sessions: {current_user.email}")
        
        return LogoutResponse(
            message="Successfully logged out from all sessions",
            sessions_revoked=len(session_keys)
        )
        
    except Exception as e:
        logger.error(f"Logout all sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again later."
        )

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: Candidate = Depends(get_current_active_user)
):
    """Get current user profile"""
    return current_user

@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    current_user: Candidate = Depends(get_current_active_user)
):
    """Get user's active sessions (admin only)"""
    try:
        # This would require additional implementation to track session details
        # For now, return basic session count
        active_sessions = await get_active_sessions_count(current_user.id)
        
        return [
            SessionInfo(
                session_id="session_id",
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                ip_address="127.0.0.1",
                user_agent="Unknown"
            )
        ]
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: Candidate = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Change user password"""
    try:
        # Validate current password
        if not verify_password(current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        is_valid, message = validate_password_with_feedback(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Hash new password
        new_password_hash = get_password_hash(new_password)
        
        # Update password
        current_user.password_hash = new_password_hash
        await db.commit()
        
        # Revoke all sessions to force re-login
        await revoke_refresh_token(current_user.id)
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return {"message": "Password changed successfully. Please login again."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest):
    """Request password reset for candidate"""
    try:
        email = request.email.strip().lower()
        
        # Use direct connection for better performance
        async with global_pool.acquire() as conn:
            # Check if user exists
            user_row = await conn.fetchrow(
                """
                SELECT id, name, email FROM candidates 
                WHERE email = $1
                """,
                email
            )
            
            if not user_row:
                # Return success even if user doesn't exist (security best practice)
                return {"message": "If the email exists, a password reset link has been sent"}
            
            user_id, user_name, user_email = user_row
            
            # Generate reset token (expires in 1 hour)
            reset_token = create_access_token(
                data={"sub": user_email, "user_id": str(user_id), "purpose": "password_reset"},
                expires_delta=timedelta(hours=1)
            )
            
            # Store reset token in database (you might want to create a separate table for this)
            await conn.execute(
                """
                UPDATE candidates 
                SET reset_token = $1, reset_token_expires = NOW() + INTERVAL '1 hour'
                WHERE id = $2
                """,
                reset_token, user_id
            )
            
            # Send password reset email
            try:
                print(f"DEBUG: Sending password reset email to {user_email}")
                email_success = await email_service.send_password_reset_email(
                    candidate_email=user_email,
                    candidate_name=user_name,
                    reset_token=reset_token
                )
                
                if email_success:
                    logger.info(f"Password reset email sent successfully to {user_email}")
                    print(f"DEBUG: Password reset email sent successfully to {user_email}")
                else:
                    logger.error(f"Password reset email failed to send to {user_email}")
                    print(f"DEBUG: Password reset email failed to send to {user_email}")
                    
            except Exception as e:
                logger.error(f"Failed to send password reset email to {user_email}: {str(e)}")
                print(f"DEBUG: Exception sending password reset email: {str(e)}")
            
            return {"message": "If the email exists, a password reset link has been sent"}
            
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/confirm-password-reset")
async def confirm_password_reset(request: PasswordResetConfirm):
    """Confirm password reset with token"""
    try:
        token = request.token
        new_password = request.new_password
        
        # Verify reset token
        try:
            payload = jwt.decode(
                token, 
                SecurityConfig.SECRET_KEY, 
                algorithms=[SecurityConfig.ALGORITHM]
            )
            
            if payload.get("purpose") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token"
                )
                
            user_email = payload.get("sub")
            user_id = payload.get("user_id")
            
            if not user_email or not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token"
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Use direct connection for better performance
        async with global_pool.acquire() as conn:
            # Verify token in database
            user_row = await conn.fetchrow(
                """
                SELECT id, name, email FROM candidates 
                WHERE id = $1 AND email = $2 AND reset_token = $3 
                AND reset_token_expires > NOW()
                """,
                int(user_id), user_email, token
            )
            
            if not user_row:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
            
            # Hash new password
            hashed_password = hash_password(new_password)
            
            # Update password and clear reset token
            await conn.execute(
                """
                UPDATE candidates 
                SET password_hash = $1, reset_token = NULL, reset_token_expires = NULL
                WHERE id = $2
                """,
                hashed_password, int(user_id)
            )
            
            logger.info(f"Password reset successfully for user {user_email}")
            
            return {"message": "Password has been reset successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 