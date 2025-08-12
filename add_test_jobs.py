#!/usr/bin/env python3
"""
Add dummy jobs for testing recruiter recommendations
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def add_test_jobs():
    """Add dummy jobs for testing"""
    
    # Database connection
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'job_matcher')}"
    )
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        # Test jobs data
        test_jobs = [
            {
                "title": "Senior React Developer",
                "company": "TechCorp",
                "location": "San Francisco",
                "domain": "Software Development",
                "salary_min": 120000,
                "salary_max": 180000,
                "total_years_required": 5,
                "job_description": "Looking for a senior React developer with 3+ years experience in React, TypeScript, and modern frontend technologies.",
                "mandatory_skills": [
                    {"skill": "React", "min_experience": 3},
                    {"skill": "TypeScript", "min_experience": 2},
                    {"skill": "JavaScript", "min_experience": 4}
                ]
            },
            {
                "title": "Python Data Scientist",
                "company": "DataTech",
                "location": "New York",
                "domain": "Data Science",
                "salary_min": 100000,
                "salary_max": 150000,
                "total_years_required": 4,
                "job_description": "Seeking a Python Data Scientist with experience in machine learning, pandas, and scikit-learn.",
                "mandatory_skills": [
                    {"skill": "Python", "min_experience": 3},
                    {"skill": "Machine Learning", "min_experience": 2},
                    {"skill": "Pandas", "min_experience": 2}
                ]
            },
            {
                "title": "Full Stack Developer",
                "company": "StartupXYZ",
                "location": "Remote",
                "domain": "Software Development",
                "salary_min": 80000,
                "salary_max": 120000,
                "total_years_required": 3,
                "job_description": "Full stack developer needed with experience in both frontend and backend technologies.",
                "mandatory_skills": [
                    {"skill": "JavaScript", "min_experience": 2},
                    {"skill": "Python", "min_experience": 2},
                    {"skill": "SQL", "min_experience": 1}
                ]
            }
        ]
        
        for job_data in test_jobs:
            # Insert job
            job_query = """
            INSERT INTO jobs (title, company, location, domain, salary_min, salary_max, 
                            total_years_required, job_description, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
            RETURNING id
            """
            
            job_id = await conn.fetchval(
                job_query,
                job_data["title"],
                job_data["company"],
                job_data["location"],
                job_data["domain"],
                job_data["salary_min"],
                job_data["salary_max"],
                job_data["total_years_required"],
                job_data["job_description"]
            )
            
            print(f"✅ Added job: {job_data['title']} (ID: {job_id})")
            
            # Add mandatory skills
            for skill_data in job_data["mandatory_skills"]:
                skill_query = """
                INSERT INTO job_mandatory_skills (job_id, skill, min_experience, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                """
                
                await conn.execute(
                    skill_query,
                    job_id,
                    skill_data["skill"],
                    skill_data["min_experience"]
                )
                
                print(f"   - Added skill: {skill_data['skill']} ({skill_data['min_experience']} years)")
        
        print("\n🎉 Successfully added test jobs!")
        print("📋 You can now test the recruiter recommendations with these jobs.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_test_jobs()) 