#!/usr/bin/env python3
"""
Test to verify that ORM operations work without prepared statements
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_orm_operations():
    """Test ORM operations that were causing prepared statement errors"""
    print("🧪 Testing ORM operations with pgbouncer fix...")
    
    try:
        from config.database import get_db_session
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from models.job import Job
        
        # Test 1: Basic ORM query
        print("  Testing basic ORM query...")
        async for db in get_db_session():
            result = await db.execute(select(Job).limit(5))
            jobs = result.scalars().all()
            print(f"    ✅ Basic ORM query works: Retrieved {len(jobs)} jobs")
            break
        
        # Test 2: ORM query with selectinload (this was causing the error)
        print("  Testing ORM query with selectinload...")
        async for db in get_db_session():
            result = await db.execute(
                select(Job)
                .options(selectinload(Job.mandatory_skills))
                .limit(5)
            )
            jobs = result.scalars().all()
            print(f"    ✅ ORM query with selectinload works: Retrieved {len(jobs)} jobs")
            
            # Check if mandatory skills were loaded
            total_skills = sum(len(job.mandatory_skills) for job in jobs)
            print(f"    ✅ Mandatory skills loaded: {total_skills} skills across {len(jobs)} jobs")
            break
        
        # Test 3: Complex ORM query with relationships
        print("  Testing complex ORM query...")
        async for db in get_db_session():
            result = await db.execute(
                select(Job)
                .options(selectinload(Job.mandatory_skills))
                .where(Job.location == "New York")
                .limit(3)
            )
            jobs = result.scalars().all()
            print(f"    ✅ Complex ORM query works: Retrieved {len(jobs)} jobs in New York")
            break
        
        print("🎉 All ORM operations work!")
        return True
        
    except Exception as e:
        print(f"❌ ORM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_crud_operations():
    """Test CRUD operations that use ORM"""
    print("\n🔧 Testing CRUD operations...")
    
    try:
        from config.database import get_db_session
        from db.crud.job import job as job_crud
        
        # Test CRUD get_with_skills operation
        async for db in get_db_session():
            # Get a job with skills (this uses selectinload internally)
            job = await job_crud.get_with_skills(db, 1)
            if job:
                print(f"    ✅ CRUD get_with_skills works: Job {job.id} - {job.title}")
            else:
                print("    ⚠️ No job found with ID 1, but operation completed successfully")
            break
        
        # Test CRUD get_multiple_with_skills operation
        async for db in get_db_session():
            # Get multiple jobs with skills
            jobs = await job_crud.get_multiple_with_skills(db, [1, 2, 3])
            print(f"    ✅ CRUD get_multiple_with_skills works: Retrieved {len(jobs)} jobs")
            break
        
        print("✅ All CRUD operations work!")
        return True
        
    except Exception as e:
        print(f"❌ CRUD test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all ORM tests"""
    print("🚀 Testing ORM Operations with Pgbouncer Fix")
    print("=" * 50)
    
    # Run tests
    orm_ok = await test_orm_operations()
    crud_ok = await test_crud_operations()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    if orm_ok and crud_ok:
        print("🎉 ALL ORM TESTS PASSED!")
        print("\n✅ ORM operations work with pgbouncer:")
        print("   • Basic ORM queries work")
        print("   • selectinload operations work")
        print("   • Complex ORM queries work")
        print("   • CRUD operations work")
        print("   • No prepared statement errors")
        return True
    else:
        print("⚠️ Some ORM tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 