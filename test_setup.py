# File: test_setup.py
"""
Test setup and database for testing modules 1-5
Run this first to test your implementation
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import AsyncSessionLocal, engine, Base
from db.connection import init_database, reset_database
from services.candidate_service import CandidateService
from schemas.candidate import CandidateCreate, CandidateExperienceCreate
from schemas.search import CandidateSearchFilter


async def test_database_connection():
    """Test database connection"""
    print("=== Testing Database Connection ===")
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_models_and_schemas():
    """Test models and schemas"""
    print("\n=== Testing Models and Schemas ===")
    try:
        # Test schema validation
        candidate_data = CandidateCreate(
            name="John Doe",
            location="New York",
            domain="Software Engineering",
            expected_salary_min=80000,
            expected_salary_max=120000,
            experiences=[
                CandidateExperienceCreate(
                    skill="Python",
                    years=3,
                    description="Backend development with Django and FastAPI"
                ),
                CandidateExperienceCreate(
                    skill="JavaScript",
                    years=2,
                    description="Frontend development with React"
                )
            ]
        )
        print("✅ Schema validation successful")
        print(f"   - Candidate: {candidate_data.name}")
        print(f"   - Skills: {[exp.skill for exp in candidate_data.experiences]}")
        return True
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False


async def test_crud_operations():
    """Test CRUD operations"""
    print("\n=== Testing CRUD Operations ===")
    try:
        async with AsyncSessionLocal() as session:
            # Test candidate CRUD
            from db.crud.candidate import candidate as candidate_crud
            
            # Create test candidate
            candidate_data = CandidateCreate(
                name="Alice Smith",
                location="San Francisco",
                domain="Data Science",
                expected_salary_min=90000,
                expected_salary_max=140000,
                experiences=[
                    CandidateExperienceCreate(
                        skill="Python",
                        years=4,
                        description="Data analysis with pandas and numpy"
                    )
                ]
            )
            
            candidate = await candidate_crud.create_with_experiences(session, candidate_data)
            print(f"✅ Created candidate: {candidate.name} (ID: {candidate.id})")
            
            # Read candidate
            retrieved = await candidate_crud.get_with_experiences(session, candidate.id)
            print(f"✅ Retrieved candidate: {retrieved.name}")
            print(f"   - Experiences: {[exp.skill for exp in retrieved.experiences]}")
            
            # Search by domain
            domain_candidates = await candidate_crud.get_by_domain(session, "Data Science")
            print(f"✅ Found {len(domain_candidates)} candidates in Data Science")
            
            return True
    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
        return False


async def test_candidate_service():
    """Test candidate service layer"""
    print("\n=== Testing Candidate Service ===")
    try:
        async with AsyncSessionLocal() as session:
            service = CandidateService()
            
            # Create candidate via service
            candidate_data = CandidateCreate(
                name="Bob Johnson",
                location="Austin",
                domain="Software Engineering",
                expected_salary_min=75000,
                expected_salary_max=110000,
                experiences=[
                    CandidateExperienceCreate(
                        skill="Java",
                        years=5,
                        description="Enterprise applications"
                    ),
                    CandidateExperienceCreate(
                        skill="Spring Boot",
                        years=3,
                        description="Microservices development"
                    )
                ]
            )
            
            candidate = await service.create_candidate(session, candidate_data)
            print(f"✅ Service created candidate: {candidate.name} (ID: {candidate.id})")
            
            # Get candidate stats
            stats = await service.get_candidate_stats(session, candidate.id)
            print(f"✅ Candidate stats:")
            print(f"   - Total skills: {stats['total_skills']}")
            print(f"   - Max experience: {stats['max_experience_years']} years")
            print(f"   - Skills: {stats['skills_list']}")
            
            # Search candidates
            search_filter = CandidateSearchFilter(
                domain="Software Engineering",
                skills=["Java"],
                min_experience=2
            )
            search_results = await service.search_candidates(session, search_filter)
            print(f"✅ Search found {len(search_results)} candidates")
            
            # Add new experience
            updated = await service.add_experience(
                session, candidate.id, "Docker", 2, "Container orchestration"
            )
            print(f"✅ Added Docker experience to {updated.name}")
            
            return True
    except Exception as e:
        print(f"❌ Candidate service failed: {e}")
        return False


async def test_database_utilities():
    """Test database utilities"""
    print("\n=== Testing Database Utilities ===")
    try:
        async with AsyncSessionLocal() as session:
            from db.utils import get_database_stats
            
            stats = await get_database_stats(session)
            print("✅ Database statistics:")
            print(f"   - Candidates: {stats['candidates']}")
            print(f"   - Jobs: {stats['jobs']}")
            print(f"   - Applications: {stats['applications']}")
            print(f"   - Interactions: {stats['interactions']}")
            
            return True
    except Exception as e:
        print(f"❌ Database utilities failed: {e}")
        return False


async def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting Comprehensive Test for Modules 1-5")
    print("=" * 50)
    
    # Reset database for clean testing
    await reset_database()
    
    tests = [
        test_database_connection,
        test_models_and_schemas,
        test_crud_operations,
        test_candidate_service,
        test_database_utilities
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your implementation is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
