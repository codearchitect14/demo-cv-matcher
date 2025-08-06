import json
import hashlib
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from config.security import SecurityConfig

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for query results and frequently accessed data"""
    
    def __init__(self):
        self.redis_client = redis.from_url(SecurityConfig.REDIS_URL, decode_responses=True)
        self.default_ttl = 3600  # 1 hour default TTL
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a unique cache key based on parameters"""
        # Create a sorted string of key-value pairs
        sorted_params = sorted(kwargs.items())
        param_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        
        # Create hash for consistent key length
        hash_object = hashlib.md5(param_string.encode())
        return f"{prefix}:{hash_object.hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            return await self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            return bool(await self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def get_or_set(self, key: str, getter_func, ttl: int = None) -> Any:
        """Get from cache or set using getter function"""
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Get fresh value
        fresh_value = await getter_func()
        if fresh_value is not None:
            await self.set(key, fresh_value, ttl)
        
        return fresh_value
    
    # Candidate-specific caching methods
    async def get_candidate(self, candidate_id: int) -> Optional[Dict]:
        """Get candidate from cache"""
        key = self._generate_cache_key("candidate", id=candidate_id)
        return await self.get(key)
    
    async def set_candidate(self, candidate_id: int, candidate_data: Dict, ttl: int = 1800) -> bool:
        """Set candidate in cache (30 minutes TTL)"""
        key = self._generate_cache_key("candidate", id=candidate_id)
        return await self.set(key, candidate_data, ttl)
    
    async def invalidate_candidate(self, candidate_id: int) -> bool:
        """Invalidate candidate cache"""
        key = self._generate_cache_key("candidate", id=candidate_id)
        return await self.delete(key)
    
    async def get_candidates_list(self, skip: int, limit: int, filters: Dict = None) -> Optional[List[Dict]]:
        """Get candidates list from cache"""
        key = self._generate_cache_key("candidates_list", skip=skip, limit=limit, filters=str(filters))
        return await self.get(key)
    
    async def set_candidates_list(self, skip: int, limit: int, filters: Dict, candidates_data: List[Dict], ttl: int = 900) -> bool:
        """Set candidates list in cache (15 minutes TTL)"""
        key = self._generate_cache_key("candidates_list", skip=skip, limit=limit, filters=str(filters))
        return await self.set(key, candidates_data, ttl)
    
    # Job-specific caching methods
    async def get_job(self, job_id: int) -> Optional[Dict]:
        """Get job from cache"""
        key = self._generate_cache_key("job", id=job_id)
        return await self.get(key)
    
    async def set_job(self, job_id: int, job_data: Dict, ttl: int = 1800) -> bool:
        """Set job in cache (30 minutes TTL)"""
        key = self._generate_cache_key("job", id=job_id)
        return await self.set(key, job_data, ttl)
    
    async def invalidate_job(self, job_id: int) -> bool:
        """Invalidate job cache"""
        key = self._generate_cache_key("job", id=job_id)
        return await self.delete(key)
    
    async def get_jobs_list(self, skip: int, limit: int, filters: Dict = None) -> Optional[List[Dict]]:
        """Get jobs list from cache"""
        key = self._generate_cache_key("jobs_list", skip=skip, limit=limit, filters=str(filters))
        return await self.get(key)
    
    async def set_jobs_list(self, skip: int, limit: int, filters: Dict, jobs_data: List[Dict], ttl: int = 900) -> bool:
        """Set jobs list in cache (15 minutes TTL)"""
        key = self._generate_cache_key("jobs_list", skip=skip, limit=limit, filters=str(filters))
        return await self.set(key, jobs_data, ttl)
    
    # Search-specific caching methods
    async def get_search_results(self, search_type: str, query: str, filters: Dict = None) -> Optional[List[Dict]]:
        """Get search results from cache"""
        key = self._generate_cache_key("search", type=search_type, query=query, filters=str(filters))
        return await self.get(key)
    
    async def set_search_results(self, search_type: str, query: str, filters: Dict, results: List[Dict], ttl: int = 600) -> bool:
        """Set search results in cache (10 minutes TTL)"""
        key = self._generate_cache_key("search", type=search_type, query=query, filters=str(filters))
        return await self.set(key, results, ttl)
    
    # Statistics caching methods
    async def get_stats(self, stats_type: str) -> Optional[Dict]:
        """Get statistics from cache"""
        key = self._generate_cache_key("stats", type=stats_type)
        return await self.get(key)
    
    async def set_stats(self, stats_type: str, stats_data: Dict, ttl: int = 3600) -> bool:
        """Set statistics in cache (1 hour TTL)"""
        key = self._generate_cache_key("stats", type=stats_type)
        return await self.set(key, stats_data, ttl)
    
    # Bulk invalidation methods
    async def invalidate_all_candidates(self) -> int:
        """Invalidate all candidate-related cache"""
        return await self.delete_pattern("candidate:*")
    
    async def invalidate_all_jobs(self) -> int:
        """Invalidate all job-related cache"""
        return await self.delete_pattern("job:*")
    
    async def invalidate_all_search(self) -> int:
        """Invalidate all search-related cache"""
        return await self.delete_pattern("search:*")
    
    async def invalidate_all_stats(self) -> int:
        """Invalidate all statistics cache"""
        return await self.delete_pattern("stats:*")
    
    # Cache warming methods
    async def warm_candidate_cache(self, candidate_ids: List[int], getter_func) -> int:
        """Warm cache with multiple candidates"""
        warmed_count = 0
        for candidate_id in candidate_ids:
            try:
                candidate_data = await getter_func(candidate_id)
                if candidate_data:
                    await self.set_candidate(candidate_id, candidate_data)
                    warmed_count += 1
            except Exception as e:
                logger.error(f"Failed to warm cache for candidate {candidate_id}: {e}")
        return warmed_count
    
    async def warm_jobs_cache(self, job_ids: List[int], getter_func) -> int:
        """Warm cache with multiple jobs"""
        warmed_count = 0
        for job_id in job_ids:
            try:
                job_data = await getter_func(job_id)
                if job_data:
                    await self.set_job(job_id, job_data)
                    warmed_count += 1
            except Exception as e:
                logger.error(f"Failed to warm cache for job {job_id}: {e}")
        return warmed_count
    
    # Cache health and monitoring
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
    
    async def clear_all_cache(self) -> bool:
        """Clear all cache (use with caution)"""
        try:
            await self.redis_client.flushdb()
            logger.info("All cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

# Global cache service instance
cache_service = CacheService() 