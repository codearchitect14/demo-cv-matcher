#!/usr/bin/env python3
"""
Simple script to test database connection and provide server start instructions
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import AsyncSessionLocal, engine
from db.crud.job import job as job_crud
from sqlalchemy import text

async def test_database_connection():
    """Test database connection and basic queries"""
    
    print("🔍 Testing database connection...")
    
    try:
        # Test 1: Basic connection
        print("1. Testing basic connection...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Basic connection successful")
        
        # Test 2: Session creation
        print("2. Testing session creation...")
        async with AsyncSessionLocal() as session:
            print("✅ Session creation successful")
        
        # Test 3: Job query (the one that was failing)
        print("3. Testing job query...")
        async with AsyncSessionLocal() as session:
            jobs = await job_crud.get_multi_with_filters(session, limit=5)
            print(f"✅ Job query successful - found {len(jobs)} jobs")
            
            if jobs:
                print(f"   First job: {jobs[0].title}")
        
        print("\n🎉 All database tests passed!")
        print("\n📋 Next steps:")
        print("1. Open a new terminal/command prompt")
        print("2. Navigate to your project directory")
        print("3. Run: python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        print("4. The server should start without the pgbouncer error")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL in .env file")
        print("3. Try restarting PostgreSQL")
        return False

async def main():
    """Main test function"""
    print("🚀 Testing database connection with updated settings...")
    
    success = await test_database_connection()
    
    if success:
        print("\n✅ Database is working correctly!")
        print("🔄 You can now start the server manually")
    else:
        print("\n❌ Database still has issues!")
        print("🔧 Please check your database configuration")

if __name__ == "__main__":
    asyncio.run(main()) 