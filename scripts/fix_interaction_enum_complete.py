import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_enum():
    """Add missing lowercase values to interactiontypeenum"""
    
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        print("Checking interactiontypeenum values...")
        
        # Check current values
        result = await conn.fetch("SELECT unnest(enum_range(NULL::interactiontypeenum)) AS enum_values")
        current_values = [row['enum_values'] for row in result]
        print(f"\nCurrent values: {current_values}")
        
        # Add missing lowercase values
        needed_values = ['viewed', 'applied', 'rejected', 'posted', 'edited']
        
        for value in needed_values:
            if value not in current_values:
                print(f"Adding '{value}'...")
                await conn.execute(f"ALTER TYPE interactiontypeenum ADD VALUE IF NOT EXISTS '{value}'")
                print(f"✅ Added '{value}'")
            else:
                print(f"✓ '{value}' already exists")
        
        print("\n✅ All values added successfully!")
        
        # Verify final state
        result = await conn.fetch("SELECT unnest(enum_range(NULL::interactiontypeenum)) AS enum_values")
        print("\nFinal enum values:")
        for row in result:
            print(f"  - {row['enum_values']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_enum())
