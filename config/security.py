import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel
# import redis.asyncio as redis  # Temporarily disabled
from dotenv import load_dotenv

load_dotenv()

# Security Configuration
class SecurityConfig:
    # JWT Settings
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # Password Security
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # Rate Limiting
    RATE_LIMIT_AUTH = int(os.getenv("RATE_LIMIT_AUTH", "5"))
    RATE_LIMIT_SEARCH = int(os.getenv("RATE_LIMIT_SEARCH", "20"))
    RATE_LIMIT_DEFAULT = int(os.getenv("RATE_LIMIT_DEFAULT", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Session Management
    SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))
    MAX_SESSIONS_PER_USER = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Input Validation
    MAX_STRING_LENGTH = 1000
    MAX_EMAIL_LENGTH = 254
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 2000
    
    # SQL Injection Prevention
    MAX_QUERY_LENGTH = 10000  # for JSON / URL-encoded requests
    # Max allowed body for multipart uploads (bytes). Defaults to 100MB.
    MAX_UPLOAD_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_CONTENT_LENGTH", str(100 * 1024 * 1024)))
    
    # Response Time Limits
    MAX_RESPONSE_TIME = float(os.getenv("MAX_RESPONSE_TIME", "8.0"))  # Maximum response time in seconds
    SLOW_RESPONSE_THRESHOLD = float(os.getenv("SLOW_RESPONSE_THRESHOLD", "5.0"))  # Log slow responses over this threshold
    
    FORBIDDEN_SQL_KEYWORDS = [
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", 
        "UPDATE", "EXEC", "EXECUTE", "UNION", "SELECT", "SCRIPT"
    ]

# Password Hashing - Optimized for performance using bcrypt directly
# Default rounds for new hashes
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "10"))

# Precomputed dummy hash to simulate constant-time verification when user is missing
# Generated once at import time to avoid per-request overhead
_DUMMY_PASSWORD = b"dummy_password_for_constant_time"
_DUMMY_SALT = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
_DUMMY_BCRYPT_HASH: bytes = bcrypt.hashpw(_DUMMY_PASSWORD, _DUMMY_SALT)

# In-memory storage for development (replaces Redis)
_refresh_tokens = {}
_user_sessions = {}

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly.
    Returns False on any error to avoid leaking details.
    """
    try:
        if not plain_password or not hashed_password:
            return False
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode("utf-8")
        else:
            hashed_bytes = hashed_password
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_bytes)
    except Exception:
        # Swallow bcrypt/backend errors and return False for safety
        return False

def get_password_hash(password: str) -> str:
    """Generate bcrypt password hash with configured rounds."""
    if not password:
        raise ValueError("Password must not be empty")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def simulate_constant_time_verify() -> None:
    """Perform a fixed-cost bcrypt check to mitigate timing side-channels.
    Always returns None and should not affect auth outcome.
    """
    try:
        bcrypt.checkpw(_DUMMY_PASSWORD, _DUMMY_BCRYPT_HASH)
    except Exception:
        # Ignore any backend issues; purpose is only to burn comparable CPU time
        pass

def validate_password_strength(password: str) -> bool:
    """Validate password strength according to security policy"""
    if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
        return False
    if len(password) > SecurityConfig.PASSWORD_MAX_LENGTH:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    # More flexible password requirements
    requirements_met = 0
    if has_upper:
        requirements_met += 1
    if has_lower:
        requirements_met += 1
    if has_digit:
        requirements_met += 1
    if has_special:
        requirements_met += 1
    
    # Require at least 3 out of 4 criteria to be met
    return requirements_met >= 3

def get_password_requirements() -> str:
    """Get password requirements as a user-friendly string"""
    return "Password must be 8-128 characters and contain at least 3 of: uppercase letter, lowercase letter, number, or special character"

def validate_password_with_feedback(password: str) -> tuple[bool, str]:
    """Validate password and return detailed feedback"""
    if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {SecurityConfig.PASSWORD_MIN_LENGTH} characters"
    if len(password) > SecurityConfig.PASSWORD_MAX_LENGTH:
        return False, f"Password must be no more than {SecurityConfig.PASSWORD_MAX_LENGTH} characters"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    missing_requirements = []
    if not has_upper:
        missing_requirements.append("uppercase letter")
    if not has_lower:
        missing_requirements.append("lowercase letter")
    if not has_digit:
        missing_requirements.append("number")
    if not has_special:
        missing_requirements.append("special character")
    
    requirements_met = 4 - len(missing_requirements)
    
    if requirements_met >= 3:
        return True, "Password meets requirements"
    else:
        return False, f"Password must contain at least 3 of: {', '.join(['uppercase letter', 'lowercase letter', 'number', 'special character'])}"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SecurityConfig.SECRET_KEY, algorithms=[SecurityConfig.ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role", "user")
        
        if email is None:
            return None
            
        return TokenData(email=email, user_id=user_id, role=role)
    except JWTError:
        return None

async def store_refresh_token(user_id: int, refresh_token: str) -> None:
    """Store refresh token in memory with expiration"""
    key = f"refresh_token:{user_id}"
    _refresh_tokens[key] = {
        "token": refresh_token,
        "expires": datetime.utcnow() + timedelta(days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS)
    }

async def validate_refresh_token(user_id: int, refresh_token: str) -> bool:
    """Validate refresh token against stored token"""
    key = f"refresh_token:{user_id}"
    if key not in _refresh_tokens:
        return False
    
    stored_data = _refresh_tokens[key]
    if datetime.utcnow() > stored_data["expires"]:
        del _refresh_tokens[key]
        return False
    
    return stored_data["token"] == refresh_token

async def revoke_refresh_token(user_id: int) -> None:
    """Revoke refresh token"""
    key = f"refresh_token:{user_id}"
    if key in _refresh_tokens:
        del _refresh_tokens[key]

async def store_user_session(user_id: int, session_id: str) -> None:
    """Store user session in memory"""
    key = f"session:{user_id}:{session_id}"
    _user_sessions[key] = {
        "active": True,
        "expires": datetime.utcnow() + timedelta(hours=SecurityConfig.SESSION_EXPIRE_HOURS)
    }

async def validate_user_session(user_id: int, session_id: str) -> bool:
    """Validate user session"""
    key = f"session:{user_id}:{session_id}"
    if key not in _user_sessions:
        return False
    
    session_data = _user_sessions[key]
    if datetime.utcnow() > session_data["expires"]:
        del _user_sessions[key]
        return False
    
    return session_data["active"]

async def revoke_user_session(user_id: int, session_id: str) -> None:
    """Revoke user session"""
    key = f"session:{user_id}:{session_id}"
    if key in _user_sessions:
        del _user_sessions[key]

async def get_active_sessions_count(user_id: int) -> int:
    """Get count of active sessions for user"""
    pattern = f"session:{user_id}:"
    count = 0
    current_time = datetime.utcnow()
    
    # Clean expired sessions and count active ones
    keys_to_remove = []
    for key, session_data in _user_sessions.items():
        if key.startswith(pattern):
            if current_time > session_data["expires"]:
                keys_to_remove.append(key)
            elif session_data["active"]:
                count += 1
    
    # Remove expired sessions
    for key in keys_to_remove:
        del _user_sessions[key]
    
    return count

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters except newline and tab
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    # Limit length
    if len(text) > SecurityConfig.MAX_STRING_LENGTH:
        text = text[:SecurityConfig.MAX_STRING_LENGTH]
    
    return text.strip()

def validate_sql_injection(text: str) -> bool:
    """Check for potential SQL injection patterns"""
    if not text:
        return True
    
    text_upper = text.upper()
    
    # Check for forbidden SQL keywords
    for keyword in SecurityConfig.FORBIDDEN_SQL_KEYWORDS:
        if keyword in text_upper:
            return False
    
    # Check for common SQL injection patterns
    dangerous_patterns = [
        "';", "';--", "';/*", "';#", 
        "'; DROP", "'; DELETE", "'; INSERT",
        "'; UPDATE", "'; ALTER", "'; CREATE"
    ]
    
    for pattern in dangerous_patterns:
        if pattern in text_upper:
            return False
    
    return True 