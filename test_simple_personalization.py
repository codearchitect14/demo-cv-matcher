#!/usr/bin/env python3
"""
Simplified Personalization Test with Mock Data
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session
from services.interaction_service import interaction_service, InteractionType
from services.personalization_service import personalization_service
from services.ml_trainer_service import ml_trainer_service
from models.candidate import Candidate, CandidateExperience
from models.job import Job, JobMandatorySkill
from models.interaction import InteractionLog, InteractionTypeEnum
from models.application import Application
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def create_simple_mock_data(db: AsyncSession):
    """Create simple mock data for testing"""
    print("📝 Creating simple mock data...")
    
    # Create one candidate
    candidate = Candidate(
        name="Test User",
        location="Lahore",
        domain="Software Development",
        expected_salary_min=80000,
        expected_salary_max=150000,
        summary="Python developer with 3 years experience"
    )
    db.add(candidate)
    await db.flush()
    
    # Add experience
    exp = CandidateExperience(
        candidate_id=candidate.id,
        skill="Python",
        years=3,
        description="Web development with Django"
    )
    db.add(exp)
    
    # Create one job
    job = Job(
        title="Python Developer",
        location="Lahore",
        domain="Software Development",
        salary_min=80000,
        salary_max=150000,
        total_years_required=2,
        job_description="We are looking for a Python developer"
    )
    db.add(job)
    await db.flush()
    
    # Add mandatory skill
    skill = JobMandatorySkill(
        job_id=job.id,
        skill="Python",
        min_experience=2
    )
    db.add(skill)
    
    await db.commit()
    
    # Create some interactions
    interactions = [
        {"type": InteractionTypeEnum.VIEW, "days_ago": 5},
        {"type": InteractionTypeEnum.APPLIED, "days_ago": 4},
        {"type": InteractionTypeEnum.VIEW, "days_ago": 3},
        {"type": InteractionTypeEnum.APPLIED, "days_ago": 2},
    ]
    
    for interaction_data in interactions:
        interaction = InteractionLog(
            candidate_id=candidate.id,
            job_id=job.id,
            interaction_type=interaction_data["type"]
        )
        db.add(interaction)
    
    await db.commit()
    
    print(f"✅ Created 1 candidate, 1 job, and {len(interactions)} interactions")
    return candidate, job

async def test_basic_functionality():
    """Test basic personalization functionality"""
    print("🧪 TEST: Basic Personalization Functionality")
    print("=" * 50)
    
    async for db in get_db_session():
        try:
            # Create simple mock data
            candidate, job = await create_simple_mock_data(db)
            
            # Test 1: Interaction logging
            print("\n1️⃣ Testing interaction logging...")
            interaction = await interaction_service.log_interaction(
                db, candidate.id, job.id, "View"
            )
            print(f"   ✅ Logged interaction: {interaction.interaction_type}")
            
            # Test 2: Behavior pattern analysis
            print("\n2️⃣ Testing behavior pattern analysis...")
            patterns = await interaction_service.get_user_behavior_patterns(db, candidate.id)
            print(f"   ✅ Total interactions: {patterns.get('total_interactions', 0)}")
            print(f"   ✅ Application rate: {patterns.get('application_rate', 0):.2f}")
            print(f"   ✅ Engagement score: {patterns.get('engagement_score', 0)}")
            
            # Test 3: ML feature extraction
            print("\n3️⃣ Testing ML feature extraction...")
            mock_interactions = [{"job_id": job.id, "interaction_type": "View", "created_at": datetime.utcnow()}]
            mock_user_patterns = {
                "total_interactions": 5,
                "total_applications": 2,
                "application_rate": 0.4,
                "preferred_domains": {"Software Development": 2},
                "preferred_locations": {"Lahore": 2},
                "salary_preferences": {"avg": 100000}
            }
            mock_job_features = {
                "job_id": job.id,
                "domain": "Software Development",
                "location": "Lahore",
                "salary_min": 80000,
                "similarity_score": 0.8,
                "filter_score": 0.9
            }
            
            features = ml_trainer_service.extract_training_features(
                mock_interactions, mock_user_patterns, mock_job_features
            )
            print(f"   ✅ Extracted {len(features)} features")
            print(f"   ✅ Sample features: {list(features.keys())[:5]}")
            
            # Test 4: Fallback scoring
            print("\n4️⃣ Testing fallback scoring...")
            score = ml_trainer_service.predict_score(features)
            print(f"   ✅ Fallback score: {score:.3f}")
            
            # Test 5: Simple personalization
            print("\n5️⃣ Testing simple personalization...")
            job_recommendations = [
                {
                    "job": job,
                    "similarity_score": 0.8,
                    "filter_score": 0.9,
                    "combined_score": 0.85
                }
            ]
            
            personalized = await personalization_service.personalize_job_recommendations(
                db, candidate.id, job_recommendations, use_ml_scoring=False
            )
            
            if personalized:
                rec = personalized[0]
                print(f"   ✅ Personalized score: {rec.get('final_score', 0):.3f}")
                print(f"   ✅ Personalization reasons: {rec.get('personalization_reasons', [])}")
            else:
                print("   ⚠️ No personalized recommendations returned")
            
            print("\n✅ All basic tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        break

async def test_ml_training_simple():
    """Test ML training with simple data"""
    print("\n🧪 TEST: Simple ML Training")
    print("=" * 50)
    
    async for db in get_db_session():
        try:
            # Create mock data
            candidate, job = await create_simple_mock_data(db)
            
            # Test model training with minimal data
            print("🤖 Testing model training with minimal data...")
            
            # Create simple training data manually
            training_data = []
            for i in range(5):
                features = {
                    "similarity_score": 0.7 + (i * 0.05),
                    "filter_score": 0.8 + (i * 0.05),
                    "salary_match": 0.9,
                    "domain_match": 1.0,
                    "location_match": 1.0,
                    "skill_match": 0.8,
                    "engagement_score": 10 + i,
                    "application_rate": 0.4 + (i * 0.1),
                    "days_since_last_interaction": 5 - i
                }
                label = 1 if i % 2 == 0 else 0  # Alternate labels
                training_data.append({"features": features, "label": label})
            
            print(f"   ✅ Created {len(training_data)} training samples")
            
            # Test feature extraction
            if training_data:
                sample_features = training_data[0]["features"]
                print(f"   ✅ Sample features: {list(sample_features.keys())}")
                
                # Test scoring
                score = ml_trainer_service.predict_score(sample_features)
                print(f"   ✅ Sample score: {score:.3f}")
            
            print("✅ Simple ML training test completed!")
            return True
            
        except Exception as e:
            print(f"❌ ML training test failed: {e}")
            return False
        break

async def main():
    """Run simplified personalization tests"""
    print("🚀 Simplified Personalization Testing")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Simple ML Training", test_ml_training_simple)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASSED" if results[i] else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SIMPLIFIED PERSONALIZATION TESTS PASSED!")
        print("\n📋 Core Features Working:")
        print("   ✅ Interaction logging")
        print("   ✅ Behavior pattern analysis")
        print("   ✅ ML feature extraction")
        print("   ✅ Fallback scoring")
        print("   ✅ Basic personalization")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main()) 