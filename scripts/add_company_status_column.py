"""
Add status column to companies table for super admin approval workflow
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def add_status_column():
    from config.connection_pool import global_pool
    
    print("Adding status column to companies table...")
    
    try:
        # Check if column exists
        column_check = await global_pool.fetchrow(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'companies' AND column_name = 'status'
            """
        )
        
        if column_check:
            print("✅ Status column already exists")
        else:
            # Add status column
            await global_pool.execute(
                """
                ALTER TABLE companies 
                ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL
                """
            )
            
            print("✅ Status column added successfully")
            
            # Update existing companies to have ACTIVE status
            await global_pool.execute(
                """
                UPDATE companies 
                SET status = CASE 
                    WHEN is_active = true THEN 'ACTIVE'
                    ELSE 'INACTIVE'
                END
                WHERE status IS NULL OR status = ''
                """
            )
            
            print("✅ Existing companies updated with status")
        
        # Create index on status column
        try:
            await global_pool.execute(
                "CREATE INDEX IF NOT EXISTS idx_company_status ON companies(status)"
            )
            print("✅ Index created on status column")
        except Exception as e:
            print(f"ℹ️  Index might already exist: {e}")
        
        print()
        print("✅ Migration completed successfully!")
        print()
        print("Status values:")
        print("- PENDING: Awaiting super admin approval")
        print("- ACTIVE: Approved and active")
        print("- REJECTED: Rejected by super admin")
        print("- SUSPENDED: Temporarily suspended")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_status_column())

