import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def add_values():
    """Add viewed and posted to interactiontypeenum"""
    
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Add viewed
        print("Adding 'viewed'...")
        await conn.execute("ALTER TYPE interactiontypeenum ADD VALUE IF NOT EXISTS 'viewed'")
        print("✅ Added 'viewed'")
        
        # Add posted  
        print("Adding 'posted'...")
        await conn.execute("ALTER TYPE interactiontypeenum ADD VALUE IF NOT EXISTS 'posted'")
        print("✅ Added 'posted'")
        
        print("\n✅ Done! Database ready.")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_values())
