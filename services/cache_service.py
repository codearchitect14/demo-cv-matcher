import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
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
        self.compression_threshold = 4096  # Increased to 4KB
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
        
        # Adaptive compression settings
        self.compression_settings = {
            'embedding': {'threshold': 2048, 'always_compress': True},  # Always compress embeddings
            'recommendation': {'threshold': 4096, 'always_compress': False},
            'job': {'threshold': 2048, 'always_compress': False},
            'candidate': {'threshold': 2048, 'always_compress': False},
            'skill': {'threshold': 1024, 'always_compress': False},
            'search': {'threshold': 8192, 'always_compress': False},  # Large search results
            'analytics': {'threshold': 4096, 'always_compress': False},
            'session': {'threshold': 1024, 'always_compress': False}
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
    
    def _should_compress(self, data: Any, prefix: str) -> bool:
        """Determine if data should be compressed based on type and size"""
        try:
            serialized = pickle.dumps(data)
            data_size = len(serialized)
            
            # Get compression settings for this data type
            settings = self.compression_settings.get(prefix, {'threshold': self.compression_threshold, 'always_compress': False})
            
            # Always compress if configured for this type
            if settings.get('always_compress', False):
                return True
            
            # Compress if size exceeds threshold
            return data_size > settings.get('threshold', self.compression_threshold)
            
        except Exception as e:
            logger.warning(f"Error determining compression for {prefix}: {e}")
            return False
    
    def _compress_data(self, data: Any, prefix: str = 'cache') -> bytes:
        """Compress data if it exceeds threshold or type-specific settings"""
        try:
            serialized = pickle.dumps(data)
            
            # Check if compression is needed
            if self._should_compress(data, prefix):
                compressed = gzip.compress(serialized)
                self.cache_stats['compressions'] += 1
                logger.debug(f"Compressed {prefix} data: {len(serialized)} -> {len(compressed)} bytes")
                return compressed
            
            return serialized
            
        except Exception as e:
            logger.error(f"Error compressing data: {e}")
            return pickle.dumps(data)  # Fallback to uncompressed
    
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
            compressed_data = self._compress_data(data, prefix)
            
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
        """Invalidate job-related cache entries"""
        try:
            # Invalidate job data
            await self.delete('job', job_id)
            
            # Invalidate related recommendations
            recommendation_pattern = f"{self.prefixes['recommendation']}*job_{job_id}*"
            await self._invalidate_pattern(recommendation_pattern)
            
            # Invalidate search results that might include this job
            search_pattern = f"{self.prefixes['search']}*"
            await self._invalidate_pattern(search_pattern)
            
            logger.info(f"Invalidated cache for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate job cache: {e}")

    async def invalidate_candidate_cache(self, candidate_id: str):
        """Invalidate candidate-related cache entries"""
        try:
            # Invalidate candidate data
            await self.delete('candidate', candidate_id)
            
            # Invalidate related recommendations
            recommendation_pattern = f"{self.prefixes['recommendation']}*candidate_{candidate_id}*"
            await self._invalidate_pattern(recommendation_pattern)
            
            # Invalidate search results that might include this candidate
            search_pattern = f"{self.prefixes['search']}*"
            await self._invalidate_pattern(search_pattern)
            
            logger.info(f"Invalidated cache for candidate {candidate_id}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate candidate cache: {e}")
    
    async def _invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern"""
        try:
            if not self.redis_client:
                return 0
            
            # Scan for keys matching pattern
            deleted_count = 0
            cursor = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor, 
                    match=pattern, 
                    count=100
                )
                
                if keys:
                    # Delete matching keys
                    deleted = await self.redis_client.delete(*keys)
                    deleted_count += deleted
                
                if cursor == 0:
                    break
            
            logger.debug(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate pattern {pattern}: {e}")
            return 0
    
    async def invalidate_skill_cache(self, skill_name: str = None):
        """Invalidate skill-related cache entries"""
        try:
            if skill_name:
                # Invalidate specific skill
                await self.delete('skill', skill_name)
            else:
                # Invalidate all skill cache
                await self.clear_prefix('skill')
            
            # Invalidate recommendations that depend on skills
            recommendation_pattern = f"{self.prefixes['recommendation']}*"
            await self._invalidate_pattern(recommendation_pattern)
            
            logger.info(f"Invalidated skill cache for: {skill_name or 'all skills'}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate skill cache: {e}")
    
    async def invalidate_embedding_cache(self, text_hash: str = None):
        """Invalidate embedding cache entries"""
        try:
            if text_hash:
                # Invalidate specific embedding
                await self.delete('embedding', text_hash)
            else:
                # Invalidate all embedding cache
                await self.clear_prefix('embedding')
            
            logger.info(f"Invalidated embedding cache for: {text_hash or 'all embeddings'}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate embedding cache: {e}")
    
    async def invalidate_analytics_cache(self, analytics_type: str = None):
        """Invalidate analytics cache entries"""
        try:
            if analytics_type:
                # Invalidate specific analytics type
                await self.clear_prefix(f"analytics:{analytics_type}")
            else:
                # Invalidate all analytics cache
                await self.clear_prefix('analytics')
            
            logger.info(f"Invalidated analytics cache for: {analytics_type or 'all analytics'}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate analytics cache: {e}")
    
    async def smart_invalidate(self, entity_type: str, entity_id: str, dependencies: List[str] = None):
        """Smart cache invalidation based on entity dependencies"""
        try:
            # Invalidate the main entity
            await self.delete(entity_type, entity_id)
            
            # Invalidate dependencies if provided
            if dependencies:
                for dep_type, dep_id in dependencies:
                    await self.delete(dep_type, dep_id)
            
            # Invalidate related caches based on entity type
            if entity_type == 'job':
                await self.invalidate_job_cache(entity_id)
            elif entity_type == 'candidate':
                await self.invalidate_candidate_cache(entity_id)
            elif entity_type == 'skill':
                await self.invalidate_skill_cache(entity_id)
            
            logger.info(f"Smart invalidation completed for {entity_type}:{entity_id}")
            
        except Exception as e:
            logger.error(f"Failed to perform smart invalidation: {e}")
    
    async def get_cache_dependencies(self, prefix: str, identifier: str) -> List[Tuple[str, str]]:
        """Get cache dependencies for a specific entry"""
        try:
            # This could be enhanced to track actual dependencies
            # For now, return common dependencies based on prefix
            dependencies = []
            
            if prefix == 'job':
                # Job cache might depend on skills and candidates
                dependencies.extend([
                    ('skill', 'all'),  # All skills might be affected
                    ('recommendation', f'job_{identifier}')  # Job recommendations
                ])
            elif prefix == 'candidate':
                # Candidate cache might depend on skills and jobs
                dependencies.extend([
                    ('skill', 'all'),  # All skills might be affected
                    ('recommendation', f'candidate_{identifier}')  # Candidate recommendations
                ])
            elif prefix == 'skill':
                # Skill cache might affect all recommendations
                dependencies.extend([
                    ('recommendation', 'all'),  # All recommendations
                    ('search', 'all')  # All search results
                ])
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Failed to get cache dependencies: {e}")
            return []
    
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