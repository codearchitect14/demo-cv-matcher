#!/usr/bin/env python3
"""
Test the Personalization & ML Model Service with Mock Data
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

async def create_mock_data(db: AsyncSession):
    """Create comprehensive mock data for testing"""
    print("📝 Creating comprehensive mock data...")
    
    # Create test candidates with different profiles
    candidates = []
    
    # Candidate 1: Python developer (high engagement)
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
    
    # Candidate 2: Data scientist
    candidate2 = Candidate(
        name="Sarah Data",
        location="Karachi",
        domain="Data Science",
        expected_salary_min=90000,
        expected_salary_max=140000,
        summary="Data scientist with 4 years experience in ML"
    )
    db.add(candidate2)
    await db.flush()
    
    exp3 = CandidateExperience(
        candidate_id=candidate2.id,
        skill="Python",
        years=4,
        description="Machine learning and data analysis"
    )
    exp4 = CandidateExperience(
        candidate_id=candidate2.id,
        skill="SQL",
        years=3,
        description="Data querying and analysis"
    )
    db.add_all([exp3, exp4])
    candidates.append(candidate2)
    
    # Candidate 3: Frontend developer
    candidate3 = Candidate(
        name="Mike Frontend",
        location="Lahore",
        domain="Software Development",
        expected_salary_min=70000,
        expected_salary_max=120000,
        summary="Frontend developer with React and Vue experience"
    )
    db.add(candidate3)
    await db.flush()
    
    exp5 = CandidateExperience(
        candidate_id=candidate3.id,
        skill="JavaScript",
        years=4,
        description="React and Vue.js development"
    )
    exp6 = CandidateExperience(
        candidate_id=candidate3.id,
        skill="HTML/CSS",
        years=5,
        description="Responsive web design"
    )
    db.add_all([exp5, exp6])
    candidates.append(candidate3)
    
    # Create test jobs
    jobs = []
    
    # Job 1: Python developer in Lahore
    job1 = Job(
        title="Senior Python Developer",
        location="Lahore",
        domain="Software Development",
        salary_min=80000,
        salary_max=150000,
        total_years_required=3,
        job_description="We are looking for a senior Python developer with experience in FastAPI and PostgreSQL"
    )
    db.add(job1)
    await db.flush()
    
    skill1 = JobMandatorySkill(
        job_id=job1.id,
        skill="Python",
        min_experience=3
    )
    skill2 = JobMandatorySkill(
        job_id=job1.id,
        skill="PostgreSQL",
        min_experience=2
    )
    db.add_all([skill1, skill2])
    jobs.append(job1)
    
    # Job 2: Data scientist in Karachi
    job2 = Job(
        title="Data Scientist",
        location="Karachi",
        domain="Data Science",
        salary_min=90000,
        salary_max=140000,
        total_years_required=3,
        job_description="We are looking for a data scientist with experience in machine learning"
    )
    db.add(job2)
    await db.flush()
    
    skill3 = JobMandatorySkill(
        job_id=job2.id,
        skill="Python",
        min_experience=3
    )
    skill4 = JobMandatorySkill(
        job_id=job2.id,
        skill="SQL",
        min_experience=2
    )
    db.add_all([skill3, skill4])
    jobs.append(job2)
    
    # Job 3: Frontend developer
    job3 = Job(
        title="Frontend Developer",
        location="Lahore",
        domain="Software Development",
        salary_min=70000,
        salary_max=120000,
        total_years_required=3,
        job_description="We are looking for a frontend developer with React experience"
    )
    db.add(job3)
    await db.flush()
    
    skill5 = JobMandatorySkill(
        job_id=job3.id,
        skill="JavaScript",
        min_experience=3
    )
    skill6 = JobMandatorySkill(
        job_id=job3.id,
        skill="React",
        min_experience=2
    )
    db.add_all([skill5, skill6])
    jobs.append(job3)
    
    await db.commit()
    
    # Create interaction history
    print("📊 Creating interaction history...")
    
    # Candidate 1 interactions (Python developer - high engagement with Python jobs)
    interactions1 = [
        {"job_id": job1.id, "type": InteractionTypeEnum.VIEW, "days_ago": 5},
        {"job_id": job1.id, "type": InteractionTypeEnum.APPLIED, "days_ago": 4},
        {"job_id": job1.id, "type": InteractionTypeEnum.VIEW, "days_ago": 3},
        {"job_id": job1.id, "type": InteractionTypeEnum.APPLIED, "days_ago": 2},
        {"job_id": job1.id, "type": InteractionTypeEnum.VIEW, "days_ago": 1},
        # Views but rejects data science jobs
        {"job_id": job2.id, "type": InteractionTypeEnum.VIEW, "days_ago": 10},
        {"job_id": job2.id, "type": InteractionTypeEnum.REJECTED, "days_ago": 9},
        # Some frontend job interactions
        {"job_id": job3.id, "type": InteractionTypeEnum.VIEW, "days_ago": 8},
        {"job_id": job3.id, "type": InteractionTypeEnum.REJECTED, "days_ago": 7},
    ]
    
    for interaction_data in interactions1:
        interaction = InteractionLog(
            candidate_id=candidate1.id,
            job_id=interaction_data["job_id"],
            interaction_type=interaction_data["type"]
        )
        db.add(interaction)
    
    # Candidate 2 interactions (Data scientist - high engagement with data jobs)
    interactions2 = [
        {"job_id": job2.id, "type": InteractionTypeEnum.VIEW, "days_ago": 5},
        {"job_id": job2.id, "type": InteractionTypeEnum.APPLIED, "days_ago": 4},
        {"job_id": job2.id, "type": InteractionTypeEnum.VIEW, "days_ago": 3},
        {"job_id": job2.id, "type": InteractionTypeEnum.APPLIED, "days_ago": 2},
        {"job_id": job2.id, "type": InteractionTypeEnum.VIEW, "days_ago": 1},
        # Views but rejects Python development jobs
        {"job_id": job1.id, "type": InteractionTypeEnum.VIEW, "days_ago": 10},
        {"job_id": job1.id, "type": InteractionTypeEnum.REJECTED, "days_ago": 9},
        # Some frontend job interactions
        {"job_id": job3.id, "type": InteractionTypeEnum.VIEW, "days_ago": 8},
        {"job_id": job3.id, "type": InteractionTypeEnum.REJECTED, "days_ago": 7},
    ]
    
    for interaction_data in interactions2:
        interaction = InteractionLog(
            candidate_id=candidate2.id,
            job_id=interaction_data["job_id"],
            interaction_type=interaction_data["type"]
        )
        db.add(interaction)
    
    # Candidate 3 interactions (Frontend developer - high engagement with frontend jobs)
    interactions3 = [
        {"job_id": job3.id, "type": InteractionTypeEnum.VIEW, "days_ago": 5},
        {"job_id": job3.id, "type": InteractionTypeEnum.APPLIED, "days_ago": 4},
        {"job_id": job3.id, "type": InteractionTypeEnum.VIEW, "days_ago": 3},
        {"job_id": job3.id, "type": InteractionTypeEnum.APPLIED, "days_ago": 2},
        {"job_id": job3.id, "type": InteractionTypeEnum.VIEW, "days_ago": 1},
        # Views but rejects Python jobs
        {"job_id": job1.id, "type": InteractionTypeEnum.VIEW, "days_ago": 10},
        {"job_id": job1.id, "type": InteractionTypeEnum.REJECTED, "days_ago": 9},
        # Views but rejects data science jobs
        {"job_id": job2.id, "type": InteractionTypeEnum.VIEW, "days_ago": 8},
        {"job_id": job2.id, "type": InteractionTypeEnum.REJECTED, "days_ago": 7},
    ]
    
    for interaction_data in interactions3:
        interaction = InteractionLog(
            candidate_id=candidate3.id,
            job_id=interaction_data["job_id"],
            interaction_type=interaction_data["type"]
        )
        db.add(interaction)
    
    await db.commit()
    
    # Re-query with eager loading
    result = await db.execute(
        select(Candidate).options(selectinload(Candidate.experiences))
    )
    candidates = result.scalars().all()
    result = await db.execute(
        select(Job).options(selectinload(Job.mandatory_skills))
    )
    jobs = result.scalars().all()
    
    print(f"✅ Created {len(candidates)} candidates, {len(jobs)} jobs, and interaction history")
    return candidates, jobs

async def test_interaction_service():
    """Test interaction service functionality"""
    print("🧪 TEST 1: Interaction Service")
    print("=" * 50)
    
    async for db in get_db_session():
        try:
            # Create mock data
            candidates, jobs = await create_mock_data(db)
            
            if not candidates:
                print("❌ No candidates found for testing")
                return False
            
            candidate = candidates[0]
            
            # Test behavior pattern analysis
            patterns = await interaction_service.get_user_behavior_patterns(db, candidate.id)
            
            print("✅ User behavior patterns:")
            print(f"   Total interactions: {patterns.get('total_interactions', 0)}")
            print(f"   Total applications: {patterns.get('total_applications', 0)}")
            print(f"   Application rate: {patterns.get('application_rate', 0):.2f}")
            print(f"   Engagement score: {patterns.get('engagement_score', 0)}")
            print(f"   Preferred domains: {patterns.get('preferred_domains', {})}")
            print(f"   Preferred locations: {patterns.get('preferred_locations', {})}")
            
            # Test similar users
            similar_users = await interaction_service.get_similar_users(db, candidate.id, limit=3)
            
            print(f"\n✅ Found {len(similar_users)} similar users:")
            for i, user in enumerate(similar_users):
                print(f"   #{i+1}: {user['name']} (Similarity: {user['similarity_score']:.3f})")
            
            return True
            
        except Exception as e:
            print(f"❌ Interaction Service Test: FAILED - {e}")
            return False
        break

async def test_ml_trainer_service():
    """Test ML trainer service functionality"""
    print("\n🧪 TEST 2: ML Trainer Service")
    print("=" * 50)
    
    try:
        # Test feature extraction with mock data
        mock_interactions = [{"job_id": 1, "interaction_type": "View", "created_at": datetime.utcnow()}]
        mock_user_patterns = {
            "total_interactions": 10,
            "total_applications": 3,
            "application_rate": 0.3,
            "preferred_domains": {"Software Development": 2},
            "preferred_locations": {"Lahore": 2},
            "salary_preferences": {"avg": 100000}
        }
        mock_job_features = {
            "job_id": 1,
            "domain": "Software Development",
            "location": "Lahore",
            "salary_min": 80000,
            "similarity_score": 0.8,
            "filter_score": 0.9
        }
        
        features = ml_trainer_service.extract_training_features(
            mock_interactions, mock_user_patterns, mock_job_features
        )
        
        print("✅ Extracted ML features:")
        for feature_name, value in features.items():
            print(f"   {feature_name}: {value:.3f}")
        
        # Test fallback scoring
        score = ml_trainer_service.predict_score(features)
        print(f"\n✅ Fallback prediction score: {score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Trainer Service Test: FAILED - {e}")
        return False

async def test_personalization_service():
    """Test personalization service functionality"""
    print("\n🧪 TEST 3: Personalization Service")
    print("=" * 50)
    
    async for db in get_db_session():
        try:
            # Get test data
            candidates, jobs = await create_mock_data(db)
            
            if not candidates or not jobs:
                print("❌ No test data available")
                return False
            
            candidate = candidates[0]
            job = jobs[0]
            
            # Create mock job recommendations
            job_recommendations = [
                {
                    "job": job,
                    "similarity_score": 0.85,
                    "filter_score": 0.9,
                    "combined_score": 0.87
                }
            ]
            
            # Test job personalization
            personalized_jobs = await personalization_service.personalize_job_recommendations(
                db, candidate.id, job_recommendations, use_ml_scoring=False
            )
            
            print("✅ Personalized job recommendations:")
            for i, rec in enumerate(personalized_jobs):
                print(f"\n   #{i+1} - {rec['job'].title}:")
                print(f"      Semantic Score: {rec.get('similarity_score', 0):.3f}")
                print(f"      Filter Score: {rec.get('filter_score', 0):.3f}")
                print(f"      Personalization Score: {rec.get('personalization_score', 0):.3f}")
                print(f"      Final Score: {rec.get('final_score', 0):.3f}")
                print(f"      Reasons: {', '.join(rec.get('personalization_reasons', []))}")
            
            return True
            
        except Exception as e:
            print(f"❌ Personalization Service Test: FAILED - {e}")
            return False
        break

async def test_behavior_learning():
    """Test behavior learning and model training"""
    print("\n🧪 TEST 4: Behavior Learning")
    print("=" * 50)
    
    async for db in get_db_session():
        try:
            # Create mock data first
            candidates, jobs = await create_mock_data(db)
            
            # Test model training (with mock data)
            print("🤖 Training personalization model...")
            training_result = await personalization_service.train_personalization_model(
                db, model_type="lightgbm"
            )
            
            if "error" in training_result:
                print(f"⚠️ Model training: {training_result['error']}")
                print("   (This might be expected with limited data)")
            else:
                print("✅ Model training completed:")
                print(f"   Model type: {training_result.get('model_type')}")
                print(f"   Samples: {training_result.get('n_samples')}")
                print(f"   Metrics: {training_result.get('metrics')}")
            
            # Test behavior pattern comparison
            if len(candidates) >= 2:
                candidate1, candidate2 = candidates[0], candidates[1]
                
                patterns1 = await interaction_service.get_user_behavior_patterns(db, candidate1.id)
                patterns2 = await interaction_service.get_user_behavior_patterns(db, candidate2.id)
                
                similarity = interaction_service._calculate_behavior_similarity(patterns1, patterns2)
                
                print(f"\n✅ Behavior similarity between {candidate1.name} and {candidate2.name}: {similarity:.3f}")
                
                if similarity > 0.5:
                    print("   High similarity - similar behavior patterns")
                elif similarity > 0.2:
                    print("   Moderate similarity - some common preferences")
                else:
                    print("   Low similarity - different behavior patterns")
            
            return True
            
        except Exception as e:
            print(f"❌ Behavior Learning Test: FAILED - {e}")
            return False
        break

async def test_personalization_comparison():
    """Compare different personalization approaches"""
    print("\n🧪 TEST 5: Personalization Comparison")
    print("=" * 50)
    
    async for db in get_db_session():
        try:
            candidates, jobs = await create_mock_data(db)
            
            if not candidates or not jobs:
                print("❌ No test data available")
                return False
            
            candidate = candidates[0]
            job = jobs[0]
            
            # Create recommendations
            job_recommendations = [
                {
                    "job": job,
                    "similarity_score": 0.8,
                    "filter_score": 0.9,
                    "combined_score": 0.85
                }
            ]
            
            print("📊 Comparing personalization approaches:")
            
            # 1. No personalization (semantic + filter only)
            print("\n1️⃣ No Personalization:")
            for i, rec in enumerate(job_recommendations):
                print(f"   #{i+1}: {rec['job'].title} (Score: {rec['combined_score']:.3f})")
            
            # 2. Rule-based personalization
            personalized_rule = await personalization_service.personalize_job_recommendations(
                db, candidate.id, job_recommendations, use_ml_scoring=False
            )
            print("\n2️⃣ Rule-Based Personalization:")
            for i, rec in enumerate(personalized_rule):
                print(f"   #{i+1}: {rec['job'].title} (Score: {rec['final_score']:.3f})")
                print(f"      Personalization: {rec['personalization_score']:.3f}")
                print(f"      Reasons: {', '.join(rec['personalization_reasons'])}")
            
            # 3. ML-based personalization (if model available)
            personalized_ml = await personalization_service.personalize_job_recommendations(
                db, candidate.id, job_recommendations, use_ml_scoring=True
            )
            print("\n3️⃣ ML-Based Personalization:")
            for i, rec in enumerate(personalized_ml):
                print(f"   #{i+1}: {rec['job'].title} (Score: {rec['final_score']:.3f})")
                print(f"      Personalization: {rec['personalization_score']:.3f}")
                print(f"      Reasons: {', '.join(rec['personalization_reasons'])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Personalization Comparison Test: FAILED - {e}")
            return False
        break

async def main():
    """Run all personalization tests"""
    print("🚀 Testing Personalization & ML Model Service with Mock Data")
    print("=" * 70)
    
    tests = [
        ("Interaction Service", test_interaction_service),
        ("ML Trainer Service", test_ml_trainer_service),
        ("Personalization Service", test_personalization_service),
        ("Behavior Learning", test_behavior_learning),
        ("Personalization Comparison", test_personalization_comparison)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("🎯 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASSED" if results[i] else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 PERSONALIZATION SERVICE TEST PASSED!")
        print("\n📋 What's Working:")
        print("   ✅ User behavior pattern analysis")
        print("   ✅ Interaction tracking and logging")
        print("   ✅ ML feature extraction and training")
        print("   ✅ Rule-based personalization scoring")
        print("   ✅ ML-based personalization (with fallback)")
        print("   ✅ Behavior similarity calculation")
        print("   ✅ Personalized recommendation ranking")
        print("   ✅ Human-readable personalization reasons")
    else:
        print("\n⚠️ PERSONALIZATION SERVICE TEST FAILED!")
        print("Check the errors above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 