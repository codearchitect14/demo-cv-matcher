import requests
import json

def test_backend_auth():
    """Test backend authentication endpoints"""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("=== BACKEND AUTHENTICATION TEST ===")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/auth/me", timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running on localhost:8000")
        return
    except Exception as e:
        print(f"❌ Server error: {e}")
        return
    
    # Test 2: Try to login with test credentials
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
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
            print(f"Token: {data.get('access_token', 'No token')[:20]}...")
            return data.get('access_token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return None

if __name__ == "__main__":
    token = test_backend_auth()
    
    if token:
        # Test 3: Test the token
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get("http://localhost:8000/api/v1/auth/me", headers=headers)
            print(f"Token test status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Token is valid!")
            else:
                print("❌ Token is invalid")
        except Exception as e:
            print(f"❌ Token test failed: {e}") 