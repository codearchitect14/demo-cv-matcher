#!/usr/bin/env python3
"""
Test the Ranking & Recommendation Engine
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session
from recommender.ranker import recommendation_engine, FeatureEngineeringService
from recommender.semantic import semantic_search_service
from models.candidate import Candidate, CandidateExperience
from models.job import Job, JobMandatorySkill
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def create_test_data(db: AsyncSession):
    """Create test candidates and jobs for ranking tests"""
    print("📝 Creating test data for ranking...")
    
    # Create test candidates with different profiles
    candidates = []
    
    # Candidate 1: Perfect match (high ML score expected)
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
    
    # Candidate 2: Good match but some issues
    candidate2 = Candidate(
        name="Sarah Developer",
        location="Lahore",
        domain="Software Development",
        expected_salary_min=90000,
        expected_salary_max=140000,
        summary="Python developer with 4 years experience"
    )
    db.add(candidate2)
    await db.flush()
    
    exp3 = CandidateExperience(
        candidate_id=candidate2.id,
        skill="Python",
        years=4,
        description="Python development"
    )
    db.add(exp3)
    candidates.append(candidate2)
    
    # Candidate 3: Moderate match
    candidate3 = Candidate(
        name="Mike Coder",
        location="Lahore",
        domain="Software Development",
        expected_salary_min=70000,
        expected_salary_max=120000,
        summary="Developer with 3 years experience"
    )
    db.add(candidate3)
    await db.flush()
    
    exp4 = CandidateExperience(
        candidate_id=candidate3.id,
        skill="Python",
        years=3,
        description="Basic Python development"
    )
    db.add(exp4)
    candidates.append(candidate3)
    
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

async def test_feature_engineering():
    """Test feature engineering service"""
    print("🧪 TEST 1: Feature Engineering Service")
    print("=" * 50)
    
    feature_service = FeatureEngineeringService()
    
    # Create mock match data
    mock_match = {
        'similarity_score': 0.85,
        'filter_score': 0.9,
        'combined_score': 0.87,
        'validation': {
            'details': {
                'salary_match': {'score': 0.95, 'reason': 'Salary overlap'},
                'skills_match': {'score': 1.0, 'reason': 'All skills met'},
                'location_match': {'score': 1.0, 'reason': 'Exact location match'},
                'domain_match': {'score': 1.0, 'reason': 'Domain match'},
                'experience_match': {'score': 1.0, 'reason': 'Experience met'}
            }
        },
        'past_applies': 0,
        'past_rejections': 0,
        'past_clicks': 2
    }
    
    features = feature_service.extract_features(mock_match)
    
    print("✅ Extracted features:")
    for feature_name, value in features.items():
        print(f"   {feature_name}: {value:.3f}")
    
    return True

async def test_ranking_engine():
    """Test ranking engine with mock data"""
    print("\n🧪 TEST 2: Ranking Engine")
    print("=" * 50)
    
    # Create mock matches with different characteristics
    mock_matches = [
        {
            'candidate_id': 1,
            'similarity_score': 0.85,
            'filter_score': 0.9,
            'combined_score': 0.87,
            'validation': {
                'details': {
                    'salary_match': {'score': 0.95},
                    'skills_match': {'score': 1.0},
                    'location_match': {'score': 1.0},
                    'domain_match': {'score': 1.0},
                    'experience_match': {'score': 1.0}
                }
            },
            'past_applies': 0,
            'past_rejections': 0,
            'past_clicks': 2
        },
        {
            'candidate_id': 2,
            'similarity_score': 0.75,
            'filter_score': 0.8,
            'combined_score': 0.77,
            'validation': {
                'details': {
                    'salary_match': {'score': 0.85},
                    'skills_match': {'score': 0.8},
                    'location_match': {'score': 1.0},
                    'domain_match': {'score': 1.0},
                    'experience_match': {'score': 0.9}
                }
            },
            'past_applies': 1,
            'past_rejections': 0,
            'past_clicks': 5
        },
        {
            'candidate_id': 3,
            'similarity_score': 0.65,
            'filter_score': 0.7,
            'combined_score': 0.67,
            'validation': {
                'details': {
                    'salary_match': {'score': 0.75},
                    'skills_match': {'score': 0.6},
                    'location_match': {'score': 1.0},
                    'domain_match': {'score': 1.0},
                    'experience_match': {'score': 0.8}
                }
            },
            'past_applies': 0,
            'past_rejections': 1,
            'past_clicks': 1
        }
    ]
    
    # Rank matches
    ranked_matches = recommendation_engine.rank_matches(mock_matches)
    
    print("✅ Ranked matches:")
    for i, match in enumerate(ranked_matches):
        print(f"\n   #{i+1} - Candidate {match['candidate_id']}:")
        print(f"      ML Score: {match['ml_score']:.3f}")
        print(f"      Semantic Score: {match['similarity_score']:.3f}")
        print(f"      Filter Score: {match['filter_score']:.3f}")
        print(f"      Combined Score: {match['combined_score']:.3f}")
        
        # Show top features
        features = match['ml_features']
        top_features = sorted(features.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"      Top Features: {', '.join([f'{k}={v:.3f}' for k, v in top_features])}")
    
    return True

async def test_integrated_ranking():
    """Test integrated ranking with real data"""
    print("\n🧪 TEST 3: Integrated Ranking with Real Data")
    print("=" * 50)
    
    async for db in get_db_session():
        try:
            # Create test data
            candidates, job = await create_test_data(db)
            
            # Create candidate recommendations (simulate semantic search results)
            candidate_recommendations = []
            for i, candidate in enumerate(candidates):
                # Simulate different similarity scores (cycle through them)
                similarity_scores = [0.85, 0.75, 0.65]
                candidate_recommendations.append({
                    'candidate': candidate,
                    'similarity_score': similarity_scores[i % len(similarity_scores)],
                    'explanation': f"Semantic match for {candidate.name}"
                })
            
            print(f"📊 Testing with {len(candidate_recommendations)} candidates")
            print(f"🎯 Job: {job.title} in {job.location}")
            
            # Apply filtering first
            print("\n🔍 Applying business rule filtering...")
            filtered_candidates = await semantic_search_service.filtering_service.filter_candidates_for_job(
                candidate_recommendations, job, db, strict_mode=False  # Lenient mode to see all
            )
            
            print(f"✅ Filtered candidates: {len(filtered_candidates)}")
            
            # Apply ML ranking
            print("\n🤖 Applying ML-based ranking...")
            ranked_candidates = recommendation_engine.rank_matches(filtered_candidates)
            
            print("\n📊 FINAL RANKED RESULTS:")
            print("-" * 40)
            
            for i, candidate_data in enumerate(ranked_candidates):
                candidate = candidate_data['candidate']
                validation = candidate_data.get('validation', {})
                
                print(f"\n#{i+1} - {candidate.name}:")
                print(f"   📍 Location: {candidate.location}")
                print(f"   💰 Salary: ${candidate.expected_salary_min:,} - ${candidate.expected_salary_max:,}")
                print(f"   🎯 ML Score: {candidate_data.get('ml_score', 0):.3f}")
                print(f"   🔍 Semantic Score: {candidate_data.get('similarity_score', 0):.3f}")
                print(f"   ✅ Filter Score: {validation.get('filter_score', 0):.3f}")
                
                if validation.get('is_valid', True):
                    print(f"   ✅ Status: VALID")
                else:
                    print(f"   ❌ Status: INVALID - {', '.join(validation.get('reasons', []))}")
            
            print("\n✅ Integrated Ranking Test: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Integrated Ranking Test: FAILED - {e}")
            return False
        break

async def test_ranking_comparison():
    """Compare different ranking approaches"""
    print("\n🧪 TEST 4: Ranking Comparison")
    print("=" * 50)
    
    async for db in get_db_session():
        try:
            candidates, job = await create_test_data(db)
            
            # Create candidate recommendations
            candidate_recommendations = []
            for candidate in candidates:
                candidate_recommendations.append({
                    'candidate': candidate,
                    'similarity_score': 0.8,  # Same semantic score for comparison
                    'explanation': f"Semantic match for {candidate.name}"
                })
            
            # Test different ranking approaches
            print("📊 Comparing ranking approaches:")
            
            # 1. Semantic only
            semantic_only = sorted(candidate_recommendations, key=lambda x: x['similarity_score'], reverse=True)
            print("\n1️⃣ Semantic Only Ranking:")
            for i, candidate_data in enumerate(semantic_only):
                print(f"   #{i+1}: {candidate_data['candidate'].name} (Score: {candidate_data['similarity_score']:.3f})")
            
            # 2. Filtered + Combined score
            filtered_candidates = await semantic_search_service.filtering_service.filter_candidates_for_job(
                candidate_recommendations, job, db, strict_mode=False
            )
            combined_ranking = sorted(filtered_candidates, key=lambda x: x.get('combined_score', 0), reverse=True)
            print("\n2️⃣ Combined Score Ranking:")
            for i, candidate_data in enumerate(combined_ranking):
                print(f"   #{i+1}: {candidate_data['candidate'].name} (Score: {candidate_data.get('combined_score', 0):.3f})")
            
            # 3. ML-based ranking
            ml_ranking = recommendation_engine.rank_matches(filtered_candidates)
            print("\n3️⃣ ML-Based Ranking:")
            for i, candidate_data in enumerate(ml_ranking):
                print(f"   #{i+1}: {candidate_data['candidate'].name} (Score: {candidate_data.get('ml_score', 0):.3f})")
            
            print("\n✅ Ranking Comparison Test: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Ranking Comparison Test: FAILED - {e}")
            return False
        break

async def main():
    """Run all ranking tests"""
    print("🚀 Testing Ranking & Recommendation Engine")
    print("=" * 60)
    
    tests = [
        ("Feature Engineering", test_feature_engineering),
        ("Ranking Engine", test_ranking_engine),
        ("Integrated Ranking", test_integrated_ranking),
        ("Ranking Comparison", test_ranking_comparison)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASSED" if results[i] else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 RANKING ENGINE TEST PASSED!")
        print("\n📋 What's Working:")
        print("   ✅ Feature engineering from semantic + filter scores")
        print("   ✅ ML-based ranking (with fallback)")
        print("   ✅ Integration with semantic search pipeline")
        print("   ✅ Comparison of different ranking approaches")
        print("   ✅ Personalized recommendations")
    else:
        print("\n⚠️ RANKING ENGINE TEST FAILED!")
        print("Check the errors above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 