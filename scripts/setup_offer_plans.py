#!/usr/bin/env python3
"""
Setup Offer Plans table and seed with test data
"""
import asyncio
import asyncpg
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

async def setup_offer_plans():
    """Create offer_plans table and seed with test data"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    # Convert SQLAlchemy URL to asyncpg format
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url, statement_cache_size=0)
        print("✅ Connected to database")
        
        # Read and execute the SQL file
        with open('scripts/create_offer_plans_table.sql', 'r') as f:
            sql_content = f.read()
        
        await conn.execute(sql_content)
        print("✅ Created offer_plans table")
        
        # Seed with test data
        test_plans = [
            {
                'plan_name': 'Platinum',
                'price': 299.00,
                'job_post_limit': None,  # Unlimited
                'recruiter_limit': 20,
                'candidate_views': None,  # Unlimited
                'analytics_level': 'Advanced',
                'support_level': '24/7 Priority',
                'status': 'Active'
            },
            {
                'plan_name': 'Gold',
                'price': 199.00,
                'job_post_limit': 50,
                'recruiter_limit': 10,
                'candidate_views': 5000,
                'analytics_level': 'Standard',
                'support_level': 'Business Hours',
                'status': 'Active'
            },
            {
                'plan_name': 'Silver',
                'price': 99.00,
                'job_post_limit': 20,
                'recruiter_limit': 5,
                'candidate_views': 1000,
                'analytics_level': 'Basic',
                'support_level': 'Email Only',
                'status': 'Active'
            }
        ]
        
        # Insert test plans (using INSERT ... ON CONFLICT to avoid duplicates)
        for plan in test_plans:
            await conn.execute("""
                INSERT INTO offer_plans (
                    plan_name, price, job_post_limit, recruiter_limit, 
                    candidate_views, analytics_level, support_level, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (plan_name) DO UPDATE SET
                    price = EXCLUDED.price,
                    job_post_limit = EXCLUDED.job_post_limit,
                    recruiter_limit = EXCLUDED.recruiter_limit,
                    candidate_views = EXCLUDED.candidate_views,
                    analytics_level = EXCLUDED.analytics_level,
                    support_level = EXCLUDED.support_level,
                    status = EXCLUDED.status,
                    updated_at = NOW()
            """, 
                plan['plan_name'], plan['price'], plan['job_post_limit'], 
                plan['recruiter_limit'], plan['candidate_views'], 
                plan['analytics_level'], plan['support_level'], plan['status']
            )
            print(f"✅ Seeded {plan['plan_name']} plan")
        
        # Verify the data
        rows = await conn.fetch("SELECT plan_name, price, status FROM offer_plans ORDER BY price DESC")
        print(f"\n📊 Current offer plans:")
        for row in rows:
            print(f"  - {row['plan_name']}: ${row['price']} ({row['status']})")
        
        await conn.close()
        print("\n✅ Offer plans setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up offer plans: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_offer_plans())
    sys.exit(0 if success else 1)
