#!/usr/bin/env python3
"""
Test to verify that API endpoints work correctly with the database fix
"""

import asyncio
import sys
import os
import aiohttp
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_jobs_endpoint():
    """Test the jobs endpoint that was failing"""
    print("🧪 Testing jobs endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test the jobs endpoint
            url = "http://localhost:8000/api/v1/jobs/"
            params = {"skip": 0, "limit": 10, "location": "New York"}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Jobs endpoint works: Retrieved {len(data)} jobs")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Jobs endpoint failed: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Jobs endpoint test failed: {e}")
        return False

async def test_database_direct():
    """Test database connection directly"""
    print("\n🔧 Testing database connection directly...")
    
    try:
        from config.database import get_db_session
        from sqlalchemy import text
        
        async for db in get_db_session():
            # Test the exact query that was failing
            result = await db.execute(
                text("SELECT jobs.title, jobs.company, jobs.location, jobs.salary_min, jobs.salary_max, jobs.domain, jobs.total_years_required, jobs.job_description, jobs.id, jobs.created_at, jobs.updated_at FROM jobs WHERE jobs.location = :location ORDER BY jobs.created_at DESC LIMIT :limit OFFSET :offset"),
                {"location": "New York", "limit": 10, "offset": 0}
            )
            rows = result.fetchall()
            print(f"✅ Direct database query works: Retrieved {len(rows)} jobs")
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Direct database test failed: {e}")
        return False

async def main():
    """Run all API tests"""
    print("🚀 Testing API Endpoints with Database Fix")
    print("=" * 50)
    
    # Run tests
    api_ok = await test_jobs_endpoint()
    db_ok = await test_database_direct()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    if api_ok and db_ok:
        print("🎉 ALL API TESTS PASSED!")
        print("\n✅ Database fix is working correctly:")
        print("   • API endpoints responding")
        print("   • Database queries working")
        print("   • No prepared statement errors")
        return True
    else:
        print("⚠️ Some API tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 