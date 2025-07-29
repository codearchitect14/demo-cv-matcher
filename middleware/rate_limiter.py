from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
import asyncio
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "auth": {"requests": 5, "window": 60},  # 5 requests per minute
            "search": {"requests": 10, "window": 60},  # 10 requests per minute
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
        }
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (IP address)"""
        return request.client.host
    
    def _get_endpoint_type(self, request: Request) -> str:
        """Determine endpoint type for rate limiting"""
        path = request.url.path
        
        if path.startswith("/api/v1/auth"):
            return "auth"
        elif path.startswith("/api/v1/search") or path.startswith("/api/v1/recommendations"):
            return "search"
        else:
            return "default"
    
    def _is_rate_limited(self, client_id: str, endpoint_type: str) -> bool:
        """Check if client is rate limited"""
        now = time.time()
        limit_config = self.limits[endpoint_type]
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < limit_config["window"]
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= limit_config["requests"]:
            return True
        
        # Add current request
        self.requests[client_id].append(now)
        return False
    
    async def __call__(self, request: Request, call_next):
        """Rate limiting middleware"""
        client_id = self._get_client_id(request)
        endpoint_type = self._get_endpoint_type(request)
        
        if self._is_rate_limited(client_id, endpoint_type):
            logger.warning(f"Rate limit exceeded for client {client_id} on {endpoint_type}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {self.limits[endpoint_type]['requests']} requests per {self.limits[endpoint_type]['window']} seconds."
                }
            )
        
        response = await call_next(request)
        return response

# Create rate limiter instance
rate_limiter = RateLimiter() 