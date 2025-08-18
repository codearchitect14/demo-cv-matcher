#!/usr/bin/env python3
"""
Simple database connection test
"""
import asyncio
from sqlalchemy import text
from config.database import engine

async def test_simple_connection():
    """Test simple database connection"""
    print("🧪 Testing simple database connection...")
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Connection successful: {row[0]}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_connection())
    if success:
        print("🎉 Database connection is working!")
    else:
        print("❌ Database connection failed!")
