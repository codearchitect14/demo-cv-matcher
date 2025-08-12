#!/usr/bin/env python3
"""
Simple test script to verify job creation endpoint works
"""

import requests
import json

def test_job_creation():
    """Test job creation endpoint"""
    
    # Test data
    job_data = {
        "title": "Test Python Developer",
        "company": "Test Company",
        "location": "Test Location",
        "salary_min": 50000,
        "salary_max": 80000,
        "domain": "IT",
        "total_years_required": 3,
        "job_description": "Test job description for Python development",
        "mandatory_skills": []
    }
    
    # Test the endpoint
    url = "http://localhost:8000/api/v1/jobs/"
    
    try:
        print("Testing job creation endpoint...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(job_data, indent=2)}")
        
        response = requests.post(
            url,
            json=job_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Job creation test PASSED")
        else:
            print("❌ Job creation test FAILED")
            
    except Exception as e:
        print(f"❌ Error testing job creation: {e}")

if __name__ == "__main__":
    test_job_creation() 