#!/usr/bin/env python3
"""
Simple test script to verify basic functionality
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
        print(f"Health check response: {data}")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_simple_job_creation():
    """Test simple job creation without mandatory skills"""
    print("\nTesting simple job creation...")
    
    job_data = {
        "title": "Test Job",
        "company": "Test Company",
        "location": "Remote",
        "salary_min": 50000,
        "salary_max": 100000,
        "domain": "Software",
        "total_years_required": 2,
        "job_description": "A simple test job for debugging.",
        "mandatory_skills": []  # Empty to avoid prepared statement issues
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/jobs/public", json=job_data, timeout=30)
        response.raise_for_status()
        job = response.json()
        print(f"Successfully created job: {job['title']} (ID: {job['id']})")
        return job
    except Exception as e:
        print(f"Job creation failed: {e}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None

def main():
    print(f"Simple test against {API_BASE_URL}")
    
    # Test 1: Health check
    if not test_health():
        print("API is not healthy. Exiting.")
        return
    
    # Test 2: Simple job creation
    job = test_simple_job_creation()
    if job:
        print("✅ Basic functionality test passed!")
    else:
        print("❌ Basic functionality test failed!")
    
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    main()
