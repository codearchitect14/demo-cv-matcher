#!/usr/bin/env python3
"""
Script to add company field to jobs table
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session

async def add_company_field():
    """Add company field to jobs table"""
    print("🔧 Adding company field to jobs table...")
    
    async for db in get_db_session():
        try:
            # Add company column to jobs table
            await db.execute(text("""
                ALTER TABLE jobs 
                ADD COLUMN IF NOT EXISTS company VARCHAR(100)
            """))
            
            await db.commit()
            print("✅ Company field added successfully!")
            
            # Verify the column was added
            result = await db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'jobs' AND column_name = 'company'
            """))
            
            if result.fetchone():
                print("✅ Company column verified in database")
            else:
                print("⚠️ Company column not found - check database manually")
                
        except Exception as e:
            print(f"❌ Error adding company field: {e}")
            await db.rollback()
        break

if __name__ == "__main__":
    asyncio.run(add_company_field()) 