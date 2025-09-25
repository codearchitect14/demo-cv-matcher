#!/usr/bin/env python3
"""
Create assessment and MCQ database tables
"""
import asyncio
import asyncpg
import os
from pathlib import Path

async def create_tables():
    """Create the assessment and MCQ tables"""
    
    # Database connection parameters
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/cv_matcher')
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("Connected to database successfully")
        
        # Create assessments table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                application_id INTEGER PRIMARY KEY,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                score DECIMAL(5,2),
                start_time TIMESTAMP,
                completion_time TIMESTAMP,
                cheat_attempts INTEGER DEFAULT 0,
                mcq_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created assessments table")
        
        # Create job_mcqs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS job_mcqs (
                id SERIAL PRIMARY KEY,
                job_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer CHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id, question_number)
            )
        """)
        print("✅ Created job_mcqs table")
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_assessments_candidate_id ON assessments(candidate_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_assessments_job_id ON assessments(job_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_job_mcqs_job_id ON job_mcqs(job_id)")
        print("✅ Created indexes")
        
        # Add foreign key constraints if parent tables exist
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('applications', 'jobs')
        """)
        existing_tables = [row['table_name'] for row in tables]
        
        if 'applications' in existing_tables:
            await conn.execute("""
                ALTER TABLE assessments ADD CONSTRAINT fk_assessments_application 
                FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
            """)
            print("✅ Added foreign key constraint to applications table")
            
        if 'jobs' in existing_tables:
            await conn.execute("""
                ALTER TABLE job_mcqs ADD CONSTRAINT fk_job_mcqs_job 
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
            """)
            print("✅ Added foreign key constraint to jobs table")
        
        # Verify tables were created
        assessments_count = await conn.fetchval("SELECT COUNT(*) FROM assessments")
        mcqs_count = await conn.fetchval("SELECT COUNT(*) FROM job_mcqs")
        
        print(f"\n📊 Database Status:")
        print(f"   - assessments table: {assessments_count} records")
        print(f"   - job_mcqs table: {mcqs_count} records")
        print(f"\n🎉 Assessment tables created successfully!")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(create_tables())
