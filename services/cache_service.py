import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from dataclasses import dataclass, asdict
import pickle
import gzip
import os

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_accessed: float = 0.0
    version: str = "1.0"

class RedisCacheService:
    """Advanced Redis caching service with compression, versioning, and analytics"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.compression_threshold = 1024  # Compress data larger than 1KB
        self.max_cache_size = 100 * 1024 * 1024  # 100MB
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'compressions': 0
        }
        
        # Cache prefixes for different data types
        self.prefixes = {
            'embedding': 'emb:',
            'recommendation': 'rec:',
            'job': 'job:',
            'candidate': 'cand:',
            'skill': 'skill:',
            'search': 'search:',
            'analytics': 'analytics:',
            'session': 'session:'
        }
        
        # Default TTL values (in seconds)
        self.default_ttl = {
            'embedding': 3600 * 24,  # 24 hours
            'recommendation': 1800,   # 30 minutes
            'job': 3600,             # 1 hour
            'candidate': 3600,       # 1 hour
            'skill': 3600 * 24 * 7,  # 1 week
            'search': 900,           # 15 minutes
            'analytics': 3600,       # 1 hour
            'session': 1800          # 30 minutes
        }
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # Keep as bytes for compression
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            await self.redis_client.ping()
            logger.info("[SUCCESS] Redis cache service connected successfully")
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache service disconnected")
    
    def _generate_cache_key(self, prefix: str, identifier: str, version: str = "1.0") -> str:
        """Generate cache key with prefix and version"""
        return f"{self.prefixes.get(prefix, 'cache:')}{identifier}:v{version}"
    
    def _compress_data(self, data: Any) -> bytes:
        """Compress data if it exceeds threshold"""
        try:
            serialized = pickle.dumps(data)
            if len(serialized) > self.compression_threshold:
                compressed = gzip.compress(serialized)
                self.cache_stats['compressions'] += 1
                return compressed
            return serialized
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return pickle.dumps(data)
    
    def _decompress_data(self, data: bytes) -> Any:
        """Decompress data if it was compressed"""
        try:
            # Try to decompress first
            try:
                decompressed = gzip.decompress(data)
                return pickle.loads(decompressed)
            except (OSError, gzip.BadGzipFile):
                # Not compressed, load directly
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return None
    
    async def get(self, prefix: str, identifier: str, version: str = "1.0") -> Optional[Any]:
        """Get data from cache"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, identifier, version)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                # Update access statistics
                await self.redis_client.hincrby(f"{cache_key}:stats", "access_count", 1)
                await self.redis_client.hset(f"{cache_key}:stats", "last_accessed", time.time())
                
                self.cache_stats['hits'] += 1
                return self._decompress_data(cached_data)
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    async def set(self, prefix: str, identifier: str, data: Any, ttl: int = None, version: str = "1.0") -> bool:
        """Set data in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, identifier, version)
            ttl = ttl or self.default_ttl.get(prefix, 3600)
            
            # Compress and store data
            compressed_data = self._compress_data(data)
            
            # Store data
            await self.redis_client.setex(cache_key, ttl, compressed_data)
            
            # Store metadata
            metadata = {
                'timestamp': time.time(),
                'ttl': ttl,
                'size': len(compressed_data),
                'version': version
            }
            await self.redis_client.hmset(f"{cache_key}:meta", metadata)
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False
    
    async def delete(self, prefix: str, identifier: str, version: str = "1.0") -> bool:
        """Delete data from cache"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, identifier, version)
            await self.redis_client.delete(cache_key, f"{cache_key}:meta", f"{cache_key}:stats")
            self.cache_stats['deletes'] += 1
            return True
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            return False
    
    async def clear_prefix(self, prefix: str) -> bool:
        """Clear all cache entries with a specific prefix"""
        if not self.redis_client:
            return False
        
        try:
            pattern = f"{self.prefixes.get(prefix, 'cache:')}*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries with prefix: {prefix}")
            return True
        except Exception as e:
            logger.error(f"Cache clear prefix failed: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {}
        
        try:
            info = await self.redis_client.info()
            memory_info = await self.redis_client.info('memory')
            
            return {
                'cache_stats': self.cache_stats,
                'redis_info': {
                    'used_memory': memory_info.get('used_memory', 0),
                    'used_memory_peak': memory_info.get('used_memory_peak', 0),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                },
                'hit_rate': self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses']) if (self.cache_stats['hits'] + self.cache_stats['misses']) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    async def cache_embedding(self, text: str, embedding: Any, model_name: str = "default") -> bool:
        """Cache embedding with metadata"""
        identifier = hashlib.md5(f"{text}:{model_name}".encode()).hexdigest()
        data = {
            'embedding': embedding,
            'text': text,
            'model_name': model_name,
            'timestamp': time.time()
        }
        return await self.set('embedding', identifier, data)
    
    async def get_cached_embedding(self, text: str, model_name: str = "default") -> Optional[Any]:
        """Get cached embedding"""
        identifier = hashlib.md5(f"{text}:{model_name}".encode()).hexdigest()
        data = await self.get('embedding', identifier)
        return data.get('embedding') if data else None
    
    async def cache_recommendation(self, user_id: str, job_id: str, recommendations: List[Dict], algorithm: str = "default") -> bool:
        """Cache recommendation results"""
        identifier = f"{user_id}:{job_id}:{algorithm}"
        data = {
            'recommendations': recommendations,
            'algorithm': algorithm,
            'timestamp': time.time()
        }
        return await self.set('recommendation', identifier, data)
    
    async def get_cached_recommendation(self, user_id: str, job_id: str, algorithm: str = "default") -> Optional[List[Dict]]:
        """Get cached recommendation results"""
        identifier = f"{user_id}:{job_id}:{algorithm}"
        data = await self.get('recommendation', identifier)
        return data.get('recommendations') if data else None
    
    async def cache_job_data(self, job_id: str, job_data: Dict) -> bool:
        """Cache job data"""
        return await self.set('job', job_id, job_data)
    
    async def get_cached_job_data(self, job_id: str) -> Optional[Dict]:
        """Get cached job data"""
        return await self.get('job', job_id)
    
    async def cache_candidate_data(self, candidate_id: str, candidate_data: Dict) -> bool:
        """Cache candidate data"""
        return await self.set('candidate', candidate_id, candidate_data)
    
    async def get_cached_candidate_data(self, candidate_id: str) -> Optional[Dict]:
        """Get cached candidate data"""
        return await self.get('candidate', candidate_id)
    
    async def cache_search_results(self, query: str, results: List[Dict], search_type: str = "default") -> bool:
        """Cache search results"""
        identifier = hashlib.md5(f"{query}:{search_type}".encode()).hexdigest()
        data = {
            'results': results,
            'query': query,
            'search_type': search_type,
            'timestamp': time.time()
        }
        return await self.set('search', identifier, data)
    
    async def get_cached_search_results(self, query: str, search_type: str = "default") -> Optional[List[Dict]]:
        """Get cached search results"""
        identifier = hashlib.md5(f"{query}:{search_type}".encode()).hexdigest()
        data = await self.get('search', identifier)
        return data.get('results') if data else None
    
    async def invalidate_job_cache(self, job_id: str):
        """Invalidate all cache entries related to a job"""
        await self.delete('job', job_id)
        # Also invalidate related recommendations
        pattern = f"{self.prefixes['recommendation']}*:{job_id}:*"
        if self.redis_client:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
    
    async def invalidate_candidate_cache(self, candidate_id: str):
        """Invalidate all cache entries related to a candidate"""
        await self.delete('candidate', candidate_id)
        # Also invalidate related recommendations
        pattern = f"{self.prefixes['recommendation']}*:{candidate_id}:*"
        if self.redis_client:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
    
    async def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries (Redis handles this automatically)"""
        return 0  # Redis handles expiration automatically
    
    async def get_cache_size(self) -> Dict[str, int]:
        """Get cache size by prefix"""
        if not self.redis_client:
            return {}
        
        try:
            sizes = {}
            for prefix_name, prefix in self.prefixes.items():
                pattern = f"{prefix}*"
                keys = await self.redis_client.keys(pattern)
                sizes[prefix_name] = len(keys)
            return sizes
        except Exception as e:
            logger.error(f"Failed to get cache size: {e}")
            return {}

# Global cache service instance
cache_service = RedisCacheService() 