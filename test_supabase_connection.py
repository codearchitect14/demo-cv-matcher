#!/usr/bin/env python3
"""
Test script for Supabase database connection
"""
import asyncio
import os
from dotenv import load_dotenv
from config.database import check_database_connection, create_tables, engine

# Load environment variables
load_dotenv()

async def test_connection():
    """Test the database connection"""
    print("🔍 Testing Supabase Database Connection...")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in .env file")
        return False
    
    print(f"✅ DATABASE_URL found: {database_url[:50]}...")
    
    # Test basic connection
    try:
        print("\n🔄 Testing connection...")
        is_connected = await check_database_connection()
        
        if is_connected:
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    
    # Test table creation (optional)
    try:
        print("\n🔄 Testing table creation...")
        await create_tables()
        print("✅ Tables created/verified successfully!")
        
    except Exception as e:
        print(f"⚠️  Table creation warning: {str(e)}")
        print("This might be normal if tables already exist")
    
    # Test engine disposal
    try:
        await engine.dispose()
        print("✅ Database engine disposed successfully!")
        
    except Exception as e:
        print(f"⚠️  Engine disposal warning: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Database connection test completed!")
    return True

async def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Checking Environment Variables...")
    print("=" * 50)
    
    required_vars = [
        "DATABASE_URL",
        "DB_HOST", 
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD"
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask password for security
            if "PASSWORD" in var:
                display_value = "*" * len(value)
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    print("=" * 50)
    return all_set

async def main():
    """Main test function"""
    print("🚀 Starting Supabase Connection Test")
    print("=" * 50)
    
    # Test environment variables first
    env_ok = await test_environment_variables()
    
    if not env_ok:
        print("\n❌ Environment variables not properly configured!")
        print("Please check your .env file")
        return
    
    print("\n" + "=" * 50)
    
    # Test database connection
    connection_ok = await test_connection()
    
    if connection_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your Supabase connection is working correctly!")
    else:
        print("\n❌ CONNECTION FAILED!")
        print("Please check your Supabase credentials and network connection")

if __name__ == "__main__":
    asyncio.run(main()) 