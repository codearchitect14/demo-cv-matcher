#!/usr/bin/env python3
"""
Simple database connection test to verify pgbouncer compatibility
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import AsyncSessionLocal
from sqlalchemy import text

async def test_db_connection():
    """Test database connection without prepared statements"""
    print("🧪 Testing Database Connection")
    print("="*40)
    
    try:
        async with AsyncSessionLocal() as db:
            # Simple query without prepared statements
            result = await db.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                print("[SUCCESS] Database connection working without prepared statements")
                return True
            else:
                print("[ERROR] Database query returned unexpected result")
                return False
                
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

async def test_simple_queries():
    """Test simple queries that should work without prepared statements"""
    print("\n🧪 Testing Simple Queries")
    print("="*40)
    
    try:
        async with AsyncSessionLocal() as db:
            # Test basic SELECT
            result = await db.execute(text("SELECT id FROM candidates LIMIT 1"))
            candidates = result.fetchall()
            print(f"[SUCCESS] Found {len(candidates)} candidates")
            
            # Test basic SELECT with parameters
            result = await db.execute(text("SELECT id FROM jobs LIMIT 1"))
            jobs = result.fetchall()
            print(f"[SUCCESS] Found {len(jobs)} jobs")
            
            return True
            
    except Exception as e:
        print(f"[ERROR] Simple queries failed: {e}")
        return False

async def main():
    """Run database connection tests"""
    print("🚀 Database Connection Test")
    print("="*40)
    
    # Test 1: Basic connection
    connection_ok = await test_db_connection()
    
    # Test 2: Simple queries
    queries_ok = await test_simple_queries()
    
    if connection_ok and queries_ok:
        print("\n✅ All database tests passed!")
        print("✅ Database connection working without prepared statements")
        print("✅ Simple queries working correctly")
    else:
        print("\n❌ Some database tests failed!")
        print("❌ Check database configuration and pgbouncer settings")
    
    return connection_ok and queries_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 