import os
import asyncpg
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import logging
from sqlalchemy import text
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'job_matcher')}"
)

# Convert to asyncpg URL for SQLAlchemy async engine
if DATABASE_URL and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Add pgbouncer-specific parameters to disable prepared statements
if DATABASE_URL and "?" not in DATABASE_URL:
    DATABASE_URL += "?statement_cache_size=0"
elif DATABASE_URL and "?" in DATABASE_URL:
    DATABASE_URL += "&statement_cache_size=0"

logger = logging.getLogger(__name__)

class DatabaseMonitor:
    """Database connection pool monitor"""
    
    def __init__(self):
        self.health_checks = []
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "overflow_connections": 0,
            "last_check": None
        }
        self.health_status = "unknown"
        self.last_error = None
    
    async def check_pool_health(self, engine) -> Dict[str, Any]:
        """Check connection pool health"""
        try:
            pool = engine.pool
            
            # Get pool statistics
            stats = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "total_connections": pool.size() + pool.overflow(),
                "active_connections": pool.checkedout(),
                "idle_connections": pool.checkedin(),
                "overflow_connections": pool.overflow(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Determine health status
            if stats["checked_out"] > stats["pool_size"] * 0.8:
                self.health_status = "warning"
            elif stats["checked_out"] > stats["pool_size"] * 0.95:
                self.health_status = "critical"
            else:
                self.health_status = "healthy"
            
            # Update connection stats
            self.connection_stats.update(stats)
            self.connection_stats["last_check"] = datetime.utcnow()
            
            # Log health status
            logger.info(f"Database pool health: {self.health_status} - "
                       f"Active: {stats['active_connections']}/{stats['total_connections']}")
            
            return {
                "status": self.health_status,
                "stats": stats,
                "last_error": self.last_error
            }
            
        except Exception as e:
            self.health_status = "error"
            self.last_error = str(e)
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_error": self.last_error
            }
    
    async def get_pool_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Get recommendations for pool optimization"""
        recommendations = []
        
        # Check for high connection usage
        if stats["active_connections"] > stats["pool_size"] * 0.8:
            recommendations.append("Consider increasing pool_size to reduce connection contention")
        
        # Check for frequent overflow
        if stats["overflow_connections"] > 0:
            recommendations.append("Connection overflow detected - consider increasing max_overflow")
        
        # Check for invalid connections
        if stats["invalid"] > 0:
            recommendations.append("Invalid connections detected - check for connection leaks")
        
        # Check for low utilization
        if stats["active_connections"] < stats["pool_size"] * 0.2:
            recommendations.append("Pool underutilized - consider reducing pool_size")
        
        return recommendations

# Database monitor instance
db_monitor = DatabaseMonitor()

def create_nuclear_pgbouncer_session_factory():
    """Create a session factory with nuclear pgbouncer compatibility"""
    
    # Nuclear approach: completely disable all caching and prepared statements
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        # Disable all caching
        connect_args={
            "server_settings": {
                "jit": "off",
                "statement_timeout": "30000",
                "idle_in_transaction_session_timeout": "30000",
            },
            "command_timeout": 30,
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        },
        # Disable SQLAlchemy caching
        enable_from_linting=False,
        future=True,
    )
    
    # Create session factory with aggressive settings
    session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    
    return session_factory, engine

# Create async session factory - use nuclear pgbouncer approach
SessionLocal, engine = create_nuclear_pgbouncer_session_factory()

# Base class for models
Base = declarative_base()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_db_session() -> AsyncSession:
    """Get database session with nuclear pgbouncer compatibility"""
    try:
        # Use nuclear session factory
        session = SessionLocal()
        await session.begin()
        return session
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise

async def get_fresh_db_session() -> AsyncSession:
    """Get a fresh database session with a new engine to avoid prepared statement conflicts"""
    fresh_session_factory = get_fresh_session_factory()
    async with fresh_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_pgbouncer_compatible_session() -> AsyncSession:
    """Get a database session specifically configured for pgbouncer compatibility"""
    # Use fresh engine to avoid prepared statement conflicts
    fresh_engine = get_fresh_engine()
    session_factory = sessionmaker(
        fresh_engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
        # Disable SQLAlchemy's statement caching
        enable_baked_queries=False,
    )
    
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def check_database_connection():
    """Check database connection health"""
    try:
        fresh_session_factory = get_fresh_session_factory()
        async with fresh_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            await result.fetchone()
        logger.info("Database connection is healthy")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

async def get_database_health() -> Dict[str, Any]:
    """Get comprehensive database health information"""
    try:
        # Use fresh engine for health checks
        fresh_engine = get_fresh_engine()
        
        # Get pool health
        pool_health = await db_monitor.check_pool_health(fresh_engine)
        
        # Get recommendations
        recommendations = await db_monitor.get_pool_recommendations(pool_health["stats"])
        
        return {
            "status": "healthy" if pool_health["status"] == "healthy" else "warning",
            "pool_health": pool_health,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

async def create_tables():
    """Create all database tables"""
    try:
        fresh_engine = get_fresh_engine()
        async with fresh_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

async def init_db():
    """Initialize database"""
    await create_tables()

async def close_db_connection():
    """Close database connection"""
    try:
        fresh_engine = get_fresh_engine()
        await fresh_engine.dispose()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database connection: {e}")

async def get_database_stats():
    """Get database statistics"""
    try:
        fresh_engine = get_fresh_engine()
        pool = fresh_engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}