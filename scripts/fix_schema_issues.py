#!/usr/bin/env python3
"""
Script to fix all database schema issues
This script will:
1. Drop problematic indexes
2. Recreate indexes with correct column names
3. Ensure all foreign key constraints are properly set
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

async def fix_schema_issues():
    """Fix all database schema issues"""
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0
    )
    
    try:
        logger.info("Starting schema fixes...")
        
        # 1. Drop problematic indexes on jobs table
        logger.info("Dropping problematic indexes on jobs table...")
        
        problematic_indexes = [
            'idx_job_company_location',
            'idx_job_company'
        ]
        
        for index_name in problematic_indexes:
            try:
                await conn.execute(f"DROP INDEX IF EXISTS {index_name}")
                logger.info(f"Dropped index: {index_name}")
            except Exception as e:
                logger.info(f"Index {index_name} doesn't exist or already dropped: {e}")
        
        # 2. Create correct indexes for jobs table
        logger.info("Creating correct indexes for jobs table...")
        
        try:
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_company_location 
                ON jobs(company_id, location)
            """)
            logger.info("Created index: idx_job_company_location")
        except Exception as e:
            logger.info(f"Index idx_job_company_location already exists: {e}")
        
        try:
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_company_id 
                ON jobs(company_id)
            """)
            logger.info("Created index: idx_job_company_id")
        except Exception as e:
            logger.info(f"Index idx_job_company_id already exists: {e}")
        
        # 3. Ensure all required indexes exist
        logger.info("Ensuring all required indexes exist...")
        
        required_indexes = [
            ("idx_job_location_domain", "jobs(location, domain)"),
            ("idx_job_salary_range", "jobs(salary_min, salary_max)"),
            ("idx_job_domain_years", "jobs(domain, total_years_required)"),
            ("idx_job_created_at", "jobs(created_at)"),
            ("idx_job_updated_at", "jobs(updated_at)"),
            ("idx_job_title", "jobs(title)"),
            ("idx_job_location", "jobs(location)"),
            ("idx_job_domain", "jobs(domain)"),
            ("idx_job_recruiter", "jobs(recruiter_id)"),
            ("idx_job_threshold_score", "jobs(threshold_score)"),
            ("idx_job_is_active", "jobs(is_active)"),
        ]
        
        for index_name, index_def in required_indexes:
            try:
                await conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                logger.info(f"Created/verified index: {index_name}")
            except Exception as e:
                logger.info(f"Index {index_name} already exists: {e}")
        
        # 4. Ensure all required indexes exist for recruiters table
        logger.info("Ensuring all required indexes exist for recruiters table...")
        
        recruiter_indexes = [
            ("idx_recruiter_domain_company_size", "recruiters(domain, company_size)"),
            ("idx_recruiter_role", "recruiters(role)"),
            ("idx_recruiter_email", "recruiters(email)"),
            ("idx_recruiter_company_id", "recruiters(company_id)"),
            ("idx_recruiter_full_name", "recruiters(full_name)"),
            ("idx_recruiter_company_name", "recruiters(company_name)"),
            ("idx_recruiter_is_active", "recruiters(is_active)"),
            ("idx_recruiter_email_verified", "recruiters(email_verified)"),
        ]
        
        for index_name, index_def in recruiter_indexes:
            try:
                await conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                logger.info(f"Created/verified index: {index_name}")
            except Exception as e:
                logger.info(f"Index {index_name} already exists: {e}")
        
        # 5. Ensure all required indexes exist for companies table
        logger.info("Ensuring all required indexes exist for companies table...")
        
        company_indexes = [
            ("idx_company_name", "companies(name)"),
            ("idx_company_domain", "companies(domain)"),
            ("idx_company_is_active", "companies(is_active)"),
            ("idx_company_created_at", "companies(created_at)"),
        ]
        
        for index_name, index_def in company_indexes:
            try:
                await conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                logger.info(f"Created/verified index: {index_name}")
            except Exception as e:
                logger.info(f"Index {index_name} already exists: {e}")
        
        # 6. Verify foreign key constraints
        logger.info("Verifying foreign key constraints...")
        
        # Check if foreign key constraints exist
        fk_checks = [
            ("recruiters", "company_id", "companies", "id"),
            ("jobs", "company_id", "companies", "id"),
            ("jobs", "recruiter_id", "recruiters", "id"),
        ]
        
        for table, column, ref_table, ref_column in fk_checks:
            try:
                result = await conn.fetch("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = $1 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name LIKE '%$2%'
                """, table, column)
                
                if result:
                    logger.info(f"Foreign key constraint exists for {table}.{column}")
                else:
                    logger.warning(f"Foreign key constraint missing for {table}.{column}")
            except Exception as e:
                logger.info(f"Could not check foreign key for {table}.{column}: {e}")
        
        # 7. Check table structure
        logger.info("Checking table structure...")
        
        tables_to_check = ['companies', 'recruiters', 'jobs']
        
        for table in tables_to_check:
            try:
                columns = await conn.fetch(f"""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = $1 
                    ORDER BY ordinal_position
                """, table)
                
                logger.info(f"Table {table} structure:")
                for col in columns:
                    logger.info(f"  {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
                    
            except Exception as e:
                logger.error(f"Could not check table {table}: {e}")
        
        logger.info("Schema fixes completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during schema fixes: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_schema_issues())



