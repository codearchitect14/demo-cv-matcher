#!/usr/bin/env python3
"""
Test to check frontend-backend connectivity
"""

import requests
import json

def test_frontend_backend():
    """Test if frontend can access backend"""
    
    print("🔍 Testing frontend-backend connectivity...")
    
    # Test the exact endpoint the frontend uses
    base_url = "http://localhost:8000"
    
    print("\n1. Testing jobs endpoint (exact frontend URL)...")
    try:
        url = f"{base_url}/api/v1/jobs/?skip=0&limit=10"
        print(f"   URL: {url}")
        
        response = requests.get(url)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Found {len(data)} jobs")
            
            if data:
                print("   📋 Sample jobs:")
                for i, job in enumerate(data[:3]):
                    print(f"      {i+1}. {job.get('title', 'No title')} - {job.get('company', 'No company')}")
                    print(f"         Location: {job.get('location', 'No location')}")
                    print(f"         Salary: {job.get('salary_min', 'N/A')} - {job.get('salary_max', 'N/A')}")
                    print()
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. Testing CORS headers...")
    try:
        response = requests.options(f"{base_url}/api/v1/jobs/")
        print(f"   Status: {response.status_code}")
        print(f"   CORS Headers: {dict(response.headers)}")
        
        if 'Access-Control-Allow-Origin' in response.headers:
            print("   ✅ CORS headers present")
        else:
            print("   ⚠️  CORS headers missing")
            
    except Exception as e:
        print(f"   ❌ CORS test error: {e}")

if __name__ == "__main__":
    test_frontend_backend() 