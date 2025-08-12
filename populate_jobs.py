#!/usr/bin/env python3
"""
Script to populate the database with sample job data
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import AsyncSessionLocal
from models.job import Job
from sqlalchemy import text

# Sample job data
SAMPLE_JOBS = [
    {
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "location": "New York, NY",
        "salary_min": 80000,
        "salary_max": 120000,
        "domain": "Software Development",
        "total_years_required": 5,
        "job_description": "We are looking for a Senior Python Developer to join our team. You will be responsible for developing high-quality software solutions and mentoring junior developers."
    },
    {
        "title": "AI Software Engineer",
        "company": "Turing Labs",
        "location": "San Francisco, CA",
        "salary_min": 90000,
        "salary_max": 140000,
        "domain": "Artificial Intelligence",
        "total_years_required": 3,
        "job_description": "Join our AI team to develop cutting-edge machine learning models and AI applications. Experience with TensorFlow and PyTorch required."
    },
    {
        "title": "Full Stack Developer",
        "company": "WebSolutions",
        "location": "Austin, TX",
        "salary_min": 70000,
        "salary_max": 110000,
        "domain": "Web Development",
        "total_years_required": 4,
        "job_description": "We need a Full Stack Developer proficient in React, Node.js, and Python. You'll be building scalable web applications."
    },
    {
        "title": "Data Scientist",
        "company": "DataCorp",
        "location": "Boston, MA",
        "salary_min": 85000,
        "salary_max": 130000,
        "domain": "Data Science",
        "total_years_required": 3,
        "job_description": "Looking for a Data Scientist to analyze large datasets and build predictive models. Experience with Python, R, and SQL required."
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudTech",
        "location": "Seattle, WA",
        "salary_min": 90000,
        "salary_max": 140000,
        "domain": "DevOps",
        "total_years_required": 4,
        "job_description": "Join our DevOps team to manage cloud infrastructure and CI/CD pipelines. Experience with AWS, Docker, and Kubernetes required."
    },
    {
        "title": "Frontend Developer",
        "company": "DesignStudio",
        "location": "Los Angeles, CA",
        "salary_min": 65000,
        "salary_max": 100000,
        "domain": "Frontend Development",
        "total_years_required": 2,
        "job_description": "We're looking for a creative Frontend Developer to build beautiful user interfaces. Experience with React, Vue.js, and CSS required."
    },
    {
        "title": "Backend Developer",
        "company": "APITech",
        "location": "Chicago, IL",
        "salary_min": 75000,
        "salary_max": 115000,
        "domain": "Backend Development",
        "total_years_required": 3,
        "job_description": "Join our backend team to build robust APIs and microservices. Experience with Python, Java, and databases required."
    },
    {
        "title": "Mobile Developer",
        "company": "AppWorks",
        "location": "Miami, FL",
        "salary_min": 70000,
        "salary_max": 110000,
        "domain": "Mobile Development",
        "total_years_required": 3,
        "job_description": "We need a Mobile Developer to build iOS and Android apps. Experience with React Native or Flutter preferred."
    },
    {
        "title": "QA Engineer",
        "company": "TestPro",
        "location": "Denver, CO",
        "salary_min": 60000,
        "salary_max": 95000,
        "domain": "Quality Assurance",
        "total_years_required": 2,
        "job_description": "Join our QA team to ensure software quality. Experience with automated testing and bug tracking tools required."
    }
]

async def populate_jobs():
    """Populate the database with sample job data"""
    
    print("🚀 Populating database with sample jobs...")
    
    try:
        async with AsyncSessionLocal() as session:
            # Check if jobs already exist
            result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
            count = result.fetchone()[0]
            
            if count > 0:
                print(f"⚠️  Database already has {count} jobs. Skipping population.")
                return
            
            # Add sample jobs
            for job_data in SAMPLE_JOBS:
                job = Job(**job_data)
                session.add(job)
            
            await session.commit()
            print(f"✅ Successfully added {len(SAMPLE_JOBS)} sample jobs!")
            
            # Verify the jobs were added
            result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
            final_count = result.fetchone()[0]
            print(f"📊 Total jobs in database: {final_count}")
            
    except Exception as e:
        print(f"❌ Error populating jobs: {e}")
        raise

async def main():
    """Main function"""
    print("📋 Sample Jobs to be added:")
    for i, job in enumerate(SAMPLE_JOBS, 1):
        print(f"  {i}. {job['title']} at {job['company']}")
    
    print("\n" + "="*50)
    
    await populate_jobs()
    
    print("\n🎉 Database population complete!")
    print("🌐 You can now start the server and view the jobs in the dashboard")

if __name__ == "__main__":
    asyncio.run(main()) 