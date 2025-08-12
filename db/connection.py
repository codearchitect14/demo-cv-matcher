# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_fresh_engine, Base
import asyncio

# Import models to register them with SQLAlchemy
def import_all_models():
    """Import all models to register with SQLAlchemy"""
    try:
        from models.candidate import Candidate, CandidateExperience
        from models.job import Job, JobMandatorySkill
        from models.application import Application
        from models.interaction import InteractionLog
        
        models = [Candidate, CandidateExperience, Job, JobMandatorySkill, Application, InteractionLog]
        print(f"Registered {len(models)} models with SQLAlchemy")
        return models
    except ImportError as e:
        print(f"Error importing models: {e}")
        return []


async def create_tables():
    """Create all database tables"""
    models = import_all_models()
    fresh_engine = get_fresh_engine()
    async with fresh_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print(f"Created tables for {len(models)} models")


async def drop_tables():
    """Drop all database tables"""
    import_all_models()  # Register models first
    fresh_engine = get_fresh_engine()
    async with fresh_engine.begin() as conn:
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
