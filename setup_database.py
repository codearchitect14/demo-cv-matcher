#!/usr/bin/env python3
"""
Database setup script to create tables and add missing columns
"""

import asyncio
import os
from sqlalchemy import text
from config.database import AsyncSessionLocal, engine

async def setup_database():
    """Set up database with correct schema"""
    print("🔧 Setting up database...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if recruiter_id column exists in jobs table
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'jobs' AND column_name = 'recruiter_id'
            """))
            has_recruiter_id = result.fetchone() is not None
            
            if not has_recruiter_id:
                print("➕ Adding recruiter_id column to jobs table...")
                await session.execute(text("""
                    ALTER TABLE jobs 
                    ADD COLUMN recruiter_id INTEGER REFERENCES recruiters(id) ON DELETE CASCADE
                """))
            
            # Check if user_type column exists in interaction_log table
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'interaction_log' AND column_name = 'user_type'
            """))
            has_user_type = result.fetchone() is not None
            
            if not has_user_type:
                print("➕ Adding user_type column to interaction_log table...")
                await session.execute(text("""
                    ALTER TABLE interaction_log 
                    ADD COLUMN user_type VARCHAR(20)
                """))
            
            await session.commit()
            print("✅ Database setup completed successfully!")
            
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            await session.rollback()
            raise

async def main():
    """Main function"""
    try:
        await setup_database()
    except Exception as e:
        print(f"❌ Failed to set up database: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 