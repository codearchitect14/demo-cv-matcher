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
        """Initialize rate limiter with Redis and fallback cache"""
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.fallback_enabled = False
        
        # Rate limiting configuration
        self.limits = {
            'api': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 5, 'window': 60},   # 5 auth attempts per minute
            'search': {'requests': 50, 'window': 60}, # 50 searches per minute
            'upload': {'requests': 10, 'window': 60}, # 10 uploads per minute
            'default': {'requests': 1000, 'window': 3600}  # 1000 requests per hour
        }
        
        # Fallback cache with LRU eviction and memory limits
        self.fallback_limits = {}
        self.fallback_cache_size = 1000  # Maximum number of entries
        self.fallback_memory_limit = 50 * 1024 * 1024  # 50MB memory limit
        self.fallback_access_times = {}  # Track access times for LRU
        self.fallback_memory_usage = 0  # Track memory usage
        
        # LRU cache implementation
        self.lru_cache = {}
        self.lru_order = []  # List to maintain access order
        
        logger.info("Rate limiter initialized with fallback cache")
    
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
            # Admin not explicitly configured; use a conservative default
            return self.limits.get('admin', self.limits['api'])
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
    
    def _cleanup_fallback_cache(self):
        """Clean up fallback cache using LRU eviction"""
        try:
            current_time = time.time()
            
            # Remove expired entries first
            expired_keys = []
            for key, data in self.fallback_limits.items():
                window_start = current_time - data['window']
                data['requests'] = [
                    req_time for req_time in data['requests']
                    if req_time > window_start
                ]
                
                # Remove empty entries
                if not data['requests']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_from_fallback_cache(key)
            
            # Check memory usage and apply LRU eviction if needed
            while (len(self.fallback_limits) > self.fallback_cache_size or 
                   self.fallback_memory_usage > self.fallback_memory_limit):
                
                if not self.lru_order:
                    break
                
                # Remove least recently used entry
                oldest_key = self.lru_order.pop(0)
                if oldest_key in self.fallback_limits:
                    self._remove_from_fallback_cache(oldest_key)
                    logger.debug(f"LRU eviction: removed {oldest_key}")
            
        except Exception as e:
            logger.error(f"Error cleaning up fallback cache: {e}")
    
    def _remove_from_fallback_cache(self, key: str):
        """Remove entry from fallback cache and update memory tracking"""
        try:
            if key in self.fallback_limits:
                # Estimate memory usage (rough calculation)
                entry_size = len(str(self.fallback_limits[key])) * 2  # Rough estimate
                self.fallback_memory_usage = max(0, self.fallback_memory_usage - entry_size)
                
                del self.fallback_limits[key]
            
            if key in self.fallback_access_times:
                del self.fallback_access_times[key]
            
            if key in self.lru_cache:
                del self.lru_cache[key]
                
        except Exception as e:
            logger.error(f"Error removing from fallback cache: {e}")
    
    def _update_lru_order(self, key: str):
        """Update LRU order for a key"""
        try:
            # Remove from current position if exists
            if key in self.lru_order:
                self.lru_order.remove(key)
            
            # Add to end (most recently used)
            self.lru_order.append(key)
            
            # Update access time
            self.fallback_access_times[key] = time.time()
            
        except Exception as e:
            logger.error(f"Error updating LRU order: {e}")
    
    def _add_to_fallback_cache(self, key: str, data: Dict):
        """Add entry to fallback cache with memory tracking"""
        try:
            # Estimate memory usage
            entry_size = len(str(data)) * 2  # Rough estimate
            self.fallback_memory_usage += entry_size
            
            # Add to cache
            self.fallback_limits[key] = data
            
            # Update LRU order
            self._update_lru_order(key)
            
            # Cleanup if needed
            self._cleanup_fallback_cache()
            
        except Exception as e:
            logger.error(f"Error adding to fallback cache: {e}")
    
    def _check_fallback_limit(self, identifier: str, endpoint: str, limit_config: Dict) -> Tuple[bool, Dict]:
        """Check rate limit using in-memory fallback with LRU eviction"""
        key = f"{identifier}:{endpoint}"
        current_time = time.time()
        
        # Cleanup expired entries periodically
        if len(self.fallback_limits) % 10 == 0:  # Cleanup every 10th request
            self._cleanup_fallback_cache()
        
        if key not in self.fallback_limits:
            self.fallback_limits[key] = {
                'requests': [], 
                'limit': limit_config['requests'], 
                'window': limit_config['window']
            }
        
        # Clean old requests
        window_start = current_time - limit_config['window']
        self.fallback_limits[key]['requests'] = [
            req_time for req_time in self.fallback_limits[key]['requests']
            if req_time > window_start
        ]
        
        # Check limit
        current_requests = len(self.fallback_limits[key]['requests'])
        limit_reached = current_requests >= limit_config['requests']
        
        # Add current request if limit not reached
        if not limit_reached:
            self.fallback_limits[key]['requests'].append(current_time)
            # Update LRU order
            self._update_lru_order(key)
        
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