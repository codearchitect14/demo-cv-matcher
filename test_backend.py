#!/usr/bin/env python3
"""
Simple test to verify the backend API is working
"""

import requests
import json

def test_backend():
    """Test the backend API endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing backend API...")
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: Jobs endpoint (without auth)
    print("\n2. Testing jobs endpoint (without auth)...")
    try:
        response = requests.get(f"{base_url}/api/v1/jobs/?limit=5")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Jobs endpoint works - Found {len(data)} jobs")
            if data:
                print(f"   📋 First job: {data[0].get('title', 'No title')}")
        else:
            print(f"   ❌ Jobs endpoint failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Jobs endpoint error: {e}")
    
    # Test 3: Check if server is running
    print("\n3. Testing server availability...")
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Server is running (docs accessible)")
        else:
            print("   ⚠️  Server might not be running properly")
    except Exception as e:
        print(f"   ❌ Server not accessible: {e}")
        print("   💡 Make sure to start the server with:")
        print("      python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    test_backend() 