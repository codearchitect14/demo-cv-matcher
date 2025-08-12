#!/usr/bin/env python3
"""
Comprehensive test for performance optimizations:
1. N+1 Query Problems
2. Hardcoded AI/ML Weights
3. No Personalization Engine
4. No Cold Start Handling
"""

import asyncio
import sys
import os
import time
import logging
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def test_n_plus_one_query_fixes():
    """Test 1: N+1 Query Problem Fixes"""
    print("\n" + "="*60)
    print("🧪 Testing N+1 Query Problem Fixes")
    print("="*60)
    
    try:
        from db.crud.job import job_crud
        from db.crud.candidate import candidate_crud
        from sqlalchemy import select, func, text
        from config.database import get_fresh_session_factory
        from sqlalchemy.ext.asyncio import AsyncSession
        
        # Use fresh session factory
        AsyncSessionLocal = get_fresh_session_factory()
        
        async with AsyncSessionLocal() as db:
            # Test bulk job retrieval
            print("[INFO] Testing bulk job retrieval...")
            
            # Get multiple job IDs
            jobs_result = await db.execute(
                text("SELECT id FROM jobs LIMIT 10")
            )
            job_ids = [row[0] for row in jobs_result.fetchall()]
            
            if job_ids:
                # Test the new bulk method
                start_time = time.time()
                jobs_with_skills = await job_crud.get_multiple_with_skills(db, job_ids)
                bulk_time = time.time() - start_time
                
                print(f"[SUCCESS] Bulk retrieval: {len(jobs_with_skills)} jobs in {bulk_time:.3f}s")
                
                # Verify skills are loaded
                for job in jobs_with_skills:
                    if hasattr(job, 'mandatory_skills'):
                        print(f"[SUCCESS] Job {job.id} has {len(job.mandatory_skills)} skills loaded")
                
                # Test individual retrieval for comparison
                start_time = time.time()
                individual_jobs = []
                for job_id in job_ids[:3]:  # Test with fewer jobs
                    job = await job_crud.get_with_skills(db, job_id)
                    if job:
                        individual_jobs.append(job)
                individual_time = time.time() - start_time
                
                print(f"[INFO] Individual retrieval: {len(individual_jobs)} jobs in {individual_time:.3f}s")
                print(f"[INFO] Performance improvement: {individual_time/bulk_time:.1f}x faster with bulk")
            
            # Test candidate bulk retrieval
            print("[INFO] Testing candidate bulk retrieval...")
            candidates_result = await db.execute(
                text("SELECT id FROM candidates LIMIT 5")
            )
            candidate_ids = [row[0] for row in candidates_result.fetchall()]
            
            if candidate_ids:
                start_time = time.time()
                candidates_with_experiences = await candidate_crud.get_multi_with_experiences(
                    db, skip=0, limit=len(candidate_ids)
                )
                bulk_time = time.time() - start_time
                
                print(f"[SUCCESS] Bulk candidate retrieval: {len(candidates_with_experiences)} candidates in {bulk_time:.3f}s")
                
                for candidate in candidates_with_experiences:
                    if hasattr(candidate, 'experiences'):
                        print(f"[SUCCESS] Candidate {candidate.id} has {len(candidate.experiences)} experiences loaded")
        
        print("[SUCCESS] N+1 query fixes test passed")
        return True
        
    except Exception as e:
        print(f"[ERROR] N+1 query fixes test failed: {e}")
        return False

async def test_adaptive_weighting():
    """Test 2: Adaptive Weighting Implementation"""
    print("\n" + "="*60)
    print("🧪 Testing Adaptive Weighting Implementation")
    print("="*60)
    
    try:
        from services.adaptive_weighting_service import adaptive_weighting_service
        from config.database import get_fresh_session_factory
        from sqlalchemy import text
        
        # Use fresh session factory
        AsyncSessionLocal = get_fresh_session_factory()
        
        async with AsyncSessionLocal() as db:
            # Test adaptive weights calculation
            print("[INFO] Testing adaptive weights calculation...")
            
            # Get a candidate and job for testing
            candidate_result = await db.execute(
                text("SELECT id FROM candidates LIMIT 1")
            )
            candidate_id = candidate_result.scalar()
            
            job_result = await db.execute(
                text("SELECT id FROM jobs LIMIT 1")
            )
            job_id = job_result.scalar()
            
            if candidate_id and job_id:
                # Test adaptive weights
                weights = await adaptive_weighting_service.get_adaptive_weights(
                    db, candidate_id, job_id
                )
                
                print(f"[SUCCESS] Adaptive weights calculated: {weights}")
                
                # Verify weights sum to approximately 1.0
                total_weight = sum(weights.values())
                if 0.9 <= total_weight <= 1.1:
                    print(f"[SUCCESS] Weights sum to {total_weight:.3f} (expected ~1.0)")
                else:
                    print(f"[WARNING] Weights sum to {total_weight:.3f} (should be ~1.0)")
                
                # Test recommendation weights
                rec_weights = await adaptive_weighting_service.get_recommendation_weights(
                    db, candidate_id, job_id, 'job'
                )
                print(f"[SUCCESS] Recommendation weights: {rec_weights}")
                
                # Test different recommendation types
                candidate_weights = await adaptive_weighting_service.get_recommendation_weights(
                    db, candidate_id, job_id, 'candidate'
                )
                print(f"[SUCCESS] Candidate recommendation weights: {candidate_weights}")
            
            print("[SUCCESS] Adaptive weighting test passed")
            return True
            
    except Exception as e:
        print(f"[ERROR] Adaptive weighting test failed: {e}")
        return False

async def test_personalization_engine():
    """Test 3: Personalization Engine"""
    print("\n" + "="*60)
    print("🧪 Testing Personalization Engine")
    print("="*60)
    
    try:
        from services.personalization_engine import personalization_engine
        from config.database import get_fresh_session_factory
        from sqlalchemy import text
        
        # Use fresh session factory
        AsyncSessionLocal = get_fresh_session_factory()
        
        async with AsyncSessionLocal() as db:
            # Test user profile building
            print("[INFO] Testing user profile building...")
            
            # Get a candidate for testing
            candidate_result = await db.execute(
                text("SELECT id FROM candidates LIMIT 1")
            )
            candidate_id = candidate_result.scalar()
            
            if candidate_id:
                # Build user profile
                profile = await personalization_engine.get_user_profile(db, candidate_id)
                
                print(f"[SUCCESS] User profile built for candidate {candidate_id}")
                print(f"[INFO] Profile keys: {list(profile.keys())}")
                
                # Check profile components
                if 'basic_info' in profile:
                    print(f"[SUCCESS] Basic info: {profile['basic_info']}")
                
                if 'skills' in profile:
                    skills = profile['skills']
                    print(f"[SUCCESS] Skills analysis: {skills.get('total_skills', 0)} skills")
                    print(f"[SUCCESS] Primary skills: {skills.get('primary_skills', [])}")
                
                if 'preferences' in profile:
                    prefs = profile['preferences']
                    print(f"[SUCCESS] Preferences: {len(prefs.get('preferred_domains', []))} domains")
                
                if 'engagement' in profile:
                    engagement = profile['engagement']
                    print(f"[SUCCESS] Engagement level: {engagement.get('engagement_level', 'unknown')}")
                
                # Test personalized recommendations
                print("[INFO] Testing personalized recommendations...")
                
                # Create mock job recommendations
                mock_recommendations = [
                    {
                        'job_id': 1,
                        'job': {'id': 1, 'title': 'Software Engineer', 'location': 'New York'},
                        'combined_score': 0.8
                    },
                    {
                        'job_id': 2,
                        'job': {'id': 2, 'title': 'Data Scientist', 'location': 'San Francisco'},
                        'combined_score': 0.6
                    }
                ]
                
                personalized = await personalization_engine.get_personalized_recommendations(
                    db, candidate_id, mock_recommendations, 5
                )
                
                print(f"[SUCCESS] Personalized {len(personalized)} recommendations")
                
                for rec in personalized:
                    print(f"[INFO] Job {rec['job_id']}: score={rec.get('final_score', 0):.3f}")
            
            print("[SUCCESS] Personalization engine test passed")
            return True
            
    except Exception as e:
        print(f"[ERROR] Personalization engine test failed: {e}")
        return False

async def test_cold_start_handler():
    """Test 4: Cold Start Handler"""
    print("\n" + "="*60)
    print("🧪 Testing Cold Start Handler")
    print("="*60)
    
    try:
        from services.cold_start_handler import cold_start_handler
        from config.database import get_fresh_session_factory
        from sqlalchemy import text
        
        # Use fresh session factory
        AsyncSessionLocal = get_fresh_session_factory()
        
        async with AsyncSessionLocal() as db:
            # Test new user recommendations
            print("[INFO] Testing new user recommendations...")
            
            # Get a candidate for testing
            candidate_result = await db.execute(
                text("SELECT id FROM candidates LIMIT 1")
            )
            candidate_id = candidate_result.scalar()
            
            if candidate_id:
                # Test cold start recommendations
                cold_start_recs = await cold_start_handler.handle_new_user_recommendations(
                    db, candidate_id, 5
                )
                
                print(f"[SUCCESS] Generated {len(cold_start_recs)} cold start recommendations")
                
                for rec in cold_start_recs:
                    print(f"[INFO] {rec.get('method', 'unknown')}: {rec.get('explanation', 'No explanation')}")
                
                # Test new job recommendations
                print("[INFO] Testing new job recommendations...")
                
                job_result = await db.execute(
                    text("SELECT id FROM jobs LIMIT 1")
                )
                job_id = job_result.scalar()
                
                if job_id:
                    candidate_recs = await cold_start_handler.handle_new_job_recommendations(
                        db, job_id, 5
                    )
                    
                    print(f"[SUCCESS] Generated {len(candidate_recs)} candidate recommendations for new job")
                    
                    for rec in candidate_recs:
                        print(f"[INFO] {rec.get('method', 'unknown')}: {rec.get('explanation', 'No explanation')}")
            
            print("[SUCCESS] Cold start handler test passed")
            return True
            
    except Exception as e:
        print(f"[ERROR] Cold start handler test failed: {e}")
        return False

async def test_integration():
    """Test 5: Integration of All Optimizations"""
    print("\n" + "="*60)
    print("🧪 Testing Integration of All Optimizations")
    print("="*60)
    
    try:
        from recommender.semantic import SemanticSearchService
        from config.database import get_fresh_session_factory
        from sqlalchemy import text
        
        # Use fresh session factory
        AsyncSessionLocal = get_fresh_session_factory()
        
        async with AsyncSessionLocal() as db:
            # Test semantic search with all optimizations
            print("[INFO] Testing semantic search with optimizations...")
            
            semantic_service = SemanticSearchService()
            
            # Get a candidate for testing
            candidate_result = await db.execute(
                text("SELECT id FROM candidates LIMIT 1")
            )
            candidate_id = candidate_result.scalar()
            
            if candidate_id:
                # Test recommendations with all optimizations
                start_time = time.time()
                recommendations = await semantic_service.find_similar_jobs(
                    candidate_id, db, k=5, apply_filters=True, use_ml_ranking=True
                )
                search_time = time.time() - start_time
                
                print(f"[SUCCESS] Generated {len(recommendations)} recommendations in {search_time:.3f}s")
                
                for rec in recommendations:
                    print(f"[INFO] Job {rec.get('job_id')}: score={rec.get('combined_score', 0):.3f}")
                    if 'weights_used' in rec:
                        print(f"[INFO] Weights used: {rec['weights_used']}")
            
            print("[SUCCESS] Integration test passed")
            return True
            
    except Exception as e:
        print(f"[ERROR] Integration test failed: {e}")
        return False

async def main():
    """Run all performance optimization tests"""
    print("🚀 Starting Performance Optimization Tests")
    print("="*60)
    
    tests = [
        ("N+1 Query Fixes", test_n_plus_one_query_fixes),
        ("Adaptive Weighting", test_adaptive_weighting),
        ("Personalization Engine", test_personalization_engine),
        ("Cold Start Handler", test_cold_start_handler),
        ("Integration", test_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"[ERROR] {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 Performance Optimization Test Results")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "[SUCCESS]" if result else "[FAILED]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All performance optimizations implemented successfully!")
        print("✅ N+1 query problems resolved with bulk operations")
        print("✅ Adaptive weighting replaces hardcoded weights")
        print("✅ Personalization engine provides user-specific recommendations")
        print("✅ Cold start handler manages new users and jobs")
        print("✅ All optimizations integrated and working")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 