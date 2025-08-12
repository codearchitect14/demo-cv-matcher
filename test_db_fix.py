#!/usr/bin/env python3
"""
Test to verify the database connection fix for pgbouncer compatibility
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_database_connection():
    """Test database connection with pgbouncer compatibility"""
    print("🧪 Testing database connection fix...")
    
    try:
        from config.database import get_db_session
        from sqlalchemy import text
        
        # Test basic connection
        async for db in get_db_session():
            result = await db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Database connection works: {row}")
            
            # Test a simple query that was failing
            result = await db.execute(text("SELECT COUNT(*) FROM jobs"))
            count = result.fetchone()
            print(f"✅ Jobs query works: Found {count[0]} jobs")
            
            # Test with parameters (this was causing the prepared statement error)
            result = await db.execute(
                text("SELECT COUNT(*) FROM jobs WHERE location = :location"),
                {"location": "New York"}
            )
            count = result.fetchone()
            print(f"✅ Parameterized query works: Found {count[0]} jobs in New York")
            
            break
        
        print("🎉 Database connection fix is working!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

async def test_session_factory():
    """Test that session factory creates compatible sessions"""
    print("\n🔧 Testing session factory...")
    
    try:
        from config.database import get_fresh_session_factory
        from sqlalchemy import text
        
        session_factory = get_fresh_session_factory()
        async with session_factory() as session:
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Session factory works: {row}")
        
        print("✅ Session factory is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Session factory test failed: {e}")
        return False

async def main():
    """Run all database tests"""
    print("🚀 Testing Database Connection Fix")
    print("=" * 50)
    
    # Run tests
    connection_ok = await test_database_connection()
    session_ok = await test_session_factory()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    if connection_ok and session_ok:
        print("🎉 ALL DATABASE TESTS PASSED!")
        print("\n✅ Pgbouncer compatibility fix is working:")
        print("   • Prepared statements disabled")
        print("   • Fresh engine creation working")
        print("   • Session factory compatible")
        print("   • Parameterized queries working")
        return True
    else:
        print("⚠️ Some database tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 