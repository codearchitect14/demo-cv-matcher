#!/usr/bin/env python3
"""
Script to add recruiter assignment functionality to the database
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def add_recruiter_assignment():
    """Add recruiter_id column to jobs table"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        print("🔌 Connecting to database...")
        conn = await asyncpg.connect(database_url, statement_cache_size=0)
        print("✅ Connected successfully")
        
        # Check if recruiter_id column already exists
        print("🔍 Checking if recruiter_id column already exists...")
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'jobs' 
                AND column_name = 'recruiter_id'
            )
        """)
        
        if column_exists:
            print("⚠️  recruiter_id column already exists in jobs table")
            await conn.close()
            return True
        
        # Check if recruiters table exists
        print("🔍 Checking if recruiters table exists...")
        recruiters_table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = 'recruiters'
            )
        """)
        
        if not recruiters_table_exists:
            print("❌ recruiters table does not exist. Please create it first.")
            await conn.close()
            return False
        
        # Get count of existing recruiters
        recruiter_count = await conn.fetchval("SELECT COUNT(*) FROM recruiters")
        print(f"📊 Found {recruiter_count} recruiters in the database")
        
        if recruiter_count == 0:
            print("❌ No recruiters found. Please add at least one recruiter first.")
            await conn.close()
            return False
        
        # Get the first recruiter ID for default assignment
        default_recruiter_id = await conn.fetchval("SELECT id FROM recruiters LIMIT 1")
        print(f"🎯 Will assign default recruiter ID: {default_recruiter_id}")
        
        # Execute the migration
        print("🚀 Starting migration...")
        
        # Add recruiter_id column
        print("   Adding recruiter_id column...")
        await conn.execute("ALTER TABLE jobs ADD COLUMN recruiter_id INTEGER")
        
        # Add foreign key constraint
        print("   Adding foreign key constraint...")
        await conn.execute("""
            ALTER TABLE jobs 
            ADD CONSTRAINT fk_jobs_recruiter_id 
            FOREIGN KEY (recruiter_id) REFERENCES recruiters(id) ON DELETE SET NULL
        """)
        
        # Create index
        print("   Creating index...")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_jobs_recruiter_id ON jobs (recruiter_id)")
        
        # Update existing jobs with default recruiter
        print("   Updating existing jobs with default recruiter...")
        jobs_updated = await conn.fetchval("""
            UPDATE jobs 
            SET recruiter_id = $1 
            WHERE recruiter_id IS NULL
        """, default_recruiter_id)
        
        print(f"   Updated {jobs_updated} jobs with default recruiter")
        
        # Make recruiter_id NOT NULL
        print("   Making recruiter_id NOT NULL...")
        await conn.execute("ALTER TABLE jobs ALTER COLUMN recruiter_id SET NOT NULL")
        
        # Add comment
        print("   Adding column comment...")
        await conn.execute("""
            COMMENT ON COLUMN jobs.recruiter_id IS 'ID of the recruiter assigned to manage this job'
        """)
        
        # Verify the changes
        print("🔍 Verifying changes...")
        column_info = await conn.fetchrow("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'jobs' 
            AND column_name = 'recruiter_id'
        """)
        
        if column_info:
            print("✅ Column added successfully:")
            print(f"   Column: {column_info['column_name']}")
            print(f"   Type: {column_info['data_type']}")
            print(f"   Nullable: {column_info['is_nullable']}")
            print(f"   Default: {column_info['column_default']}")
        
        # Show job assignments
        print("\n📋 Job-Recruiter Assignments:")
        assignments = await conn.fetch("""
            SELECT j.id, j.title, j.company, r.name as recruiter_name
            FROM jobs j
            LEFT JOIN recruiters r ON j.recruiter_id = r.id
            ORDER BY j.id
        """)
        
        for assignment in assignments:
            print(f"   Job #{assignment['id']}: {assignment['title']} at {assignment['company']} → {assignment['recruiter_name']}")
        
        await conn.close()
        print("\n🎉 Recruiter assignment migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Adding Recruiter Assignment Functionality")
    print("=" * 50)
    
    success = asyncio.run(add_recruiter_assignment())
    
    if success:
        print("\n✅ Next steps:")
        print("   1. Update the Job model to include recruiter_id field")
        print("   2. Modify job creation API to accept recruiter_id")
        print("   3. Add recruiter validation in job creation")
    else:
        print("\n❌ Migration failed. Please check the errors above.")

