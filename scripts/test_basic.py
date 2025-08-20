#!/usr/bin/env python3
"""
Basic test script to verify the API is working
"""

import requests
import json
import time
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
HEALTH_CHECK_ENDPOINT = f"{API_BASE_URL}/health"

def test_health():
    """Test API health endpoint"""
    print("Testing API health...")
    try:
        response = requests.get(HEALTH_CHECK_ENDPOINT, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed: {data}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_simple_job():
    """Test simple job creation"""
    print("\nTesting simple job creation...")
    
    job_data = {
        "title": "Simple Test Job",
        "company": "Test Company",
        "location": "Remote",
        "salary_min": 50000,
        "salary_max": 100000,
        "domain": "Software",
        "total_years_required": 2,
        "job_description": "A simple test job.",
        "mandatory_skills": []
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/jobs/public", json=job_data, timeout=30)
        response.raise_for_status()
        job = response.json()
        print(f"✅ Job created successfully: {job['title']} (ID: {job['id']})")
        return True
    except Exception as e:
        print(f"❌ Job creation failed: {e}")
        if hasattr(e, 'response'):
            print(f"   Status: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
        return False

def main():
    print(f"Basic API test against {API_BASE_URL}")
    print("=" * 50)
    
    # Test 1: Health check
    health_ok = test_health()
    
    # Test 2: Simple job creation
    job_ok = test_simple_job()
    
    print("\n" + "=" * 50)
    if health_ok and job_ok:
        print("🎉 All basic tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    main()
