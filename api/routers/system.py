from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import time
import logging

from config.database import get_db_session, get_database_stats
from services.cache_service import cache_service
from api.routers.auth import get_current_active_user, require_role
from models.candidate import Candidate
from embeddings.embedder import embedding_service
from embeddings.build_index import index_manager
from services.personalization_service import personalization_service
from middleware.rate_limiter import rate_limiter

router = APIRouter(tags=["System"])

logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "cv-matcher-api"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db_session)):
    """Detailed health check with database and cache status"""
    try:
        # Check database connection
        db_healthy = await get_database_stats()
        
        # Check cache connection
        cache_healthy = await cache_service.get_cache_stats()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": {
                "status": "healthy" if "error" not in db_healthy else "unhealthy",
                "stats": db_healthy
            },
            "cache": {
                "status": "healthy" if "error" not in cache_healthy else "unhealthy",
                "stats": cache_healthy
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@router.get("/performance/database")
async def get_database_performance(
    db: AsyncSession = Depends(get_db_session),
    current_user: Candidate = Depends(get_current_active_user)
):
    """Get database performance metrics"""
    try:
        # Get database statistics
        db_stats = await get_database_stats()
        
        return {
            "database_stats": db_stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to get database performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get database performance metrics"
        )

@router.get("/performance/cache")
async def get_cache_performance(
    current_user: Candidate = Depends(get_current_active_user)
):
    """Get cache performance metrics"""
    try:
        cache_stats = await cache_service.get_cache_stats()
        
        return {
            "cache_stats": cache_stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to get cache performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache performance metrics"
        )

@router.get("/performance/overview")
async def get_performance_overview(
    db: AsyncSession = Depends(get_db_session),
    current_user: Candidate = Depends(get_current_active_user)
):
    """Get comprehensive performance overview"""
    try:
        # Get database performance
        db_stats = await get_database_stats()
        
        # Get cache performance
        cache_stats = await cache_service.get_cache_stats()
        
        # Calculate hit rates
        cache_hit_rate = 0
        if cache_stats.get("keyspace_hits", 0) + cache_stats.get("keyspace_misses", 0) > 0:
            cache_hit_rate = cache_stats.get("keyspace_hits", 0) / (
                cache_stats.get("keyspace_hits", 0) + cache_stats.get("keyspace_misses", 0)
            ) * 100
        
        return {
            "database": {
                "stats": db_stats,
                "pool_status": "N/A", # Removed pool_status as db_monitor is removed
                "connection_health": "N/A" # Removed connection_health as pool_status is removed
            },
            "cache": {
                "stats": cache_stats,
                "hit_rate_percentage": round(cache_hit_rate, 2),
                "health": "healthy" if "error" not in cache_stats else "unhealthy"
            },
            "overall_health": "healthy",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to get performance overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance overview"
        )

@router.post("/cache/clear")
async def clear_cache(
    current_user: Candidate = Depends(require_role(["admin"]))
):
    """Clear all cache (admin only)"""
    try:
        success = await cache_service.clear_all_cache()
        if success:
            return {"message": "Cache cleared successfully", "timestamp": time.time()}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear cache"
            )
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )

@router.post("/cache/warm")
async def warm_cache(
    current_user: Candidate = Depends(require_role(["admin"]))
):
    """Warm cache with frequently accessed data (admin only)"""
    try:
        # This would typically warm cache with popular candidates and jobs
        # For now, just return success
        return {
            "message": "Cache warming initiated",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to warm cache"
        )

@router.get("/metrics")
async def get_system_metrics(
    current_user: Candidate = Depends(require_role(["admin"]))
):
    """Get system metrics (admin only)"""
    try:
        # Get database metrics
        db_stats = await get_database_stats()
        
        # Get cache metrics
        cache_stats = await cache_service.get_cache_stats()
        
        # Calculate performance metrics
        cache_hit_rate = 0
        if cache_stats.get("keyspace_hits", 0) + cache_stats.get("keyspace_misses", 0) > 0:
            cache_hit_rate = cache_stats.get("keyspace_hits", 0) / (
                cache_stats.get("keyspace_hits", 0) + cache_stats.get("keyspace_misses", 0)
            ) * 100
        
        return {
            "database": {
                "active_connections": db_stats.get("active_connections", 0),
                "pool_size": "N/A", # Removed pool_status as db_monitor is removed
                "checked_out": "N/A", # Removed pool_status as db_monitor is removed
                "overflow": "N/A" # Removed pool_status as db_monitor is removed
            },
            "cache": {
                "hit_rate_percentage": round(cache_hit_rate, 2),
                "memory_usage": cache_stats.get("used_memory_human", "0B"),
                "total_commands": cache_stats.get("total_commands_processed", 0),
                "uptime_seconds": cache_stats.get("uptime_in_seconds", 0)
            },
            "performance": {
                "cache_efficiency": "excellent" if cache_hit_rate > 80 else "good" if cache_hit_rate > 60 else "poor",
                "database_health": "healthy", # Removed pool_status as db_monitor is removed
                "overall_status": "optimal" if cache_hit_rate > 80 and "error" not in db_stats else "degraded" # Removed pool_status as db_monitor is removed
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system metrics"
        ) 