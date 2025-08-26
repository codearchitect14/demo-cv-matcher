import asyncio
import urllib.request
import urllib.parse
import json
from config.database import get_db_session
from db.crud.candidate import candidate as candidate_crud

def make_request(url, method="GET", data=None, headers=None):
    """Make HTTP request using urllib"""
    if headers is None:
        headers = {}
    
    if data and method == "POST":
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            return response.status, response_data
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

def test_auth_flow():
    """Test the complete authentication flow"""
    print("🔍 Testing Authentication Flow...")
    
    # Test credentials - using the correct ones
    test_email = "db5@boolmind.com"
    test_password = "Alibool123@"
    
    # Step 1: Test login
    print("\n1. Testing login...")
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    status, response_data = make_request(
        "http://localhost:8000/api/v1/auth/login",
        method="POST",
        data=login_data
    )
    
    print(f"Login status: {status}")
    
    if status == 200:
        login_result = json.loads(response_data)
        print("✅ Login successful!")
        print(f"Access token: {login_result.get('access_token', 'N/A')[:50]}...")
        print(f"User ID: {login_result.get('user_id')}")
        print(f"Role: {login_result.get('role')}")
        
        access_token = login_result.get('access_token')
        
        # Step 2: Test profile endpoint
        print("\n2. Testing profile endpoint...")
        status, response_data = make_request(
            "http://localhost:8000/api/v1/candidates/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"Profile status: {status}")
        
        if status == 200:
            profile_data = json.loads(response_data)
            print("✅ Profile fetch successful!")
            print(f"User: {profile_data.get('name')} ({profile_data.get('email')})")
        else:
            print(f"❌ Profile fetch failed: {response_data}")
        
        # Step 3: Test applications endpoint
        print("\n3. Testing applications endpoint...")
        status, response_data = make_request(
            "http://localhost:8000/api/v1/applications/my-applications",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"Applications status: {status}")
        
        if status == 200:
            apps_data = json.loads(response_data)
            print("✅ Applications fetch successful!")
            print(f"Found {len(apps_data)} applications")
        else:
            print(f"❌ Applications fetch failed: {response_data}")
        
        # Step 4: Test recommendations endpoint
        print("\n4. Testing recommendations endpoint...")
        status, response_data = make_request(
            "http://localhost:8000/api/v1/jobs/recommendations",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"Recommendations status: {status}")
        
        if status == 200:
            rec_data = json.loads(response_data)
            print("✅ Recommendations fetch successful!")
            print(f"Found {len(rec_data)} recommendations")
        else:
            print(f"❌ Recommendations fetch failed: {response_data}")
        
    else:
        print(f"❌ Login failed: {response_data}")

async def check_user_in_db():
    """Check if test user exists in database"""
    print("\n🔍 Checking database for test user...")
    
    async for db in get_db_session():
        try:
            user = await candidate_crud.get_by_email(db, email="db5@boolmind.com")
            if user:
                print(f"✅ Test user found: {user.email} (ID: {user.id})")
                print(f"   Role: {getattr(user, 'role', 'N/A')}")
                return True
            else:
                print("❌ Test user not found in database")
                return False
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False

async def main():
    print("🚀 Starting Authentication Debug Test...")
    
    # Check database first
    await check_user_in_db()
    
    # Test authentication flow
    test_auth_flow()
    
    print("\n🏁 Authentication debug test completed!")

if __name__ == "__main__":
    asyncio.run(main())
