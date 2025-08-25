import os
import asyncpg
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import logging
from sqlalchemy import text
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import ssl

# Note: This configuration is optimized for Supabase connection pooler (pgbouncer)
# When using pgbouncer, we disable SQLAlchemy connection pooling and prepared statements
# to avoid conflicts with the external connection pooler

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

# Create direct database URL (bypassing PgBouncer)
DIRECT_DATABASE_URL = DATABASE_URL

logger = logging.getLogger(__name__)

# Build permissive SSL context (to bypass intercepted/self-signed certs)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Create async engine with proper connection pooling
if "pooler" in DATABASE_URL:
    # Use small pool when connecting through pgbouncer/pooler for better performance
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,  # Small pool size for pooler
        max_overflow=10,
        pool_timeout=5,
        pool_recycle=1800,
        pool_pre_ping=False,  # Disable pre-ping for faster connections
        connect_args={
            "server_settings": {
                "jit": "off",
                "statement_timeout": "5000",  # Reduced timeout for faster failure
                "idle_in_transaction_session_timeout": "10000",
            },
            "command_timeout": 5,  # Reduced timeout
            "statement_cache_size": 0,
            "ssl": ssl_context,
        },
        future=True,
    )
else:
    # Use connection pooling when connecting directly to PostgreSQL
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_timeout=10,
        pool_recycle=3600,
        pool_pre_ping=True,
        connect_args={
            "server_settings": {
                "jit": "off",
                "statement_timeout": "10000",
                "idle_in_transaction_session_timeout": "15000",
            },
            "command_timeout": 10,
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "ssl": ssl_context,
        },
        future=True,
    )

# Create direct engine for initialization (bypasses PgBouncer)
if "pooler" in DIRECT_DATABASE_URL:
    # Use NullPool when connecting through pgbouncer/pooler
    direct_engine = create_async_engine(
        DIRECT_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        connect_args={
            "server_settings": {
                "jit": "off",
                "statement_timeout": "10000",
                "idle_in_transaction_session_timeout": "15000",
            },
            "command_timeout": 10,
            "statement_cache_size": 0,
            "ssl": ssl_context,
        },
        future=True,
    )
else:
    # Use connection pooling when connecting directly to PostgreSQL
    direct_engine = create_async_engine(
        DIRECT_DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_timeout=5,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args={
            "server_settings": {
                "jit": "off",
                "statement_timeout": "10000",
                "idle_in_transaction_session_timeout": "15000",
            },
            "command_timeout": 10,
            "statement_cache_size": 0,
            "ssl": ssl_context,
        },
        future=True,
    )

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_fresh_engine():
    """Get a fresh database engine instance with connection pooling"""
    if "pooler" in DATABASE_URL:
        # Use NullPool when connecting through pgbouncer/pooler
        return create_async_engine(
            DATABASE_URL,
            echo=False,
            poolclass=NullPool,
            connect_args={
                "server_settings": {
                    "jit": "off",
                    "statement_timeout": "10000",
                    "idle_in_transaction_session_timeout": "15000",
                },
                "command_timeout": 10,
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
                "ssl": ssl_context,
            },
            future=True,
        )
    else:
        # Use connection pooling when connecting directly to PostgreSQL
        return create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_timeout=5,
            pool_recycle=1800,
            pool_pre_ping=True,
            connect_args={
                "server_settings": {
                    "jit": "off",
                    "statement_timeout": "10000",
                    "idle_in_transaction_session_timeout": "15000",
                },
                "command_timeout": 10,
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
                "ssl": ssl_context,
            },
            future=True,
        )

async def get_db_session() -> AsyncSession:
    """Get database session with performance monitoring"""
    import time
    start_time = time.time()
    
    session = AsyncSession(engine)
    try:
        # Quick connection health check for critical operations
        connection_time = time.time() - start_time
        if connection_time > 1.0:  # Warn if connection takes > 1 second
            logger.warning(f"Database connection took {connection_time:.3f}s")
        
        yield session
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Database session error after {elapsed:.3f}s: {e}")
        await session.rollback()
        raise
    finally:
        try:
            await session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {e}")

async def check_database_connection():
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
    try:
        async with direct_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

async def init_db():
    await create_tables()

async def close_db_connection():
    try:
        await engine.dispose()
        await direct_engine.dispose()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database connection: {e}")

async def get_database_stats():
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