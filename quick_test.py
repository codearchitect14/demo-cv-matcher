#!/usr/bin/env python3
"""
Quick test to verify database connection works
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import AsyncSessionLocal, engine
from sqlalchemy import text

async def quick_test():
    """Quick database connection test"""
    
    print("🔍 Quick database test...")
    
    try:
        # Test basic connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Database connection works: {row}")
        
        # Test session
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
            count = result.fetchone()
            print(f"✅ Session works: Found {count[0]} jobs")
        
        print("\n🎉 Database is working correctly!")
        print("🚀 You can now start the server:")
        print("   python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(quick_test()) 