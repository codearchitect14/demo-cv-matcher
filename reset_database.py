#!/usr/bin/env python3
"""
Reset database with new schema (no embedding columns)
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import engine
from models import Candidate, CandidateExperience, Job, JobMandatorySkill, Application, InteractionLog
from sqlalchemy import text

async def reset_database():
    """Reset database with new schema"""
    print("🔄 Resetting database...")
    
    try:
        # Drop and recreate schema
        async with engine.begin() as conn:
            await conn.execute(text('DROP SCHEMA IF EXISTS public CASCADE'))
            await conn.execute(text('CREATE SCHEMA public'))
            await conn.execute(text('GRANT ALL ON SCHEMA public TO postgres'))
            await conn.execute(text('GRANT ALL ON SCHEMA public TO public'))
        
        print("✅ Schema reset complete")
        
        # Create tables with new schema
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: Candidate.__table__.create(sync_conn))
            await conn.run_sync(lambda sync_conn: CandidateExperience.__table__.create(sync_conn))
            await conn.run_sync(lambda sync_conn: Job.__table__.create(sync_conn))
            await conn.run_sync(lambda sync_conn: JobMandatorySkill.__table__.create(sync_conn))
            await conn.run_sync(lambda sync_conn: Application.__table__.create(sync_conn))
            await conn.run_sync(lambda sync_conn: InteractionLog.__table__.create(sync_conn))
        
        print("✅ All tables created successfully!")
        print("📋 Tables created:")
        print("   - candidates (with summary column, no embedding)")
        print("   - candidate_experience (no embedding column)")
        print("   - jobs (no embedding column)")
        print("   - job_mandatory_skills")
        print("   - applications")
        print("   - interaction_logs")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(reset_database()) 