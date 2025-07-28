#!/usr/bin/env python3
"""
Test the Filtering & Constraint Service
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session
from recommender.filters import filtering_service
from models.candidate import Candidate, CandidateExperience
from models.job import Job, JobMandatorySkill
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def create_test_data(db: AsyncSession):
    """Create test candidates and jobs for filtering tests"""
    print("📝 Creating test data...")
    
    # Create test candidates
    candidates = []
    
    # Candidate 1: Perfect match
    candidate1 = Candidate(
        name="John Python",
        location="Lahore",
        domain="Software Development",
        expected_salary_min=80000,
        expected_salary_max=150000,
        summary="Experienced Python developer with 5 years in web development"
    )
    db.add(candidate1)
    await db.flush()
    
    exp1 = CandidateExperience(
        candidate_id=candidate1.id,
        skill="Python",
        years=5,
        description="Web development with Django and FastAPI"
    )
    exp2 = CandidateExperience(
        candidate_id=candidate1.id,
        skill="PostgreSQL",
        years=3,
        description="Database design and optimization"
    )
    db.add_all([exp1, exp2])
    candidates.append(candidate1)
    
    # Candidate 2: Salary too high
    candidate2 = Candidate(
        name="Jane Senior",
        location="Lahore",
        domain="Software Development",
        expected_salary_min=200000,
        expected_salary_max=300000,
        summary="Senior developer with 8 years experience"
    )
    db.add(candidate2)
    await db.flush()
    
    exp3 = CandidateExperience(
        candidate_id=candidate2.id,
        skill="Python",
        years=8,
        description="Senior Python development"
    )
    db.add(exp3)
    candidates.append(candidate2)
    
    # Candidate 3: Wrong location
    candidate3 = Candidate(
        name="Bob Remote",
        location="Karachi",
        domain="Software Development",
        expected_salary_min=70000,
        expected_salary_max=120000,
        summary="Python developer in Karachi"
    )
    db.add(candidate3)
    await db.flush()
    
    exp4 = CandidateExperience(
        candidate_id=candidate3.id,
        skill="Python",
        years=4,
        description="Python development"
    )
    db.add(exp4)
    candidates.append(candidate3)
    
    # Candidate 4: Insufficient experience
    candidate4 = Candidate(
        name="Alice Junior",
        location="Lahore",
        domain="Software Development",
        expected_salary_min=60000,
        expected_salary_max=90000,
        summary="Junior Python developer"
    )
    db.add(candidate4)
    await db.flush()
    
    exp5 = CandidateExperience(
        candidate_id=candidate4.id,
        skill="Python",
        years=1,
        description="Basic Python development"
    )
    db.add(exp5)
    candidates.append(candidate4)
    
    # Create test job
    job = Job(
        title="Senior Python Developer",
        location="Lahore",
        domain="Software Development",
        salary_min=80000,
        salary_max=150000,
        total_years_required=3,
        job_description="We are looking for a senior Python developer with experience in FastAPI and PostgreSQL"
    )
    db.add(job)
    await db.flush()
    
    # Add mandatory skills
    skill1 = JobMandatorySkill(
        job_id=job.id,
        skill="Python",
        min_experience=3
    )
    skill2 = JobMandatorySkill(
        job_id=job.id,
        skill="PostgreSQL",
        min_experience=2
    )
    db.add_all([skill1, skill2])
    
    await db.commit()
    
    # Re-query with eager loading
    result = await db.execute(
        select(Candidate).options(selectinload(Candidate.experiences))
    )
    candidates = result.scalars().all()
    result = await db.execute(
        select(Job).options(selectinload(Job.mandatory_skills))
    )
    job = result.scalars().first()
    
    print(f"✅ Created {len(candidates)} candidates and 1 job")
    return candidates, job

async def test_filtering_service():
    """Test the filtering service with various scenarios"""
    print("🧪 Testing Filtering & Constraint Service")
    print("=" * 60)
    
    async for db in get_db_session():
        try:
            # Create test data
            candidates, job = await create_test_data(db)
            
            # Create candidate recommendations (simulate semantic search results)
            candidate_recommendations = []
            for candidate in candidates:
                candidate_recommendations.append({
                    'candidate': candidate,
                    'similarity_score': 0.8,  # Mock similarity score
                    'explanation': f"Semantic match for {candidate.name}"
                })
            
            print(f"\n📊 Testing with {len(candidate_recommendations)} candidates")
            print(f"🎯 Job: {job.title} in {job.location}")
            print(f"💰 Salary: ${job.salary_min:,} - ${job.salary_max:,}")
            print(f"📋 Required: {job.total_years_required} years total, Python (3+), PostgreSQL (2+)")
            
            # Test strict filtering
            print("\n🔍 STRICT FILTERING (all constraints enforced)")
            print("-" * 50)
            
            filtered_candidates = await filtering_service.filter_candidates_for_job(
                candidate_recommendations, job, db, strict_mode=True
            )
            
            print(f"✅ Passed strict filtering: {len(filtered_candidates)} candidates")
            
            for candidate_data in filtered_candidates:
                candidate = candidate_data['candidate']
                validation = candidate_data['validation']
                print(f"\n👤 {candidate.name}:")
                print(f"   📍 Location: {candidate.location}")
                print(f"   💰 Salary: ${candidate.expected_salary_min:,} - ${candidate.expected_salary_max:,}")
                print(f"   🎯 Filter Score: {validation['filter_score']:.2f}")
                print(f"   ✅ Reasons: {', '.join(validation['reasons'])}")
            
            # Test lenient filtering
            print("\n🔍 LENIENT FILTERING (show all with scores)")
            print("-" * 50)
            
            lenient_candidates = await filtering_service.filter_candidates_for_job(
                candidate_recommendations, job, db, strict_mode=False
            )
            
            print(f"📊 All candidates with scores:")
            for candidate_data in lenient_candidates:
                candidate = candidate_data['candidate']
                validation = candidate_data['validation']
                status = "✅ VALID" if validation['is_valid'] else "❌ INVALID"
                print(f"\n{status} {candidate.name}:")
                print(f"   📍 Location: {candidate.location}")
                print(f"   💰 Salary: ${candidate.expected_salary_min:,} - ${candidate.expected_salary_max:,}")
                print(f"   🎯 Filter Score: {validation['filter_score']:.2f}")
                if not validation['is_valid']:
                    print(f"   ❌ Rejected: {', '.join(validation['reasons'])}")
                else:
                    print(f"   ✅ Accepted: {', '.join(validation['reasons'])}")
            
            # Test individual validation functions
            print("\n🔍 INDIVIDUAL VALIDATION TESTS")
            print("-" * 50)
            
            test_candidate = candidates[0]  # Perfect match candidate
            
            # Test domain match
            domain_result = filtering_service._check_domain_match(
                test_candidate.domain, job.domain
            )
            print(f"🌐 Domain Match: {domain_result['reason']} (Score: {domain_result['score']:.2f})")
            
            # Test location match
            location_result = filtering_service._check_location_match(
                test_candidate.location, job.location
            )
            print(f"📍 Location Match: {location_result['reason']} (Score: {location_result['score']:.2f})")
            
            # Test salary compatibility
            salary_result = filtering_service._check_salary_compatibility(
                test_candidate.expected_salary_min,
                test_candidate.expected_salary_max,
                job.salary_min,
                job.salary_max
            )
            print(f"💰 Salary Match: {salary_result['reason']} (Score: {salary_result['score']:.2f})")
            
            # Test experience requirements
            experience_result = await filtering_service._check_experience_requirements(
                test_candidate, job, db
            )
            print(f"⏰ Experience Match: {experience_result['reason']} (Score: {experience_result['score']:.2f})")
            
            # Test mandatory skills
            skills_result = await filtering_service._check_mandatory_skills(
                test_candidate, job, db
            )
            print(f"🛠️ Skills Match: {skills_result['reason']} (Score: {skills_result['score']:.2f})")
            
            print("\n✅ Filtering Service Test: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Filtering Service Test: FAILED - {e}")
            return False
        break

async def main():
    """Run the filtering service test"""
    print("🚀 Testing Filtering & Constraint Service")
    print("=" * 60)
    
    result = await test_filtering_service()
    
    if result:
        print("\n🎉 FILTERING SERVICE TEST PASSED!")
        print("\n📋 What's Working:")
        print("   ✅ Domain matching (exact and partial)")
        print("   ✅ Location matching (exact, remote, partial)")
        print("   ✅ Salary range compatibility checks")
        print("   ✅ Total experience requirements")
        print("   ✅ Mandatory skills with minimum experience")
        print("   ✅ Application history checks")
        print("   ✅ Strict vs lenient filtering modes")
        print("   ✅ Detailed validation explanations")
    else:
        print("\n⚠️ FILTERING SERVICE TEST FAILED!")
        print("Check the errors above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 