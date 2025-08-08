#!/usr/bin/env python3
"""
Test to verify the NUCLEAR pgbouncer compatibility fix
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_nuclear_database_connection():
    """Test database connection with NUCLEAR pgbouncer compatibility"""
    print("🧪 Testing NUCLEAR database connection fix...")
    
    try:
        from config.database import get_db_session
        from sqlalchemy import text
        
        # Test 1: Basic connection
        print("  Testing basic connection...")
        async for db in get_db_session():
            result = await db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"    ✅ Basic connection works: {row}")
            break
        
        # Test 2: Jobs query (the one that was failing)
        print("  Testing jobs query...")
        async for db in get_db_session():
            result = await db.execute(text("SELECT COUNT(*) FROM jobs"))
            count = result.fetchone()
            print(f"    ✅ Jobs query works: Found {count[0]} jobs")
            break
        
        # Test 3: Complex query with joins (the exact one that was failing)
        print("  Testing complex query with joins...")
        async for db in get_db_session():
            result = await db.execute(text("""
                SELECT j.*, jms.skill, jms.min_experience, jms.id as skill_id,
                       jms.created_at as skill_created_at, jms.updated_at as skill_updated_at
                FROM jobs j
                LEFT JOIN job_mandatory_skills jms ON j.id = jms.job_id
                WHERE j.location = :location
                ORDER BY j.created_at DESC
                LIMIT :limit OFFSET :offset
            """), {"location": "New York", "limit": 10, "offset": 0})
            rows = result.fetchall()
            print(f"    ✅ Complex query works: Retrieved {len(rows)} rows")
            break
        
        # Test 4: Multiple complex queries (to test for statement conflicts)
        print("  Testing multiple complex queries...")
        for i in range(3):
            async for db in get_db_session():
                result = await db.execute(text("""
                    SELECT j.*, jms.skill, jms.min_experience, jms.id as skill_id,
                           jms.created_at as skill_created_at, jms.updated_at as skill_updated_at
                    FROM jobs j
                    LEFT JOIN job_mandatory_skills jms ON j.id = jms.job_id
                    WHERE j.id IN (:id1, :id2, :id3)
                """), {"id1": 1, "id2": 2, "id3": 3})
                rows = result.fetchall()
                print(f"    ✅ Query {i+1} works: Retrieved {len(rows)} rows")
                break
        
        print("🎉 All NUCLEAR database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ NUCLEAR database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_simulation():
    """Simulate the API endpoint that was failing"""
    print("\n🔧 Testing API simulation with NUCLEAR fix...")
    
    try:
        from config.database import get_db_session
        from sqlalchemy import text
        
        # Simulate the exact API endpoint that was failing
        async for db in get_db_session():
            # Build the query like the API does
            query = """
                SELECT j.*, jms.skill, jms.min_experience, jms.id as skill_id,
                       jms.created_at as skill_created_at, jms.updated_at as skill_updated_at
                FROM jobs j
                LEFT JOIN job_mandatory_skills jms ON j.id = jms.job_id
                WHERE 1=1
                ORDER BY j.created_at DESC
                LIMIT :limit OFFSET :offset
            """
            params = {"limit": 10, "offset": 0}
            
            result = await db.execute(text(query), params)
            rows = result.fetchall()
            
            # Group by job like the API does
            jobs = {}
            for row in rows:
                job_id = row.id
                if job_id not in jobs:
                    jobs[job_id] = {
                        "id": row.id,
                        "title": row.title,
                        "company": row.company,
                        "location": row.location,
                        "salary_min": row.salary_min,
                        "salary_max": row.salary_max,
                        "domain": row.domain,
                        "total_years_required": row.total_years_required,
                        "job_description": row.job_description,
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                        "mandatory_skills": []
                    }
                
                if row.skill:
                    jobs[job_id]["mandatory_skills"].append({
                        "id": row.skill_id,
                        "skill": row.skill,
                        "min_experience": row.min_experience,
                        "job_id": job_id,
                        "created_at": row.skill_created_at,
                        "updated_at": row.skill_updated_at
                    })
            
            print(f"    ✅ API simulation works: Retrieved {len(jobs)} jobs")
            break
        
        print("✅ API simulation successful!")
        return True
        
    except Exception as e:
        print(f"❌ API simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all NUCLEAR tests"""
    print("🚀 Testing NUCLEAR Pgbouncer Compatibility Fix")
    print("=" * 50)
    
    # Run tests
    db_ok = await test_nuclear_database_connection()
    api_ok = await test_api_simulation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    if db_ok and api_ok:
        print("🎉 ALL NUCLEAR TESTS PASSED!")
        print("\n✅ NUCLEAR pgbouncer compatibility fix is working:")
        print("   • All prepared statements disabled")
        print("   • Raw SQL queries work")
        print("   • Complex joins work")
        print("   • Multiple queries work")
        print("   • API simulation works")
        print("   • NO MORE PREPARED STATEMENT ERRORS")
        return True
    else:
        print("⚠️ Some NUCLEAR tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 