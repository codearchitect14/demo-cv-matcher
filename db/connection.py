import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine, Base
from db.models_registry import ALL_MODELS  # Import to register models
import asyncio


async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print(f"Created {len(ALL_MODELS)} tables: {[model.__tablename__ for model in ALL_MODELS]}")


async def drop_tables():
    """Drop all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("All tables dropped successfully!")


async def init_database():
    """Initialize database with tables"""
    print("Initializing database...")
    await create_tables()
    print("Database initialization completed!")


async def reset_database():
    """Reset database by dropping and recreating all tables"""
    print("Resetting database...")
    await drop_tables()
    await create_tables()
    print("Database reset completed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        asyncio.run(reset_database())
    else:
        asyncio.run(init_database())
