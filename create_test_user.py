import requests
import json

def create_test_user():
    """Create a test user account"""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("=== CREATING TEST USER ===")
    
    # Test user data - fixed to meet requirements
    user_data = {
        "email": "test@example.com",
        "password": "TestPass123!",
        "name": "Test User",
        "summary": "Experienced IT professional looking for new opportunities",
        "location": "New York",
        "domain": "IT",
        "expected_salary_min": 50000,
        "expected_salary_max": 80000
    }
    
    try:
        response = requests.post(
            f"{base_url}/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Registration response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User created successfully!")
            print(f"User ID: {data.get('id')}")
            print(f"Email: {data.get('email')}")
            return True
        elif response.status_code == 422:
            print("❌ User already exists or validation error")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
        return False

def test_login():
    """Test login with the created user"""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("\n=== TESTING LOGIN ===")
    
    login_data = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(
            f"{base_url}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"Token: {data.get('access_token', 'No token')[:30]}...")
            return data.get('access_token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return None

if __name__ == "__main__":
    # Try to create user
    user_created = create_test_user()
    
    if user_created:
        print("\n✅ User account ready!")
    else:
        print("\n⚠️ User might already exist, trying login...")
    
    # Test login
    token = test_login()
    
    if token:
        print("\n✅ Authentication is working!")
        print("You can now use these credentials in the frontend:")
        print("Email: test@example.com")
        print("Password: TestPass123!")
    else:
        print("\n❌ Authentication is not working")
        print("Please check the backend logs for more details") 