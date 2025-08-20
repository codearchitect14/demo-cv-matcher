#!/usr/bin/env python3
"""
Database initialization script using raw SQL to avoid prepared statement issues
"""

import asyncio
import sys
import os
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'job_matcher')}"
)

async def create_tables_raw():
    try:
        # Connect using DSN; Supabase requires SSL
        conn = await asyncpg.connect(
            dsn=DATABASE_URL,
            statement_cache_size=0,
            timeout=60,
            ssl="require",
        )
        logger.info("Connected to database successfully")

        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS candidates (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            location VARCHAR(255),
            domain VARCHAR(100),
            expected_salary_min INTEGER,
            expected_salary_max INTEGER,
            summary TEXT,
            role VARCHAR(50) DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS recruiters (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            company VARCHAR(255),
            role VARCHAR(50) DEFAULT 'recruiter',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            company VARCHAR(255) NOT NULL,
            location VARCHAR(255),
            salary_min INTEGER,
            salary_max INTEGER,
            domain VARCHAR(100),
            total_years_required INTEGER,
            job_description TEXT,
            recruiter_id INTEGER REFERENCES recruiters(id),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS job_mandatory_skills (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
            skill VARCHAR(255) NOT NULL,
            min_experience INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
            job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(candidate_id, job_id)
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
            job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
            interaction_type VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS skills (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            category VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS candidate_skills (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
            skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
            experience_years INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(candidate_id, skill_id)
        );

        CREATE TABLE IF NOT EXISTS job_skills (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
            skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
            min_experience INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(job_id, skill_id)
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            user_type VARCHAR(50),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100),
            resource_id INTEGER,
            details JSONB,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """

        await conn.execute(create_tables_sql)
        logger.info("All tables created successfully")
        await conn.close()
        return True

    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

async def main():
    logger.info("Starting database initialization with raw SQL...")
    success = await create_tables_raw()
    if not success:
        logger.error("Database initialization failed!")
        sys.exit(1)
    logger.info("Database initialization completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
