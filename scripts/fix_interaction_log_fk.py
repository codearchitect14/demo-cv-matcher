import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_foreign_key():
    """Remove the foreign key constraint on interaction_log.user_id"""
    
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        print("Checking foreign key constraints on interaction_log...")
        
        # Check existing constraints
        constraints = await conn.fetch("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'interaction_log'
        """)
        
        print("\nCurrent constraints:")
        for c in constraints:
            print(f"  - {c['constraint_name']}: {c['constraint_type']}")
        
        # Drop the foreign key constraint on user_id
        print("\nDropping interaction_log_user_id_fkey constraint...")
        await conn.execute("ALTER TABLE interaction_log DROP CONSTRAINT IF EXISTS interaction_log_user_id_fkey")
        print("✅ Dropped foreign key constraint")
        
        print("\n✅ Done! interaction_log.user_id can now accept both candidate and recruiter IDs")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_foreign_key())
