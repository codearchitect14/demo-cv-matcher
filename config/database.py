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

# Ensure prepared statement cache is disabled at the URL level for asyncpg/pgbouncer compatibility
if DATABASE_URL and "prepared_statement_cache_size" not in DATABASE_URL:
    DATABASE_URL = (
        f"{DATABASE_URL}{'&' if '?' in DATABASE_URL else '?'}prepared_statement_cache_size=0"
    )

logger = logging.getLogger(__name__)

# Create async engine with basic configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    # Pgbouncer compatibility - disable statement caching
    connect_args={
        "server_settings": {
            "jit": "off",
            "statement_timeout": "30000",
            "idle_in_transaction_session_timeout": "30000",
        },
        "command_timeout": 30,
        "statement_cache_size": 0,  # Disable prepared statement caching for pgbouncer compatibility
    },
    future=True,
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Base class for models
Base = declarative_base()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_fresh_engine():
    """Get a fresh database engine instance with pgbouncer compatibility"""
    return create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        # Pgbouncer compatibility - disable statement caching
        connect_args={
            "server_settings": {
                "jit": "off",
                "statement_timeout": "30000",
                "idle_in_transaction_session_timeout": "30000",
            },
            "command_timeout": 30,
            "statement_cache_size": 0,  # Disable prepared statement caching for pgbouncer compatibility
        },
        future=True,
    )

async def get_db_session() -> AsyncSession:
    """Get database session"""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def check_database_connection():
    """Check database connection health"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
        logger.info("Database connection is healthy")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

async def create_tables():
    """Create all database tables"""
    try:
        async with engine.begin() as conn:
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
        await engine.dispose()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database connection: {e}")

async def get_database_stats():
    """Get database statistics"""
    try:
        pool = engine.pool
        
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