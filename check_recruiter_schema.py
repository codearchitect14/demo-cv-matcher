import asyncio
from sqlalchemy import text
from config.database import AsyncSessionLocal

async def check_schema():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'recruiters' 
            AND column_name IN ('domain', 'company_size')
        """))
        rows = result.fetchall()
        print('Database schema:')
        for row in rows:
            print(f'{row[0]}: {row[1]}')

if __name__ == "__main__":
    asyncio.run(check_schema()) 