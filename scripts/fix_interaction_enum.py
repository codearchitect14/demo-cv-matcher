import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_enum():
    """Add 'edited' to interactiontypeenum"""
    
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        print("Adding 'edited' to interactiontypeenum...")
        
        # Add the value if it doesn't exist
        await conn.execute("ALTER TYPE interactiontypeenum ADD VALUE IF NOT EXISTS 'edited'")
        
        print("✅ Successfully added 'edited' to interactiontypeenum")
        
        # Verify
        result = await conn.fetch("SELECT unnest(enum_range(NULL::interactiontypeenum)) AS enum_values")
        print("\nCurrent enum values:")
        for row in result:
            print(f"  - {row['enum_values']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_enum())
