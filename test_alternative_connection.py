#!/usr/bin/env python3
"""
Alternative connection test for Supabase
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Load environment variables
load_dotenv()

async def test_alternative_connection():
    """Test connection with different SSL settings"""
    print("🔍 Testing Alternative Connection Methods...")
    print("=" * 50)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    # Method 1: No SSL
    print("\n🔄 Method 1: Testing without SSL...")
    try:
        engine1 = create_async_engine(
            database_url,
            echo=False,
            future=True,
            connect_args={"ssl": False}
        )
        
        async with engine1.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Connection successful without SSL")
        
        await engine1.dispose()
        
    except Exception as e:
        print(f"❌ Method 1 failed: {str(e)}")
    
    # Method 2: With SSL but different settings
    print("\n🔄 Method 2: Testing with SSL...")
    try:
        engine2 = create_async_engine(
            database_url,
            echo=False,
            future=True,
            connect_args={
                "ssl": True,
                "ssl_context": None
            }
        )
        
        async with engine2.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Connection successful with SSL")
        
        await engine2.dispose()
        
    except Exception as e:
        print(f"❌ Method 2 failed: {str(e)}")
    
    # Method 3: Direct connection string
    print("\n🔄 Method 3: Testing direct connection...")
    try:
        # Extract components from DATABASE_URL
        if "postgresql+asyncpg://" in database_url:
            # Remove the +asyncpg part
            direct_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
            
            engine3 = create_async_engine(
                direct_url,
                echo=False,
                future=True,
                connect_args={"ssl": True}
            )
            
            async with engine3.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                print("✅ Direct connection successful")
            
            await engine3.dispose()
            
    except Exception as e:
        print(f"❌ Method 3 failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Alternative connection tests completed!")

async def test_ping():
    """Test basic ping to the host"""
    import subprocess
    import platform
    
    print("🔍 Testing ping to Supabase host...")
    print("=" * 50)
    
    db_host = os.getenv("DB_HOST")
    if not db_host:
        print("❌ DB_HOST not found")
        return
    
    # Determine ping command based on OS
    if platform.system().lower() == "windows":
        ping_cmd = ["ping", "-n", "4", db_host]
    else:
        ping_cmd = ["ping", "-c", "4", db_host]
    
    try:
        result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Ping successful!")
            print(result.stdout)
        else:
            print("❌ Ping failed!")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("❌ Ping timed out!")
    except Exception as e:
        print(f"❌ Ping error: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 Starting Alternative Connection Tests")
    print("=" * 50)
    
    # Test ping first
    await test_ping()
    
    # Test alternative connections
    await test_alternative_connection()

if __name__ == "__main__":
    asyncio.run(main()) 