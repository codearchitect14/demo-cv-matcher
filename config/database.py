import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import logging
from sqlalchemy import text

# Load environment variables
load_dotenv(dotenv_path=".env")

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql+asyncpg://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'job_matcher')}"
)

# Create async engine with connection pool configuration and error handling (Issue #15)
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() == "true",
    future=True,
    # Connection pool settings
    # poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections beyond pool_size
    pool_timeout=30,  # Timeout when getting connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Validate connections before use
    # SSL settings for Supabase
    connect_args={
        "ssl": True if "supabase.co" in DATABASE_URL else False
    }
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Configure logging for database operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_db_session() -> AsyncSession:
    """Get database session for dependency injection"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection():
    """Check database connection health"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            logger.info("Database connection is healthy")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


async def create_tables():
    """Create all tables in the database"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


# Add the missing init_db function that your main.py is looking for
async def init_db():
    """Initialize database - alias for create_tables for compatibility"""
    await create_tables()


async def close_db_connection():
    """Close database connection properly"""
    try:
        await engine.dispose()
        logger.info("Database connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connection: {str(e)}")