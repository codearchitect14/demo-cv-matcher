import requests
import json

def test_login_after_fix():
    """Test login after pgbouncer fix"""
    
    print("=== TESTING LOGIN AFTER PGBOUNCER FIX ===")
    
    # Test login with valid credentials
    login_data = {
        "email": "db5@boolmind.com",
        "password": "your_password_here"  # Replace with actual password
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
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
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("Please make sure the backend is running on localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return None

if __name__ == "__main__":
    token = test_login_after_fix()
    
    if token:
        print("\n✅ Login is working! The pgbouncer fix is successful.")
        print("You can now use the frontend login form.")
    else:
        print("\n❌ Login is still not working.")
        print("Please check the backend logs for more details.") 