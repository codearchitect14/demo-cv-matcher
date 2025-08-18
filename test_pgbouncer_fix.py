#!/usr/bin/env python3
"""
Test pgbouncer compatibility fix
"""
import asyncio
from sqlalchemy import text
from config.database import engine, get_db_session

async def test_pgbouncer_compatibility():
    """Test pgbouncer compatibility"""
    print("🧪 Testing pgbouncer compatibility...")
    
    try:
        # Test 1: Multiple connections to simulate pgbouncer behavior
        print("📊 Test 1: Multiple connections...")
        for i in range(5):
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Connection {i+1}: {row[0]}")
        
        # Test 2: Session operations
        print("📊 Test 2: Session operations...")
        async for session in get_db_session():
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM candidates"))
                count = result.fetchone()
                print(f"✅ Candidates count: {count[0]}")
                await session.commit()
                break
            finally:
                await session.close()
        
        # Test 3: Multiple rapid queries
        print("📊 Test 3: Multiple rapid queries...")
        for i in range(10):
            async with engine.connect() as conn:
                result = await conn.execute(text(f"SELECT {i} as iteration"))
                row = result.fetchone()
                print(f"✅ Query {i+1}: {row[0]}")
        
        print("🎉 Pgbouncer compatibility test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Pgbouncer test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_pgbouncer_compatibility())
    if success:
        print("🎉 Pgbouncer issue is FIXED!")
    else:
        print("❌ Pgbouncer issue still exists!")
