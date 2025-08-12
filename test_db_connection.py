#!/usr/bin/env python3
"""
Test database connection and query execution
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session, engine
from db.crud.job import job as job_crud

async def test_database_connection():
    """Test database connection and basic queries"""
    
    print("🔍 Testing database connection...")
    
    try:
        # Test 1: Basic connection
        print("1. Testing basic connection...")
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("✅ Basic connection successful")
        
        # Test 2: Session creation
        print("2. Testing session creation...")
        async with get_db_session() as session:
            print("✅ Session creation successful")
        
        # Test 3: Job query (the one that was failing)
        print("3. Testing job query...")
        async with get_db_session() as session:
            jobs = await job_crud.get_multi_with_filters(session, limit=5)
            print(f"✅ Job query successful - found {len(jobs)} jobs")
            
            if jobs:
                print(f"   First job: {jobs[0].title}")
        
        # Test 4: Complex query with mandatory skills
        print("4. Testing complex query with mandatory skills...")
        async with get_db_session() as session:
            # This is the query that was causing the prepared statement error
            from sqlalchemy import select
            from models.job import Job, JobMandatorySkill
            from sqlalchemy.orm import selectinload
            
            query = select(Job).options(selectinload(Job.mandatory_skills)).limit(5)
            result = await session.execute(query)
            jobs_with_skills = result.scalars().all()
            print(f"✅ Complex query successful - found {len(jobs_with_skills)} jobs with skills")
        
        print("\n🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting database connection tests...")
    
    success = await test_database_connection()
    
    if success:
        print("\n✅ Database is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Database has issues!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 