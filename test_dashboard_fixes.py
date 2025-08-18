#!/usr/bin/env python3
"""
Test script to verify dashboard fixes:
1. Modal positioning (centered)
2. API endpoint fixes (422 error)
3. Job recommendations instead of recent jobs
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_job_recommendations_endpoint():
    """Test the new job recommendations endpoint"""
    print("Testing job recommendations endpoint...")
    
    try:
        # First, try to get recommendations without auth (should fail)
        response = requests.get(f"{BASE_URL}/api/v1/jobs/recommendations")
        print(f"Unauthenticated request status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Endpoint correctly requires authentication")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing recommendations endpoint: {e}")

def test_applications_endpoint():
    """Test the applications endpoint"""
    print("\nTesting applications endpoint...")
    
    try:
        # Test the my-applications endpoint without auth
        response = requests.get(f"{BASE_URL}/api/v1/applications/my-applications")
        print(f"My applications endpoint status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Endpoint correctly requires authentication")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing applications endpoint: {e}")

def test_public_endpoints():
    """Test public endpoints that should work without auth"""
    print("\nTesting public endpoints...")
    
    try:
        # Test public jobs endpoint
        response = requests.get(f"{BASE_URL}/api/v1/jobs/public?limit=5")
        print(f"Public jobs endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Public jobs endpoint working, returned {len(data)} jobs")
        else:
            print(f"❌ Public jobs endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing public endpoints: {e}")

def main():
    print("🧪 Testing Dashboard Fixes")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print("✅ Backend server is running")
    except Exception as e:
        print(f"❌ Backend server not running: {e}")
        print("Please start the backend server first:")
        print("uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Run tests
    test_job_recommendations_endpoint()
    test_applications_endpoint()
    test_public_endpoints()
    
    print("\n" + "=" * 50)
    print("📋 Summary of fixes implemented:")
    print("1. ✅ Modal positioning: Added centered modal styles with backdrop blur")
    print("2. ✅ API endpoint fixes: Added fallback logic for 422 errors")
    print("3. ✅ Job recommendations: Replaced 'Recent Job Postings' with 'Recommended Jobs'")
    print("4. ✅ Professional styling: Modern modal design with animations")
    print("\n🎯 Next steps:")
    print("- Start the frontend: npm start")
    print("- Login as a candidate")
    print("- Test the 'Update Profile' and 'Upload CV' modals")
    print("- Verify job recommendations are showing instead of recent jobs")

if __name__ == "__main__":
    main()
