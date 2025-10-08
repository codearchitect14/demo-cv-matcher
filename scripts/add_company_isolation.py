#!/usr/bin/env python3
"""
Script to add company isolation to the existing database
This script will:
1. Create the companies table
2. Add company_id to recruiters and jobs tables
3. Create sample companies for existing data
4. Update existing recruiters and jobs with company assignments
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_company_isolation():
    """Add company isolation to the database"""
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0
    )
    
    try:
        logger.info("Starting company isolation migration...")
        
        # 1. Create companies table
        logger.info("Creating companies table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                domain VARCHAR(100) NOT NULL,
                description TEXT,
                max_recruiters INTEGER NOT NULL DEFAULT 10,
                max_jobs INTEGER NOT NULL DEFAULT 100,
                contact_email VARCHAR(255),
                contact_phone VARCHAR(20),
                address TEXT,
                is_active BOOLEAN NOT NULL DEFAULT true,
                subscription_plan VARCHAR(50) NOT NULL DEFAULT 'basic',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create indexes for companies table
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_company_name ON companies(name);
            CREATE INDEX IF NOT EXISTS idx_company_domain ON companies(domain);
            CREATE INDEX IF NOT EXISTS idx_company_is_active ON companies(is_active);
            CREATE INDEX IF NOT EXISTS idx_company_created_at ON companies(created_at);
        """)
        
        # 2. Add company_id to recruiters table
        logger.info("Adding company_id to recruiters table...")
        await conn.execute("""
            ALTER TABLE recruiters 
            ADD COLUMN IF NOT EXISTS company_id INTEGER;
        """)
        
        # Add foreign key constraint (check if it exists first)
        try:
            await conn.execute("""
                ALTER TABLE recruiters 
                ADD CONSTRAINT fk_recruiters_company_id 
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            """)
        except Exception as e:
            if "already exists" not in str(e):
                raise
        
        # Create index
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_recruiter_company_id ON recruiters(company_id);
        """)
        
        # 3. Add company_id to jobs table
        logger.info("Adding company_id to jobs table...")
        await conn.execute("""
            ALTER TABLE jobs 
            ADD COLUMN IF NOT EXISTS company_id INTEGER;
        """)
        
        # Add foreign key constraint (check if it exists first)
        try:
            await conn.execute("""
                ALTER TABLE jobs 
                ADD CONSTRAINT fk_jobs_company_id 
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            """)
        except Exception as e:
            if "already exists" not in str(e):
                raise
        
        # Create index
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_company_id ON jobs(company_id);
        """)
        
        # 4. Create sample companies
        logger.info("Creating sample companies...")
        
        # Check if companies already exist
        existing_companies = await conn.fetch("SELECT COUNT(*) FROM companies")
        if existing_companies[0]['count'] == 0:
            # Create sample companies
            companies_data = [
                {
                    'name': 'TechCorp Solutions',
                    'domain': 'IT',
                    'description': 'Leading technology solutions provider',
                    'max_recruiters': 20,
                    'max_jobs': 200,
                    'contact_email': 'admin@techcorp.com',
                    'subscription_plan': 'premium'
                },
                {
                    'name': 'FinanceCorp Ltd',
                    'domain': 'Finance',
                    'description': 'Financial services and consulting',
                    'max_recruiters': 15,
                    'max_jobs': 150,
                    'contact_email': 'admin@financecorp.com',
                    'subscription_plan': 'basic'
                },
                {
                    'name': 'HealthCorp Medical',
                    'domain': 'Healthcare',
                    'description': 'Healthcare and medical services',
                    'max_recruiters': 25,
                    'max_jobs': 300,
                    'contact_email': 'admin@healthcorp.com',
                    'subscription_plan': 'enterprise'
                }
            ]
            
            for company_data in companies_data:
                await conn.execute("""
                    INSERT INTO companies (name, domain, description, max_recruiters, max_jobs, contact_email, subscription_plan)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, 
                company_data['name'], 
                company_data['domain'], 
                company_data['description'], 
                company_data['max_recruiters'], 
                company_data['max_jobs'], 
                company_data['contact_email'], 
                company_data['subscription_plan']
                )
        
        # 5. Update existing recruiters with company assignments
        logger.info("Updating existing recruiters with company assignments...")
        
        # Get all companies
        companies = await conn.fetch("SELECT id, name, domain FROM companies")
        company_map = {company['domain']: company['id'] for company in companies}
        
        # Get all recruiters without company_id
        recruiters = await conn.fetch("SELECT id, company_name, domain FROM recruiters WHERE company_id IS NULL")
        
        for recruiter in recruiters:
            # Try to match by domain first, then by company name
            company_id = None
            
            # Match by domain
            if recruiter['domain'] in company_map:
                company_id = company_map[recruiter['domain']]
            else:
                # Match by company name (partial match)
                for company in companies:
                    if company['name'].lower() in recruiter['company_name'].lower() or \
                       recruiter['company_name'].lower() in company['name'].lower():
                        company_id = company['id']
                        break
            
            # If no match found, assign to first company (TechCorp)
            if company_id is None:
                company_id = companies[0]['id']
                logger.warning(f"No company match found for recruiter {recruiter['id']}, assigning to default company")
            
            # Update recruiter
            await conn.execute("""
                UPDATE recruiters 
                SET company_id = $1 
                WHERE id = $2
            """, company_id, recruiter['id'])
        
        # 6. Update existing jobs with company assignments
        logger.info("Updating existing jobs with company assignments...")
        
        # Get all jobs without company_id
        jobs = await conn.fetch("SELECT id, company FROM jobs WHERE company_id IS NULL")
        
        for job in jobs:
            # Try to match by company name
            company_id = None
            
            if job['company']:
                for company in companies:
                    if company['name'].lower() in job['company'].lower() or \
                       job['company'].lower() in company['name'].lower():
                        company_id = company['id']
                        break
            
            # If no match found, assign to first company (TechCorp)
            if company_id is None:
                company_id = companies[0]['id']
                logger.warning(f"No company match found for job {job['id']}, assigning to default company")
            
            # Update job
            await conn.execute("""
                UPDATE jobs 
                SET company_id = $1 
                WHERE id = $2
            """, company_id, job['id'])
        
        # 7. Make company_id NOT NULL for recruiters
        logger.info("Making company_id NOT NULL for recruiters...")
        await conn.execute("""
            ALTER TABLE recruiters 
            ALTER COLUMN company_id SET NOT NULL
        """)
        
        # 8. Make company_id NOT NULL for jobs
        logger.info("Making company_id NOT NULL for jobs...")
        await conn.execute("""
            ALTER TABLE jobs 
            ALTER COLUMN company_id SET NOT NULL
        """)
        
        logger.info("Company isolation migration completed successfully!")
        
        # 9. Verify the migration
        logger.info("Verifying migration...")
        
        # Check companies
        company_count = await conn.fetchval("SELECT COUNT(*) FROM companies")
        logger.info(f"Companies created: {company_count}")
        
        # Check recruiters with company assignments
        recruiter_count = await conn.fetchval("SELECT COUNT(*) FROM recruiters WHERE company_id IS NOT NULL")
        logger.info(f"Recruiters with company assignments: {recruiter_count}")
        
        # Check jobs with company assignments
        job_count = await conn.fetchval("SELECT COUNT(*) FROM jobs WHERE company_id IS NOT NULL")
        logger.info(f"Jobs with company assignments: {job_count}")
        
        # Show company distribution
        distribution = await conn.fetch("""
            SELECT c.name, COUNT(r.id) as recruiters, COUNT(j.id) as jobs
            FROM companies c
            LEFT JOIN recruiters r ON c.id = r.company_id
            LEFT JOIN jobs j ON c.id = j.company_id
            GROUP BY c.id, c.name
            ORDER BY c.name
        """)
        
        logger.info("Company distribution:")
        for row in distribution:
            logger.info(f"  {row['name']}: {row['recruiters']} recruiters, {row['jobs']} jobs")
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_company_isolation())
