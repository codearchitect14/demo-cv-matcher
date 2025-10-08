"""
Response caching service for frequently accessed data to improve API performance
"""
import time
import hashlib
import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ResponseCacheService:
    """In-memory response cache with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0
        
    def _generate_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and parameters"""
        # Sort params for consistent key generation
        sorted_params = sorted(params.items()) if params else []
        key_data = f"{endpoint}:{json.dumps(sorted_params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = []
        
        for key, data in self.cache.items():
            if current_time > data['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
    
    def _evict_lru(self):
        """Evict least recently used entries when cache is full"""
        if len(self.cache) < self.max_size:
            return
            
        # Sort by access time and remove oldest entries
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
        keys_to_remove = sorted_keys[:len(self.cache) - self.max_size + 10]  # Remove 10 extra
        
        for key, _ in keys_to_remove:
            self._remove_entry(key)
    
    def _remove_entry(self, key: str):
        """Remove entry from cache and access times"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]
    
    def get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached response if available and not expired"""
        key = self._generate_key(endpoint, params)
        current_time = time.time()
        
        if key in self.cache:
            data = self.cache[key]
            if current_time <= data['expires_at']:
                # Update access time for LRU
                self.access_times[key] = current_time
                self.hit_count += 1
                logger.debug(f"Cache HIT for {endpoint}")
                return data['response']
            else:
                # Expired, remove it
                self._remove_entry(key)
        
        self.miss_count += 1
        logger.debug(f"Cache MISS for {endpoint}")
        return None
    
    def set(self, endpoint: str, params: Dict[str, Any], response: Any, ttl: Optional[int] = None) -> None:
        """Cache response with TTL"""
        key = self._generate_key(endpoint, params)
        current_time = time.time()
        expires_at = current_time + (ttl or self.default_ttl)
        
        # Cleanup expired entries periodically
        if len(self.cache) % 50 == 0:
            self._cleanup_expired()
        
        # Evict LRU entries if needed
        self._evict_lru()
        
        # Store response
        self.cache[key] = {
            'response': response,
            'expires_at': expires_at,
            'created_at': current_time,
            'endpoint': endpoint
        }
        self.access_times[key] = current_time
        
        logger.debug(f"Cached response for {endpoint} (TTL: {ttl or self.default_ttl}s)")
    
    def invalidate(self, endpoint_pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        removed_count = 0
        keys_to_remove = []
        
        for key, data in self.cache.items():
            if endpoint_pattern in data['endpoint']:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_entry(key)
            removed_count += 1
        
        logger.info(f"Invalidated {removed_count} cache entries for pattern: {endpoint_pattern}")
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': f"{hit_rate:.2f}%",
            'total_requests': total_requests
        }
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()
        self.hit_count = 0
        self.miss_count = 0
        logger.info("Cache cleared")

# Global cache instance
response_cache = ResponseCacheService(max_size=1000, default_ttl=300)

def cache_response(ttl: int = 300):
    """Decorator to cache endpoint responses for FastAPI"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract endpoint and params for cache key
            endpoint = func.__name__
            params = {}
            
            # Extract query parameters from kwargs (FastAPI style)
            for key, value in kwargs.items():
                if value is not None:  # Only include non-None values
                    params[key] = value
            
            # Check cache first
            cached_response = response_cache.get(endpoint, params)
            if cached_response is not None:
                return cached_response
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            response_cache.set(endpoint, params, result, ttl)
            return result
        
        return wrapper
    return decorator
