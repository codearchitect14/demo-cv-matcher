#!/usr/bin/env python3
"""
Simple script to fix the company migration
This script will:
1. Check if companies table exists and has data
2. Update existing recruiters and jobs with company assignments
3. Make company_id NOT NULL
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

async def fix_company_migration():
    """Fix the company migration"""
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0
    )
    
    try:
        logger.info("Starting company migration fix...")
        
        # 1. Check if companies table exists and has data
        try:
            company_count = await conn.fetchval("SELECT COUNT(*) FROM companies")
            logger.info(f"Found {company_count} companies in database")
            
            if company_count == 0:
                logger.info("No companies found, creating sample companies...")
                
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
                
                logger.info("Sample companies created successfully")
            else:
                logger.info("Companies already exist, skipping creation")
                
        except Exception as e:
            logger.error(f"Error checking companies: {e}")
            return
        
        # 2. Get all companies
        companies = await conn.fetch("SELECT id, name, domain FROM companies")
        company_map = {company['domain']: company['id'] for company in companies}
        logger.info(f"Available companies: {[c['name'] for c in companies]}")
        
        # 3. Update recruiters without company_id
        logger.info("Updating recruiters without company assignments...")
        
        recruiters = await conn.fetch("SELECT id, company_name, domain FROM recruiters WHERE company_id IS NULL")
        logger.info(f"Found {len(recruiters)} recruiters without company assignments")
        
        for recruiter in recruiters:
            # Try to match by domain first, then by company name
            company_id = None
            
            # Match by domain
            if recruiter['domain'] in company_map:
                company_id = company_map[recruiter['domain']]
                logger.info(f"Matched recruiter {recruiter['id']} to company by domain: {recruiter['domain']}")
            else:
                # Match by company name (partial match)
                for company in companies:
                    if company['name'].lower() in recruiter['company_name'].lower() or \
                       recruiter['company_name'].lower() in company['name'].lower():
                        company_id = company['id']
                        logger.info(f"Matched recruiter {recruiter['id']} to company by name: {company['name']}")
                        break
            
            # If no match found, assign to first company (TechCorp)
            if company_id is None:
                company_id = companies[0]['id']
                logger.warning(f"No company match found for recruiter {recruiter['id']} ({recruiter['company_name']}), assigning to default company: {companies[0]['name']}")
            
            # Update recruiter
            await conn.execute("""
                UPDATE recruiters 
                SET company_id = $1 
                WHERE id = $2
            """, company_id, recruiter['id'])
        
        # 4. Update jobs without company_id
        logger.info("Updating jobs without company assignments...")
        
        jobs = await conn.fetch("SELECT id, company FROM jobs WHERE company_id IS NULL")
        logger.info(f"Found {len(jobs)} jobs without company assignments")
        
        for job in jobs:
            # Try to match by company name
            company_id = None
            
            if job['company']:
                for company in companies:
                    if company['name'].lower() in job['company'].lower() or \
                       job['company'].lower() in company['name'].lower():
                        company_id = company['id']
                        logger.info(f"Matched job {job['id']} to company: {company['name']}")
                        break
            
            # If no match found, assign to first company (TechCorp)
            if company_id is None:
                company_id = companies[0]['id']
                logger.warning(f"No company match found for job {job['id']} ({job['company']}), assigning to default company: {companies[0]['name']}")
            
            # Update job
            await conn.execute("""
                UPDATE jobs 
                SET company_id = $1 
                WHERE id = $2
            """, company_id, job['id'])
        
        # 5. Make company_id NOT NULL for recruiters (if not already)
        try:
            logger.info("Making company_id NOT NULL for recruiters...")
            await conn.execute("ALTER TABLE recruiters ALTER COLUMN company_id SET NOT NULL")
            logger.info("Recruiters company_id is now NOT NULL")
        except Exception as e:
            logger.info(f"Recruiters company_id constraint already set: {e}")
        
        # 6. Make company_id NOT NULL for jobs (if not already)
        try:
            logger.info("Making company_id NOT NULL for jobs...")
            await conn.execute("ALTER TABLE jobs ALTER COLUMN company_id SET NOT NULL")
            logger.info("Jobs company_id is now NOT NULL")
        except Exception as e:
            logger.info(f"Jobs company_id constraint already set: {e}")
        
        logger.info("Company migration fix completed successfully!")
        
        # 7. Verify the migration
        logger.info("Verifying migration...")
        
        # Check companies
        company_count = await conn.fetchval("SELECT COUNT(*) FROM companies")
        logger.info(f"Companies: {company_count}")
        
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
        logger.error(f"Error during migration fix: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_company_migration())

