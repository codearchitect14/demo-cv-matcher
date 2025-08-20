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

# Create async engine with PgBouncer compatibility
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={
        "server_settings": {
            "jit": "off",
            "statement_timeout": "30000",
            "idle_in_transaction_session_timeout": "30000",
        },
        "command_timeout": 30,
        "statement_cache_size": 0,
        "ssl": ssl_context,
    },
    future=True,
)

# Create direct engine for initialization (bypasses PgBouncer)
direct_engine = create_async_engine(
    DIRECT_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={
        "server_settings": {
            "jit": "off",
            "statement_timeout": "30000",
            "idle_in_transaction_session_timeout": "30000",
        },
        "command_timeout": 30,
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
    """Get a fresh database engine instance with pgbouncer compatibility"""
    return create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        connect_args={
            "server_settings": {
                "jit": "off",
                "statement_timeout": "30000",
                "idle_in_transaction_session_timeout": "30000",
            },
            "command_timeout": 30,
            "statement_cache_size": 0,
            "ssl": ssl_context,
        },
        future=True,
    )

async def get_db_session() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

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