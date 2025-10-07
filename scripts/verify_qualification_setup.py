#!/usr/bin/env python3
"""
Simple script to verify qualification columns were added successfully
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def verify_setup():
    """Quick verification that qualification columns exist"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        print("🔌 Connecting to database...")
        conn = await asyncpg.connect(database_url)
        print("✅ Connected successfully")
        
        # Check jobs table
        print("\n📊 Checking jobs table...")
        jobs_result = await conn.fetch("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'jobs' AND column_name = 'threshold_score'
        """)
        
        if jobs_result:
            print(f"✅ threshold_score column found: {jobs_result[0]['data_type']} (default: {jobs_result[0]['column_default']})")
        else:
            print("❌ threshold_score column not found")
        
        # Check applications table
        print("\n📊 Checking applications table...")
        app_result = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'applications' 
            AND column_name IN ('candidate_score', 'is_qualified')
            ORDER BY column_name
        """)
        
        if len(app_result) == 2:
            print("✅ Applications table columns found:")
            for col in app_result:
                print(f"   • {col['column_name']}: {col['data_type']}")
        else:
            print(f"❌ Missing columns in applications table. Found: {[col['column_name'] for col in app_result]}")
        
        # Check some sample data
        print("\n📈 Checking sample data...")
        sample_apps = await conn.fetch("""
            SELECT COUNT(*) as total, 
                   COUNT(candidate_score) as with_score,
                   COUNT(is_qualified) as with_qualified
            FROM applications
        """)
        
        if sample_apps:
            stats = sample_apps[0]
            print(f"✅ Applications data: {stats['total']} total, {stats['with_score']} with scores, {stats['with_qualified']} with qualification")
        
        await conn.close()
        print("\n🎉 Verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying qualification setup...")
    asyncio.run(verify_setup())



