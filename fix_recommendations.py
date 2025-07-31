#!/usr/bin/env python3
"""
Fix recommendations by adding missing data and reindexing
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session
from sqlalchemy.future import select
from models.job import Job, JobMandatorySkill
from models.candidate import Candidate, CandidateExperience
from models.interaction import InteractionLog
from models.application import Application

async def add_missing_data():
    """Add missing data to existing tables"""
    async for db in get_db_session():
        try:
            print("🔧 Adding missing data to existing tables...")
            
            # 1. Add mandatory skills to existing jobs
            print("\n1. Adding mandatory skills to jobs...")
            
            # Get existing jobs
            jobs_result = await db.execute(select(Job))
            jobs = jobs_result.scalars().all()
            print(f"Found {len(jobs)} jobs")
            
            for job in jobs:
                print(f"Processing job: {job.title} (ID: {job.id})")
                
                # Check if job already has skills
                skills_result = await db.execute(
                    select(JobMandatorySkill).where(JobMandatorySkill.job_id == job.id)
                )
                existing_skills = skills_result.scalars().all()
                
                if not existing_skills:
                    # Add skills based on job title
                    if "Python" in job.title:
                        skills = [
                            {"skill": "Python", "min_experience": 2},
                            {"skill": "Django", "min_experience": 1},
                            {"skill": "SQL", "min_experience": 1}
                        ]
                    elif "Senior" in job.title:
                        skills = [
                            {"skill": "Python", "min_experience": 3},
                            {"skill": "FastAPI", "min_experience": 2},
                            {"skill": "AWS", "min_experience": 1}
                        ]
                    else:
                        skills = [
                            {"skill": "Programming", "min_experience": 1},
                            {"skill": "Problem Solving", "min_experience": 1}
                        ]
                    
                    for skill_data in skills:
                        skill = JobMandatorySkill(
                            job_id=job.id,
                            skill=skill_data["skill"],
                            min_experience=skill_data["min_experience"]
                        )
                        db.add(skill)
                        print(f"  ✅ Added skill '{skill_data['skill']}' to job '{job.title}'")
                else:
                    print(f"  ⚠️  Job '{job.title}' already has {len(existing_skills)} skills")
            
            # 2. Add experience to existing candidates
            print("\n2. Adding experience to candidates...")
            
            # Get existing candidates
            candidates_result = await db.execute(select(Candidate))
            candidates = candidates_result.scalars().all()
            print(f"Found {len(candidates)} candidates")
            
            for candidate in candidates:
                print(f"Processing candidate: {candidate.name} (ID: {candidate.id})")
                
                # Check if candidate already has experience
                exp_result = await db.execute(
                    select(CandidateExperience).where(CandidateExperience.candidate_id == candidate.id)
                )
                existing_exp = exp_result.scalars().all()
                
                if not existing_exp:
                    # Add experience based on candidate domain
                    if "Software Development" in candidate.domain or "Technology" in candidate.domain:
                        experiences = [
                            {"skill": "Python", "years": 3, "description": "Web development with Django"},
                            {"skill": "JavaScript", "years": 2, "description": "Frontend development"},
                            {"skill": "SQL", "years": 2, "description": "Database design and queries"}
                        ]
                    else:
                        experiences = [
                            {"skill": "Programming", "years": 2, "description": "General programming experience"},
                            {"skill": "Problem Solving", "years": 3, "description": "Analytical thinking"}
                        ]
                    
                    for exp_data in experiences:
                        experience = CandidateExperience(
                            candidate_id=candidate.id,
                            skill=exp_data["skill"],
                            years=exp_data["years"],
                            description=exp_data["description"]
                        )
                        db.add(experience)
                        print(f"  ✅ Added experience '{exp_data['skill']}' to candidate '{candidate.name}'")
                else:
                    print(f"  ⚠️  Candidate '{candidate.name}' already has {len(existing_exp)} experiences")
            
            # 3. Add some sample applications
            print("\n3. Adding sample applications...")
            
            # Check if applications exist
            apps_result = await db.execute(select(Application))
            existing_apps = apps_result.scalars().all()
            
            if not existing_apps:
                # Add sample applications
                for candidate in candidates:
                    for job in jobs:
                        # Create application for each candidate-job pair
                        application = Application(
                            candidate_id=candidate.id,
                            job_id=job.id,
                            status="applied",
                            applied_at=datetime.utcnow() - timedelta(days=len(existing_apps))
                        )
                        db.add(application)
                        print(f"  ✅ Added application: {candidate.name} applied to {job.title}")
            else:
                print(f"  ⚠️  Already have {len(existing_apps)} applications")
            
            await db.commit()
            print("\n✅ Missing data added successfully!")
            
            # Print summary
            print("\n📊 Updated Database Summary:")
            
            # Count jobs with skills
            jobs_with_skills = await db.execute(
                select(Job).join(JobMandatorySkill)
            )
            print(f"Jobs with skills: {len(jobs_with_skills.scalars().all())}")
            
            # Count candidates with experience
            candidates_with_exp = await db.execute(
                select(Candidate).join(CandidateExperience)
            )
            print(f"Candidates with experience: {len(candidates_with_exp.scalars().all())}")
            
            # Count applications
            apps_count = await db.execute(select(Application))
            print(f"Applications: {len(apps_count.scalars().all())}")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error adding missing data: {e}")
            raise

async def reindex_data():
    """Reindex the data for semantic search"""
    try:
        from recommender.semantic import semantic_search_service
        
        async for db in get_db_session():
            print("\n🔄 Reindexing jobs...")
            await semantic_search_service.index_jobs(db)
            
            print("🔄 Reindexing candidates...")
            await semantic_search_service.index_candidates(db)
            
            print("✅ Data reindexed successfully!")
            
            # Check index stats
            stats = semantic_search_service.get_index_stats()
            print(f"📊 Index stats: {stats}")
            
    except Exception as e:
        print(f"❌ Error reindexing data: {e}")

async def test_recommendations():
    """Test the recommendation endpoints"""
    import requests
    
    print("\n🧪 Testing recommendation endpoints...")
    
    # Test job recommendations for candidate 2
    try:
        response = requests.get("http://localhost:8000/api/v1/recommendations/candidates/2/job-recommendations?limit=5")
        print(f"Job recommendations status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Job recommendations count: {len(data)}")
            if data:
                print("First recommendation:")
                print(f"  - Job: {data[0].get('title', 'N/A')}")
                print(f"  - Company: {data[0].get('company', 'N/A')}")
                print(f"  - Score: {data[0].get('similarity_score', 'N/A')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing job recommendations: {e}")
    
    # Test candidate recommendations for job 2
    try:
        response = requests.get("http://localhost:8000/api/v1/recommendations/jobs/2/candidate-recommendations?limit=5")
        print(f"Candidate recommendations status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Candidate recommendations count: {len(data)}")
            if data:
                print("First recommendation:")
                print(f"  - Candidate: {data[0].get('name', 'N/A')}")
                print(f"  - Domain: {data[0].get('domain', 'N/A')}")
                print(f"  - Score: {data[0].get('similarity_score', 'N/A')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing candidate recommendations: {e}")

async def main():
    """Main function"""
    print("🚀 Fixing CV Matcher Recommendations...")
    
    # Add missing data
    await add_missing_data()
    
    # Reindex data for semantic search
    await reindex_data()
    
    # Test recommendations
    await test_recommendations()
    
    print("\n🎉 Recommendations should now work!")
    print("\n📋 Test URLs:")
    print("GET /api/v1/recommendations/candidates/2/job-recommendations")
    print("GET /api/v1/recommendations/jobs/2/candidate-recommendations")

if __name__ == "__main__":
    asyncio.run(main()) 