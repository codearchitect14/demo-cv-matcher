from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Union
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import secrets
import logging

from config.database import get_db_session
from config.security import (
    SecurityConfig, verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token, store_refresh_token, validate_refresh_token,
    revoke_refresh_token, store_user_session, validate_user_session, 
    revoke_user_session, get_active_sessions_count, validate_password_with_feedback
)
from models.candidate import Candidate
from models.recruiter import Recruiter
from db.crud.candidate import candidate as candidate_crud
from db.crud.recruiter import recruiter as recruiter_crud
from schemas.validation import UserRegistrationValidation, EmailValidation, PasswordValidation
from fastapi.security import OAuth2PasswordBearer

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
    """Get current authenticated user"""
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
        
        # Get user from database
        user = await candidate_crud.get_by_email(db, email=token_data.email)
        if user is None:
            raise credentials_exception
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception

async def get_current_recruiter(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> Recruiter:
    """Get current authenticated recruiter"""
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
        
        # Get recruiter from database
        recruiter = await recruiter_crud.get_by_email(db, email=token_data.email)
        if recruiter is None:
            raise credentials_exception
        
        return recruiter
        
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
        
        # Try to get candidate first
        user = await candidate_crud.get_by_email(db, email=token_data.email)
        if user is not None:
            logger.info(f"Found candidate user: {user.id} - {user.email} with role: {getattr(user, 'role', 'N/A')}")
            return user
        
        # Try to get recruiter
        recruiter = await recruiter_crud.get_by_email(db, email=token_data.email)
        if recruiter is not None:
            logger.info(f"Found recruiter user: {recruiter.id} - {recruiter.email} with role: {getattr(recruiter, 'role', 'N/A')}")
            return recruiter
        
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
        
        # Try to get recruiter FIRST (prioritize recruiters)
        recruiter = await recruiter_crud.get_by_email(db, email=token_data.email)
        if recruiter is not None:
            logger.info(f"Found recruiter user: {recruiter.id} - {recruiter.email} with role: {getattr(recruiter, 'role', 'N/A')}")
            return recruiter
        
        # Try to get candidate as fallback
        user = await candidate_crud.get_by_email(db, email=token_data.email)
        if user is not None:
            logger.info(f"Found candidate user: {user.id} - {user.email} with role: {getattr(user, 'role', 'N/A')}")
            return user
        
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
    db: AsyncSession = Depends(get_db_session),
    request: Request = None
):
    """Register a new user with comprehensive validation"""
    try:
        # Check if user already exists
        existing_user = await candidate_crud.get_by_email(db, email=user_data.email)
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
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user_dict = user_data.dict()
        user_dict["password_hash"] = hashed_password
        del user_dict["password"]
        
        # Set default role
        user_dict["role"] = "user"
        
        user = await candidate_crud.create(db, obj_in=user_dict)
        
        # Create tokens
        access_token_expires = timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role}
        )
        
        # Store refresh token
        await store_refresh_token(user.id, refresh_token)
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        await store_user_session(user.id, session_id)
        
        # Log registration
        logger.info(f"New user registered: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            role=user.role
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
    """Login user with session management"""
    try:
        # Validate email format
        email_validation = EmailValidation(email=user_credentials.email)
        email = email_validation.email
        
        # Get user
        user = await candidate_crud.get_by_email(db, email=email)
        if not user or not verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password. Please check your credentials and try again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check active sessions limit
        active_sessions = await get_active_sessions_count(user.id)
        if active_sessions >= SecurityConfig.MAX_SESSIONS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Maximum sessions limit reached ({SecurityConfig.MAX_SESSIONS_PER_USER}). Please logout from other devices."
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role}
        )
        
        # Store refresh token
        await store_refresh_token(user.id, refresh_token)
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        await store_user_session(user.id, session_id)
        
        # Log login
        logger.info(f"User logged in: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            role=user.role
        )
        
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