import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def check_user():
    from config.connection_pool import global_pool
    
    result = await global_pool.fetchrow(
        "SELECT id, email, role FROM candidates WHERE email = $1",
        'aliboolmind228@gmail.com'
    )
    
    if result:
        print(f"User ID: {result['id']}")
        print(f"Email: {result['email']}")
        print(f"Role: '{result['role']}'")
    else:
        print("User not found in candidates table")

asyncio.run(check_user())

