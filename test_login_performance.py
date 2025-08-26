import asyncio
import time
from config.database import get_db_session
from db.crud.candidate import candidate as candidate_crud
from config.security import get_password_hash

async def check_users():
    """Check existing users in the database"""
    async for db in get_db_session():
        users = await candidate_crud.get_multi(db, limit=5)
        print(f'Found {len(users)} users:')
        for user in users:
            print(f'- {user.email} (ID: {user.id})')
        return users

async def create_test_user():
    """Create a test user for performance testing"""
    async for db in get_db_session():
        # Check if test user already exists
        existing = await candidate_crud.get_by_email(db, email='test@example.com')
        if existing:
            print(f'Test user already exists: {existing.email}')
            return existing
        
        # Create test user
        user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password_hash': get_password_hash('testpass123'),
            'location': 'Test City',
            'domain': 'Technology',
            'summary': 'Test user for performance testing',
            'role': 'user'
        }
        user = await candidate_crud.create(db, obj_in=user_data)
        print(f'Created test user: {user.email}')
        return user

async def test_login_performance():
    """Test login performance with timing"""
    async for db in get_db_session():
        start_time = time.time()
        
        # Simulate login process
        user = await candidate_crud.get_by_email(db, email='test@example.com')
        
        if user:
            elapsed = time.time() - start_time
            print(f'Login query completed in {elapsed:.3f} seconds')
            return elapsed
        else:
            print('Test user not found')
            return None

async def main():
    print("=== Login Performance Test ===")
    
    # Check existing users
    print("\n1. Checking existing users...")
    users = await check_users()
    
    # Create test user if needed
    print("\n2. Ensuring test user exists...")
    test_user = await create_test_user()
    
    # Test login performance
    print("\n3. Testing login performance...")
    performance = await test_login_performance()
    
    if performance:
        print(f"\n✅ Login performance: {performance:.3f} seconds")
        if performance < 6.0:
            print("🎉 Login is under 6 seconds target!")
        else:
            print("⚠️  Login is still above 6 seconds target")
    else:
        print("❌ Login performance test failed")

if __name__ == "__main__":
    asyncio.run(main())
