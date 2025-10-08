#!/usr/bin/env python3
"""
Setup Company Subscriptions table and assign default plans to existing companies
"""
import asyncio
import asyncpg
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

async def setup_company_subscriptions():
    """Create company_subscriptions table and assign default plans to existing companies"""
    
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
        with open('scripts/create_company_subscriptions_table.sql', 'r') as f:
            sql_content = f.read()
        
        await conn.execute(sql_content)
        print("✅ Created company_subscriptions table")
        
        # Get the Silver plan (cheapest) as default
        silver_plan = await conn.fetchrow("SELECT id FROM offer_plans WHERE plan_name = 'Silver'")
        if not silver_plan:
            print("❌ Silver plan not found. Please run offer plans setup first.")
            return False
        
        silver_plan_id = silver_plan['id']
        print(f"✅ Found Silver plan: {silver_plan_id}")
        
        # Get all companies that don't have subscriptions yet
        companies_without_subscriptions = await conn.fetch("""
            SELECT c.id, c.name 
            FROM companies c
            LEFT JOIN company_subscriptions cs ON c.id = cs.company_id
            WHERE cs.id IS NULL
        """)
        
        print(f"📊 Found {len(companies_without_subscriptions)} companies without subscriptions")
        
        # Assign Silver plan to all companies without subscriptions
        for company in companies_without_subscriptions:
            await conn.execute("""
                INSERT INTO company_subscriptions (company_id, offer_plan_id, status)
                VALUES ($1, $2, 'Active')
            """, company['id'], silver_plan_id)
            print(f"✅ Assigned Silver plan to company: {company['name']}")
        
        # Verify the data
        subscription_count = await conn.fetchval("SELECT COUNT(*) FROM company_subscriptions")
        print(f"\n📊 Total company subscriptions: {subscription_count}")
        
        # Show subscription summary
        summary = await conn.fetch("""
            SELECT 
                c.name as company_name,
                op.plan_name,
                op.price,
                cs.status,
                cs.subscribed_at
            FROM company_subscriptions cs
            JOIN companies c ON cs.company_id = c.id
            JOIN offer_plans op ON cs.offer_plan_id = op.id
            ORDER BY c.name
        """)
        
        print(f"\n📋 Company Subscriptions Summary:")
        for row in summary:
            print(f"  - {row['company_name']}: {row['plan_name']} (${row['price']}) - {row['status']}")
        
        await conn.close()
        print("\n✅ Company subscriptions setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up company subscriptions: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_company_subscriptions())
    sys.exit(0 if success else 1)
