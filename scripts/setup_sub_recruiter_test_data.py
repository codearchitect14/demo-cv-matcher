#!/usr/bin/env python3
"""
Setup test data for sub-recruiter dashboard
This script assigns some jobs to tayyab10@boolmind.com for testing
"""

import asyncio
import asyncpg
import os
from datetime import datetime

async def setup_test_data():
    """Setup test data for sub-recruiter dashboard"""
    
    # Database connection
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/cv_matcher')
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("Connected to database")
        
        # First, get or create the test recruiter
        recruiter_query = """
            SELECT id FROM recruiters WHERE email = 'tayyab10@boolmind.com'
        """
        recruiter_result = await conn.fetchrow(recruiter_query)
        
        if not recruiter_result:
            print("Creating test recruiter...")
            recruiter_insert = """
                INSERT INTO recruiters (full_name, email, password_hash, company_id, created_at)
                VALUES ('Tayyab Test', 'tayyab10@boolmind.com', '$2b$12$test', 1, NOW())
                RETURNING id
            """
            recruiter_id = await conn.fetchval(recruiter_insert)
            print(f"Created recruiter with ID: {recruiter_id}")
        else:
            recruiter_id = recruiter_result['id']
            print(f"Found existing recruiter with ID: {recruiter_id}")
        
        # Get some jobs to assign
        jobs_query = """
            SELECT id, title, company, location 
            FROM jobs 
            WHERE assigned_recruiter_id IS NULL 
            LIMIT 5
        """
        jobs = await conn.fetch(jobs_query)
        
        if not jobs:
            print("No unassigned jobs found. Creating some test jobs...")
            # Create some test jobs
            test_jobs = [
                ("Software Engineer", "TechCorp", "San Francisco"),
                ("Data Scientist", "DataCorp", "New York"),
                ("Frontend Developer", "WebCorp", "Seattle"),
                ("Backend Developer", "APICorp", "Austin"),
                ("Full Stack Developer", "StackCorp", "Boston")
            ]
            
            for title, company, location in test_jobs:
                job_insert = """
                    INSERT INTO jobs (title, company, location, description, requirements, 
                                    salary_min, salary_max, status, created_at, assigned_recruiter_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), $9)
                """
                await conn.execute(job_insert, 
                    title, company, location, 
                    f"Great opportunity for {title} at {company}",
                    f"Experience in {title} required",
                    50000, 100000, "ACTIVE", recruiter_id
                )
            
            # Get the newly created jobs
            jobs = await conn.fetch(jobs_query)
        
        # Assign jobs to the recruiter
        assigned_count = 0
        for job in jobs:
            assign_query = """
                UPDATE jobs 
                SET assigned_recruiter_id = $1 
                WHERE id = $2
            """
            await conn.execute(assign_query, recruiter_id, job['id'])
            assigned_count += 1
            print(f"Assigned job: {job['title']} at {job['company']}")
        
        print(f"\n✅ Setup complete!")
        print(f"📊 Assigned {assigned_count} jobs to tayyab10@boolmind.com")
        print(f"🔗 Access the dashboard at: http://localhost:3000/sub-recruiter/dashboard")
        print(f"📧 Login with: tayyab10@boolmind.com")
        
        # Create some test applications if they don't exist
        applications_query = """
            SELECT COUNT(*) as count FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE j.assigned_recruiter_id = $1
        """
        app_count = await conn.fetchval(applications_query, recruiter_id)
        
        if app_count == 0:
            print("\n📝 Creating some test applications...")
            
            # Get some candidates
            candidates_query = "SELECT id FROM candidates LIMIT 3"
            candidates = await conn.fetch(candidates_query)
            
            # Get assigned jobs
            assigned_jobs_query = """
                SELECT id FROM jobs WHERE assigned_recruiter_id = $1
            """
            assigned_jobs = await conn.fetch(assigned_jobs_query, recruiter_id)
            
            # Create applications
            for job in assigned_jobs:
                for candidate in candidates:
                    app_insert = """
                        INSERT INTO applications (candidate_id, job_id, status, applied_at)
                        VALUES ($1, $2, $3, NOW())
                    """
                    statuses = ['APPLIED', 'INTERVIEW_SCHEDULED', 'REJECTED']
                    import random
                    status = random.choice(statuses)
                    await conn.execute(app_insert, candidate['id'], job['id'], status)
            
            print("✅ Created test applications")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_test_data())
