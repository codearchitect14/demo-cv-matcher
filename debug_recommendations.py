#!/usr/bin/env python3
"""
Debug script to see why recommendations are returning empty lists
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session
from sqlalchemy.future import select
from models.job import Job, JobMandatorySkill
from models.candidate import Candidate, CandidateExperience
from recommender.semantic import semantic_search_service
from recommender.filters import filtering_service

async def debug_recommendations():
    """Debug the recommendation process"""
    async for db in get_db_session():
        try:
            print("🔍 Debugging recommendation process...")
            
            # 1. Check what data we have
            print("\n1. Checking database data...")
            
            jobs_result = await db.execute(select(Job))
            jobs = jobs_result.scalars().all()
            print(f"Jobs: {len(jobs)}")
            for job in jobs:
                print(f"  - ID: {job.id}, Title: {job.title}, Domain: {job.domain}")
            
            candidates_result = await db.execute(select(Candidate))
            candidates = candidates_result.scalars().all()
            print(f"Candidates: {len(candidates)}")
            for candidate in candidates:
                print(f"  - ID: {candidate.id}, Name: {candidate.name}, Domain: {candidate.domain}")
            
            # 2. Test semantic search directly
            print("\n2. Testing semantic search...")
            
            # Test job search for candidate 2
            candidate_2 = await db.execute(select(Candidate).where(Candidate.id == 2))
            candidate_2 = candidate_2.scalar_one_or_none()
            
            if candidate_2:
                print(f"Testing job recommendations for candidate: {candidate_2.name}")
                
                # Get semantic search results
                semantic_results = await semantic_search_service.find_similar_jobs(
                    candidate_2.id, db, k=5, apply_filters=False, strict_mode=False, use_ml_ranking=False
                )
                print(f"Semantic search results: {len(semantic_results)}")
                
                if semantic_results:
                    print("First semantic result:")
                    first_result = semantic_results[0]
                    print(f"  - Job ID: {first_result.get('job_id')}")
                    print(f"  - Similarity Score: {first_result.get('similarity_score')}")
                    print(f"  - Explanation: {first_result.get('explanation')}")
                else:
                    print("❌ No semantic search results!")
            
            # 3. Test filtering
            print("\n3. Testing filtering...")
            
            if semantic_results:
                # Test filtering
                filtered_results = await filtering_service.filter_jobs_for_candidate(
                    semantic_results, candidate_2, db, strict_mode=False
                )
                print(f"Filtered results: {len(filtered_results)}")
                
                if filtered_results:
                    print("First filtered result:")
                    first_filtered = filtered_results[0]
                    print(f"  - Job ID: {first_filtered.get('job_id')}")
                    print(f"  - Filter Score: {first_filtered.get('filter_score')}")
                    if 'validation' in first_filtered:
                        validation = first_filtered['validation']
                        print(f"  - Is Valid: {validation.get('is_valid')}")
                        print(f"  - Reasons: {validation.get('reasons')}")
                else:
                    print("❌ All results filtered out!")
                    
                    # Debug why filtering failed
                    if semantic_results:
                        first_result = semantic_results[0]
                        job = first_result.get('job')
                        if job:
                            print(f"\nDebugging filter for job: {job.title}")
                            validation = await filtering_service._validate_job_for_candidate(
                                job, candidate_2, db, strict_mode=False
                            )
                            print(f"Validation result: {validation}")
            
            # 4. Test with strict_mode=False
            print("\n4. Testing with strict_mode=False...")
            
            if semantic_results:
                # Test with very loose filtering
                loose_results = await filtering_service.filter_jobs_for_candidate(
                    semantic_results, candidate_2, db, strict_mode=False
                )
                print(f"Loose filtering results: {len(loose_results)}")
                
                if loose_results:
                    print("✅ Loose filtering works!")
                else:
                    print("❌ Even loose filtering removes all results")
            
        except Exception as e:
            print(f"❌ Error debugging: {e}")
            import traceback
            traceback.print_exc()

async def test_simple_recommendation():
    """Test a simple recommendation without complex filtering"""
    async for db in get_db_session():
        try:
            print("\n🧪 Testing simple recommendation...")
            
            # Get candidate 2
            candidate_result = await db.execute(select(Candidate).where(Candidate.id == 2))
            candidate = candidate_result.scalar_one_or_none()
            
            if not candidate:
                print("❌ Candidate 2 not found")
                return
            
            # Get all jobs
            jobs_result = await db.execute(select(Job))
            jobs = jobs_result.scalars().all()
            
            if not jobs:
                print("❌ No jobs found")
                return
            
            print(f"Testing recommendations for candidate: {candidate.name}")
            print(f"Available jobs: {len(jobs)}")
            
            # Simple matching based on domain
            matches = []
            for job in jobs:
                if candidate.domain and job.domain:
                    if candidate.domain.lower() == job.domain.lower():
                        matches.append({
                            'job_id': job.id,
                            'title': job.title,
                            'company': job.company,
                            'domain': job.domain,
                            'match_type': 'exact_domain'
                        })
                    elif 'software' in candidate.domain.lower() and 'software' in job.domain.lower():
                        matches.append({
                            'job_id': job.id,
                            'title': job.title,
                            'company': job.company,
                            'domain': job.domain,
                            'match_type': 'partial_domain'
                        })
            
            print(f"Simple matches found: {len(matches)}")
            for match in matches:
                print(f"  - {match['title']} ({match['company']}) - {match['match_type']}")
            
        except Exception as e:
            print(f"❌ Error in simple test: {e}")

async def main():
    """Main function"""
    print("🚀 Debugging CV Matcher Recommendations...")
    
    # Debug the recommendation process
    await debug_recommendations()
    
    # Test simple recommendation
    await test_simple_recommendation()
    
    print("\n📋 Summary:")
    print("Check the output above to see where the filtering is failing")

if __name__ == "__main__":
    asyncio.run(main()) 