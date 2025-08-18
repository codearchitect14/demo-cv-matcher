#!/usr/bin/env python3
"""
Test database connection and fix transaction issues
"""
import asyncio
import os
from sqlalchemy import text
from config.database import engine, get_db_session

async def test_database_connection():
    """Test database connection"""
    print("🧪 Testing database connection...")
    
    try:
        # Test 1: Direct engine connection
        print("📊 Test 1: Direct engine connection...")
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Direct connection: {row[0]}")
        
        # Test 2: Session connection
        print("📊 Test 2: Session connection...")
        async for session in get_db_session():
            try:
                result = await session.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Session connection: {row[0]}")
                break
            finally:
                await session.close()
        
        # Test 3: Version check
        print("📊 Test 3: Database version...")
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ Database version: {version[0]}")
        
        print("🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_auth_simulation():
    """Test auth-like operations"""
    print("\n🧪 Testing auth simulation...")
    
    try:
        async for session in get_db_session():
            try:
                # Simulate auth operations
                result = await session.execute(text("SELECT COUNT(*) FROM candidates"))
                count = result.fetchone()
                print(f"✅ Candidates count: {count[0]}")
                
                # Test transaction
                await session.commit()
                print("✅ Transaction committed successfully")
                break
                
            except Exception as e:
                await session.rollback()
                print(f"❌ Transaction failed: {e}")
                raise
            finally:
                await session.close()
        
        print("🎉 Auth simulation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Auth simulation failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting database connection tests...")
    
    # Test basic connection
    if not await test_database_connection():
        print("❌ Basic connection test failed")
        return
    
    # Test auth simulation
    if not await test_auth_simulation():
        print("❌ Auth simulation test failed")
        return
    
    print("\n🎉 All tests passed! Database is working correctly.")

if __name__ == "__main__":
    asyncio.run(main()) 