#!/usr/bin/env python3
"""
Setup notifications table for in-app notifications
"""
import asyncio
import asyncpg
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from dotenv import load_dotenv

async def setup_notifications_table():
    """Create notifications table"""
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    # Convert SQLAlchemy URL to asyncpg format
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url, statement_cache_size=0)
        print("✅ Connected to database")
        
        # Read and execute the SQL file
        with open('scripts/create_notifications_table.sql', 'r') as f:
            sql_content = f.read()
        
        await conn.execute(sql_content)
        print("✅ Created notifications table")
        
        # Verify the table was created
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'notifications'
        """)
        
        if tables:
            print("✅ Notifications table verified")
        else:
            print("❌ Notifications table not found")
            return False
        
        await conn.close()
        print("✅ Notifications table setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up notifications table: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_notifications_table())
    sys.exit(0 if success else 1)
