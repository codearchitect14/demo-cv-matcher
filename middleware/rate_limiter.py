from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
import asyncio
from collections import defaultdict
import logging
from typing import Optional, Dict, Any
from config.security import SecurityConfig, verify_token
from config.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class SimpleRateLimiter:
    """Simple in-memory rate limiter for development"""
    
    def __init__(self):
        # In-memory storage for rate limiting
        self.request_counts = defaultdict(list)
        
        # Rate limit configurations by endpoint type and user role
        self.limits = {
            "auth": {
                "anonymous": {"requests": 5, "window": 60},  # 5 requests per minute for anonymous
                "user": {"requests": 10, "window": 60},      # 10 requests per minute for users
                "admin": {"requests": 50, "window": 60},     # 50 requests per minute for admins
            },
            "search": {
                "anonymous": {"requests": 10, "window": 60},
                "user": {"requests": 100, "window": 60},
                "admin": {"requests": 500, "window": 60},
            },
            "api": {
                "anonymous": {"requests": 20, "window": 60},
                "user": {"requests": 200, "window": 60},
                "admin": {"requests": 1000, "window": 60},
            },
            "default": {
                "anonymous": {"requests": 30, "window": 60},
                "user": {"requests": 300, "window": 60},
                "admin": {"requests": 1500, "window": 60},
            }
        }
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (IP address with additional headers)"""
        # Get real IP from headers (for proxy/load balancer setups)
        real_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For")
        if real_ip:
            # Take the first IP if multiple are present
            client_ip = real_ip.split(",")[0].strip()
        else:
            client_ip = request.client.host
        
        # Add user agent for additional uniqueness
        user_agent = request.headers.get("User-Agent", "Unknown")
        return f"{client_ip}:{user_agent[:50]}"
    
    def _get_user_id(self, request: Request) -> Optional[int]:
        """Extract user ID from JWT token if present"""
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                token_data = verify_token(token)
                if token_data and token_data.user_id:
                    return token_data.user_id
        except Exception as e:
            logger.debug(f"Failed to extract user ID from token: {e}")
        return None
    
    def _get_user_role(self, request: Request) -> str:
        """Extract user role from JWT token if present"""
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                token_data = verify_token(token)
                if token_data and token_data.role:
                    return token_data.role
        except Exception as e:
            logger.debug(f"Failed to extract user role from token: {e}")
        return "anonymous"
    
    def _get_endpoint_type(self, request: Request) -> str:
        """Determine endpoint type for rate limiting"""
        path = request.url.path.lower()
        
        if path.startswith("/auth"):
            return "auth"
        elif path.startswith("/search") or path.startswith("/recommendations"):
            return "search"
        elif path.startswith("/api"):
            return "api"
        else:
            return "default"
    
    def _get_rate_limit_key(self, request: Request) -> str:
        """Generate key for rate limiting"""
        client_id = self._get_client_id(request)
        user_id = self._get_user_id(request)
        endpoint_type = self._get_endpoint_type(request)
        
        if user_id:
            return f"user:{user_id}:{endpoint_type}"
        else:
            return f"ip:{client_id}:{endpoint_type}"
    
    def _is_rate_limited(self, request: Request) -> tuple[bool, Dict[str, Any]]:
        """Check if request is rate limited"""
        try:
            key = self._get_rate_limit_key(request)
            user_role = self._get_user_role(request)
            endpoint_type = self._get_endpoint_type(request)
            
            # Get limits for this endpoint and user role
            limits = self.limits.get(endpoint_type, self.limits["default"])
            user_limits = limits.get(user_role, limits["anonymous"])
            
            max_requests = user_limits["requests"]
            window_seconds = user_limits["window"]
            
            # Get current timestamp
            current_time = time.time()
            
            # Clean old requests
            self.request_counts[key] = [
                req_time for req_time in self.request_counts[key]
                if current_time - req_time < window_seconds
            ]
            
            # Check if limit exceeded
            request_count = len(self.request_counts[key])
            is_limited = request_count >= max_requests
            
            # Add current request if not limited
            if not is_limited:
                self.request_counts[key].append(current_time)
            
            details = {
                "key": key,
                "user_role": user_role,
                "endpoint_type": endpoint_type,
                "current_requests": request_count,
                "max_requests": max_requests,
                "window_seconds": window_seconds,
                "reset_time": current_time + window_seconds
            }
            
            return is_limited, details
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request if rate limiting fails
            return False, {"error": str(e)}
    
    async def __call__(self, request: Request, call_next):
        """Rate limiting middleware"""
        try:
            # Check rate limit
            is_limited, details = self._is_rate_limited(request)
            
            if is_limited:
                logger.warning(f"Rate limit exceeded: {details}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": details.get("window_seconds", 60)
                    },
                    headers={
                        "X-RateLimit-Limit": str(details.get("max_requests", 0)),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(details.get("reset_time", 0))
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            remaining = details.get("max_requests", 0) - details.get("current_requests", 0)
            response.headers["X-RateLimit-Limit"] = str(details.get("max_requests", 0))
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
            response.headers["X-RateLimit-Reset"] = str(details.get("reset_time", 0))
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request if rate limiting fails
            return await call_next(request)
    
    async def clear_user_limits(self, user_id: int):
        """Clear rate limits for a specific user"""
        try:
            keys_to_remove = [key for key in self.request_counts.keys() if f"user:{user_id}:" in key]
            for key in keys_to_remove:
                del self.request_counts[key]
            logger.info(f"Cleared rate limits for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing user limits: {e}")
    
    async def clear_ip_limits(self, client_id: str):
        """Clear rate limits for a specific IP"""
        try:
            keys_to_remove = [key for key in self.request_counts.keys() if f"ip:{client_id}:" in key]
            for key in keys_to_remove:
                del self.request_counts[key]
            logger.info(f"Cleared rate limits for IP {client_id}")
        except Exception as e:
            logger.error(f"Error clearing IP limits: {e}")
    
    async def get_rate_limit_status(self, request: Request) -> Dict[str, Any]:
        """Get current rate limit status"""
        try:
            key = self._get_rate_limit_key(request)
            user_role = self._get_user_role(request)
            endpoint_type = self._get_endpoint_type(request)
            
            limits = self.limits.get(endpoint_type, self.limits["default"])
            user_limits = limits.get(user_role, limits["anonymous"])
            
            current_time = time.time()
            window_seconds = user_limits["window"]
            
            # Clean old requests
            self.request_counts[key] = [
                req_time for req_time in self.request_counts[key]
                if current_time - req_time < window_seconds
            ]
            
            request_count = len(self.request_counts[key])
            max_requests = user_limits["requests"]
            
            return {
                "key": key,
                "user_role": user_role,
                "endpoint_type": endpoint_type,
                "current_requests": request_count,
                "max_requests": max_requests,
                "remaining_requests": max(0, max_requests - request_count),
                "window_seconds": window_seconds,
                "reset_time": current_time + window_seconds
            }
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {"error": str(e)}

# Create global rate limiter instance
rate_limiter = SimpleRateLimiter() 