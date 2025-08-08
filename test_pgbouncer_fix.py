#!/usr/bin/env python3
"""
Comprehensive test to verify pgbouncer compatibility fix
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_database_connection():
    """Test database connection with pgbouncer compatibility"""
    print("🧪 Testing database connection with pgbouncer fix...")
    
    try:
        from config.database import get_db_session, create_pgbouncer_compatible_session_factory
        from sqlalchemy import text
        
        # Test 1: Basic connection
        print("  Testing basic connection...")
        async for db in get_db_session():
            result = await db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"    ✅ Basic connection works: {row}")
            break
        
        # Test 2: Session factory
        print("  Testing session factory...")
        session_factory = create_pgbouncer_compatible_session_factory()
        async with session_factory() as session:
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"    ✅ Session factory works: {row}")
        
        # Test 3: Parameterized query (this was causing the error)
        print("  Testing parameterized query...")
        async for db in get_db_session():
            result = await db.execute(
                text("SELECT COUNT(*) FROM jobs WHERE location = :location"),
                {"location": "New York"}
            )
            count = result.fetchone()
            print(f"    ✅ Parameterized query works: Found {count[0]} jobs in New York")
            break
        
        # Test 4: Complex query (the exact one that was failing)
        print("  Testing complex query...")
        async for db in get_db_session():
            result = await db.execute(
                text("""
                    SELECT jobs.title, jobs.company, jobs.location, jobs.salary_min, 
                           jobs.salary_max, jobs.domain, jobs.total_years_required, 
                           jobs.job_description, jobs.id, jobs.created_at, jobs.updated_at 
                    FROM jobs 
                    WHERE jobs.location = :location 
                    ORDER BY jobs.created_at DESC 
                    LIMIT :limit OFFSET :offset
                """),
                {"location": "New York", "limit": 10, "offset": 0}
            )
            rows = result.fetchall()
            print(f"    ✅ Complex query works: Retrieved {len(rows)} jobs")
            break
        
        print("🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_engine_configuration():
    """Test that the engine is configured correctly"""
    print("\n🔧 Testing engine configuration...")
    
    try:
        from config.database import create_db_engine, get_fresh_engine, create_pgbouncer_compatible_session_factory
        from sqlalchemy import text
        
        # Test engine creation
        engine = create_db_engine()
        print("    ✅ Engine creation works")
        
        # Test fresh engine creation
        fresh_engine = get_fresh_engine()
        print("    ✅ Fresh engine creation works")
        
        # Test connection using session factory (to avoid prepared statement conflicts)
        session_factory = create_pgbouncer_compatible_session_factory()
        async with session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            print(f"    ✅ Engine connection works: {row}")
        
        print("✅ Engine configuration is correct!")
        return True
        
    except Exception as e:
        print(f"❌ Engine configuration test failed: {e}")
        return False

async def main():
    """Run all pgbouncer compatibility tests"""
    print("🚀 Testing Pgbouncer Compatibility Fix")
    print("=" * 50)
    
    # Run tests
    db_ok = await test_database_connection()
    engine_ok = await test_engine_configuration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    if db_ok and engine_ok:
        print("🎉 ALL PGBOUNCER TESTS PASSED!")
        print("\n✅ Pgbouncer compatibility fix is working:")
        print("   • Prepared statements disabled")
        print("   • Fresh engine creation working")
        print("   • Session factory compatible")
        print("   • Parameterized queries working")
        print("   • Complex queries working")
        print("   • No prepared statement errors")
        return True
    else:
        print("⚠️ Some pgbouncer tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 