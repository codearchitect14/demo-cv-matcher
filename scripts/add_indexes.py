#!/usr/bin/env python3
"""
Database Index Creation Script
Adds performance indexes to improve query response times
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from config.database import get_db_session

# Index creation SQL statements (using regular CREATE INDEX for transaction compatibility)
INDEXES_SQL = [
    # Jobs table indexes
    "CREATE INDEX IF NOT EXISTS idx_jobs_domain ON jobs(domain);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_salary_range ON jobs(salary_min, salary_max);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);",
    
    # Candidates table indexes
    "CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);",
    "CREATE INDEX IF NOT EXISTS idx_candidates_domain ON candidates(domain);",
    "CREATE INDEX IF NOT EXISTS idx_candidates_location ON candidates(location);",
    "CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON candidates(created_at DESC);",
    
    # Applications table indexes (CRITICAL for "Applied" button performance)
    "CREATE INDEX IF NOT EXISTS idx_applications_candidate_job ON applications(candidate_id, job_id);",
    "CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);",
    "CREATE INDEX IF NOT EXISTS idx_applications_candidate_id ON applications(candidate_id);",
    "CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);",
    "CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at DESC);",
    
    # Text search indexes for better ILIKE performance
    "CREATE INDEX IF NOT EXISTS idx_jobs_title_gin ON jobs USING gin(to_tsvector('english', title));",
    "CREATE INDEX IF NOT EXISTS idx_jobs_company_gin ON jobs USING gin(to_tsvector('english', company));",
    "CREATE INDEX IF NOT EXISTS idx_jobs_description_gin ON jobs USING gin(to_tsvector('english', job_description));",
    
    # Composite indexes for common query patterns
    "CREATE INDEX IF NOT EXISTS idx_jobs_domain_location ON jobs(domain, location);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_domain_salary ON jobs(domain, salary_min, salary_max);",
    "CREATE INDEX IF NOT EXISTS idx_candidates_domain_location ON candidates(domain, location);",
]

# Update statistics SQL
ANALYZE_SQL = [
    "ANALYZE jobs;",
    "ANALYZE candidates;",
    "ANALYZE applications;",
]

async def create_indexes():
    """Create all performance indexes"""
    print("🚀 Starting database index creation...")
    print(f"📊 Will create {len(INDEXES_SQL)} indexes")
    
    try:
        async for db in get_db_session():
            print("\n📋 Creating indexes...")
            
            for i, sql in enumerate(INDEXES_SQL, 1):
                try:
                    print(f"  [{i:2d}/{len(INDEXES_SQL)}] Creating index...")
                    await db.execute(text(sql))
                    await db.commit()
                    print(f"  ✅ Index {i} created successfully")
                except Exception as e:
                    print(f"  ⚠️  Index {i} failed (may already exist): {e}")
                    await db.rollback()
            
            print("\n📈 Updating table statistics...")
            for sql in ANALYZE_SQL:
                try:
                    await db.execute(text(sql))
                    await db.commit()
                    print(f"  ✅ Statistics updated")
                except Exception as e:
                    print(f"  ⚠️  Statistics update failed: {e}")
                    await db.rollback()
            
            break  # Exit the async generator
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure your .env file has the correct DATABASE_URL")
        return False
    
    print("\n🎉 All indexes created successfully!")
    print("⚡ Your API endpoints should now be much faster!")
    return True

async def check_existing_indexes():
    """Check which indexes already exist"""
    print("🔍 Checking existing indexes...")
    
    try:
        async for db in get_db_session():
            # Check jobs table indexes
            result = await db.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'jobs' AND indexname LIKE 'idx_jobs_%'
                ORDER BY indexname;
            """))
            existing_jobs = [row[0] for row in result.fetchall()]
            
            # Check candidates table indexes
            result = await db.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'candidates' AND indexname LIKE 'idx_candidates_%'
                ORDER BY indexname;
            """))
            existing_candidates = [row[0] for row in result.fetchall()]
            
            # Check applications table indexes
            result = await db.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'applications' AND indexname LIKE 'idx_applications_%'
                ORDER BY indexname;
            """))
            existing_applications = [row[0] for row in result.fetchall()]
            
            print(f"📊 Existing indexes:")
            print(f"  Jobs: {len(existing_jobs)} indexes")
            print(f"  Candidates: {len(existing_candidates)} indexes")
            print(f"  Applications: {len(existing_applications)} indexes")
            
            if existing_jobs or existing_candidates or existing_applications:
                print("\n📋 Existing index names:")
                for idx in existing_jobs + existing_candidates + existing_applications:
                    print(f"  - {idx}")
            
            break
            
    except Exception as e:
        print(f"❌ Failed to check indexes: {e}")
        return False
    
    return True

async def main():
    """Main function"""
    print("=" * 60)
    print("🗄️  CV Matcher - Database Performance Optimization")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ .env file not found!")
        print("💡 Please create a .env file with your DATABASE_URL")
        return
    
    # Check existing indexes first
    await check_existing_indexes()
    
    print("\n" + "=" * 60)
    response = input("🤔 Do you want to create/update the indexes? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        success = await create_indexes()
        if success:
            print("\n🎯 Next steps:")
            print("1. Restart your FastAPI server")
            print("2. Test your endpoints - they should be much faster!")
            print("3. Check the logs for response times")
    else:
        print("👋 Index creation cancelled")

if __name__ == "__main__":
    asyncio.run(main())
