import time
import hashlib
import json
import logging
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    """Redis-based rate limiter with distributed session management"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.fallback_limits = {}  # In-memory fallback
        self.fallback_enabled = True
        
        # Rate limit configurations
        self.limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'auth': {'requests': 10, 'window': 300},       # 10 auth attempts per 5 minutes
            'api': {'requests': 1000, 'window': 3600},     # 1000 API calls per hour
            'search': {'requests': 50, 'window': 300},      # 50 searches per 5 minutes
            'upload': {'requests': 10, 'window': 3600},     # 10 uploads per hour
            'admin': {'requests': 500, 'window': 3600},     # 500 admin calls per hour
        }
        
        # User role limits
        self.role_limits = {
            'admin': {'requests': 1000, 'window': 3600},
            'recruiter': {'requests': 500, 'window': 3600},
            'candidate': {'requests': 200, 'window': 3600},
            'guest': {'requests': 50, 'window': 3600},
        }
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            await self.redis_client.ping()
            logger.info("[SUCCESS] Redis rate limiter connected successfully")
            self.fallback_enabled = False
        except Exception as e:
            logger.warning(f"[WARNING] Redis connection failed, using fallback: {e}")
            self.redis_client = None
            self.fallback_enabled = True
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis rate limiter disconnected")
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get user ID from token first
        user_id = self._extract_user_id(request)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token"""
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                # Decode JWT token to get user ID
                # This is a simplified version - you should use proper JWT decoding
                return f"user_{hash(token) % 10000}"
        except Exception:
            pass
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'
    
    def _get_rate_limit_key(self, identifier: str, endpoint: str) -> str:
        """Generate rate limit key"""
        return f"rate_limit:{identifier}:{endpoint}"
    
    def _get_limit_config(self, request: Request) -> Dict:
        """Get rate limit configuration based on endpoint and user role"""
        path = request.url.path
        
        # Determine endpoint type
        if '/auth/' in path:
            return self.limits['auth']
        elif '/api/v1/search' in path:
            return self.limits['search']
        elif '/api/v1/upload' in path or '/upload' in path:
            return self.limits['upload']
        elif '/admin/' in path:
            return self.limits['admin']
        else:
            return self.limits['api']
    
    async def _check_redis_limit(self, key: str, limit_config: Dict) -> Tuple[bool, Dict]:
        """Check rate limit using Redis"""
        try:
            current_time = int(time.time())
            window_start = current_time - limit_config['window']
            
            # Get current requests in window
            pipeline = self.redis_client.pipeline()
            pipeline.zremrangebyscore(key, 0, window_start)
            pipeline.zcard(key)
            pipeline.zadd(key, {str(current_time): current_time})
            pipeline.expire(key, limit_config['window'])
            results = await pipeline.execute()
            
            current_requests = results[1]
            limit_reached = current_requests >= limit_config['requests']
            
            return limit_reached, {
                'current': current_requests,
                'limit': limit_config['requests'],
                'window': limit_config['window'],
                'reset_time': current_time + limit_config['window']
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Redis rate limit check failed: {e}")
            return False, {}
    
    def _check_fallback_limit(self, identifier: str, endpoint: str, limit_config: Dict) -> Tuple[bool, Dict]:
        """Check rate limit using in-memory fallback"""
        key = f"{identifier}:{endpoint}"
        current_time = time.time()
        
        if key not in self.fallback_limits:
            self.fallback_limits[key] = {'requests': [], 'limit': limit_config['requests'], 'window': limit_config['window']}
        
        # Clean old requests
        window_start = current_time - limit_config['window']
        self.fallback_limits[key]['requests'] = [
            req_time for req_time in self.fallback_limits[key]['requests']
            if req_time > window_start
        ]
        
        # Check limit
        current_requests = len(self.fallback_limits[key]['requests'])
        limit_reached = current_requests >= limit_config['requests']
        
        # Add current request
        if not limit_reached:
            self.fallback_limits[key]['requests'].append(current_time)
        
        return limit_reached, {
            'current': current_requests,
            'limit': limit_config['requests'],
            'window': limit_config['window'],
            'reset_time': current_time + limit_config['window']
        }
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, Dict]:
        """Check if request exceeds rate limit"""
        identifier = self._get_client_identifier(request)
        endpoint = request.url.path
        limit_config = self._get_limit_config(request)
        
        if self.redis_client and not self.fallback_enabled:
            return await self._check_redis_limit(
                self._get_rate_limit_key(identifier, endpoint),
                limit_config
            )
        else:
            return self._check_fallback_limit(identifier, endpoint, limit_config)
    
    async def get_rate_limit_info(self, request: Request) -> Dict:
        """Get current rate limit information"""
        identifier = self._get_client_identifier(request)
        endpoint = request.url.path
        limit_config = self._get_limit_config(request)
        
        if self.redis_client and not self.fallback_enabled:
            key = self._get_rate_limit_key(identifier, endpoint)
            try:
                current_requests = await self.redis_client.zcard(key)
                return {
                    'current': current_requests,
                    'limit': limit_config['requests'],
                    'window': limit_config['window'],
                    'remaining': max(0, limit_config['requests'] - current_requests)
                }
            except Exception:
                return {'error': 'Unable to get rate limit info'}
        else:
            # Fallback implementation
            key = f"{identifier}:{endpoint}"
            if key in self.fallback_limits:
                current_requests = len(self.fallback_limits[key]['requests'])
                return {
                    'current': current_requests,
                    'limit': limit_config['requests'],
                    'window': limit_config['window'],
                    'remaining': max(0, limit_config['requests'] - current_requests)
                }
            else:
                return {
                    'current': 0,
                    'limit': limit_config['requests'],
                    'window': limit_config['window'],
                    'remaining': limit_config['requests']
                }

# Global rate limiter instance
rate_limiter = RedisRateLimiter()

async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    try:
        # Check rate limit
        limit_reached, limit_info = await rate_limiter.check_rate_limit(request)
        
        if limit_reached:
            # Return rate limit exceeded response
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "limit_info": limit_info,
                    "retry_after": limit_info.get('window', 3600)
                },
                headers={
                    "X-RateLimit-Limit": str(limit_info.get('limit', 100)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(limit_info.get('reset_time', 0)),
                    "Retry-After": str(limit_info.get('window', 3600))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit_info.get('limit', 100))
        response.headers["X-RateLimit-Remaining"] = str(limit_info.get('limit', 100) - limit_info.get('current', 0))
        response.headers["X-RateLimit-Reset"] = str(limit_info.get('reset_time', 0))
        
        return response
        
    except Exception as e:
        logger.error(f"[ERROR] Rate limiting middleware error: {e}")
        # Continue without rate limiting if there's an error
        return await call_next(request) 