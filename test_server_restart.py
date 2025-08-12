#!/usr/bin/env python3
"""
Test to verify that server restart will fix the prepared statement issue
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_fresh_connections():
    """Test that fresh connections work without prepared statement errors"""
    print("🧪 Testing fresh database connections...")
    
    try:
        from config.database import get_db_session, create_pgbouncer_compatible_session_factory
        from sqlalchemy import text
        
        # Test multiple fresh connections
        for i in range(3):
            print(f"  Test {i+1}: Creating fresh connection...")
            
            # Use the session factory that the API uses
            session_factory = create_pgbouncer_compatible_session_factory()
            async with session_factory() as session:
                result = await session.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"    ✅ Connection {i+1} works: {row}")
                
                # Test the exact query that was failing in the API
                result = await session.execute(
                    text("SELECT COUNT(*) FROM jobs"),
                )
                count = result.fetchone()
                print(f"    ✅ Jobs query {i+1} works: Found {count[0]} jobs")
        
        print("🎉 All fresh connections work!")
        return True
        
    except Exception as e:
        print(f"❌ Fresh connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_simulation():
    """Simulate the API endpoint that was failing"""
    print("\n🔧 Testing API simulation...")
    
    try:
        from config.database import get_db_session
        from sqlalchemy import text
        
        # Simulate the exact query that was failing
        async for db in get_db_session():
            result = await db.execute(
                text("""
                    SELECT jobs.title, jobs.company, jobs.location, jobs.salary_min, 
                           jobs.salary_max, jobs.domain, jobs.total_years_required, 
                           jobs.job_description, jobs.id, jobs.created_at, jobs.updated_at 
                    FROM jobs 
                    ORDER BY jobs.created_at DESC 
                    LIMIT :limit OFFSET :offset
                """),
                {"limit": 10, "offset": 0}
            )
            rows = result.fetchall()
            print(f"    ✅ API simulation works: Retrieved {len(rows)} jobs")
            break
        
        print("✅ API simulation successful!")
        return True
        
    except Exception as e:
        print(f"❌ API simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all server restart tests"""
    print("🚀 Testing Server Restart Fix")
    print("=" * 50)
    
    # Run tests
    fresh_ok = await test_fresh_connections()
    api_ok = await test_api_simulation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    if fresh_ok and api_ok:
        print("🎉 ALL SERVER RESTART TESTS PASSED!")
        print("\n✅ Server restart should fix the prepared statement issue:")
        print("   • Fresh connections work correctly")
        print("   • API simulation works")
        print("   • No prepared statement errors")
        print("   • Ready for server restart")
        return True
    else:
        print("⚠️ Some server restart tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 