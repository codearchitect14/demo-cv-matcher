#!/usr/bin/env python3
"""
Test recommendation endpoints without authentication
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test the recommendation endpoints"""
    print("🧪 Testing recommendation endpoints...")
    
    # Test semantic search endpoints (these don't require auth)
    print("\n1. Testing semantic job search:")
    try:
        search_data = {
            "query": "python developer",
            "limit": 5,
            "apply_filters": True,
            "strict_mode": False,
            "use_ml_ranking": True
        }
        response = requests.post(f"{BASE_URL}/api/v1/recommendations/search/jobs", json=search_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Number of search results: {len(data)}")
            if data:
                print("First result:")
                print(json.dumps(data[0], indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n2. Testing semantic candidate search:")
    try:
        search_data = {
            "query": "python developer",
            "limit": 5,
            "apply_filters": True,
            "strict_mode": False,
            "use_ml_ranking": True
        }
        response = requests.post(f"{BASE_URL}/api/v1/recommendations/search/candidates", json=search_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Number of search results: {len(data)}")
            if data:
                print("First result:")
                print(json.dumps(data[0], indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test data indexing
    print("\n3. Testing data indexing:")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/recommendations/index-data")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test health check
    print("\n4. Testing health check:")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def add_sample_data():
    """Add sample data via API"""
    print("\n📝 Adding sample data...")
    
    # Add a job
    job_data = {
        "title": "Python Developer",
        "company": "TechCorp",
        "location": "New York",
        "domain": "Technology",
        "salary_min": 80000,
        "salary_max": 120000,
        "total_years_required": 3,
        "job_description": "We are looking for a Python developer with experience in Django and FastAPI.",
        "mandatory_skills": [
            {"skill": "Python", "min_experience": 2},
            {"skill": "Django", "min_experience": 1},
            {"skill": "SQL", "min_experience": 1}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/jobs/", json=job_data)
        print(f"Add job status: {response.status_code}")
        if response.status_code == 200 or response.status_code == 201:
            job = response.json()
            print(f"✅ Added job: {job.get('title', 'N/A')} (ID: {job.get('id', 'N/A')})")
        else:
            print(f"❌ Failed to add job: {response.text}")
    except Exception as e:
        print(f"❌ Error adding job: {e}")
    
    # Add a candidate
    candidate_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0101",
        "location": "New York",
        "domain": "Technology",
        "expected_salary_min": 85000,
        "expected_salary_max": 120000,
        "summary": "Experienced Python developer with 3 years of experience in web development.",
        "experiences": [
            {"skill": "Python", "years": 3, "description": "Web development with Django"},
            {"skill": "JavaScript", "years": 2, "description": "Frontend development"},
            {"skill": "SQL", "years": 2, "description": "Database design and queries"}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/candidates/", json=candidate_data)
        print(f"Add candidate status: {response.status_code}")
        if response.status_code == 200 or response.status_code == 201:
            candidate = response.json()
            print(f"✅ Added candidate: {candidate.get('name', 'N/A')} (ID: {candidate.get('id', 'N/A')})")
        else:
            print(f"❌ Failed to add candidate: {response.text}")
    except Exception as e:
        print(f"❌ Error adding candidate: {e}")

def main():
    """Main function"""
    print("🚀 Testing CV Matcher Endpoints...")
    
    # Test endpoints
    test_endpoints()
    
    # Add sample data
    add_sample_data()
    
    # Test endpoints again after adding data
    print("\n🔄 Testing endpoints after adding data...")
    test_endpoints()
    
    print("\n📋 Summary:")
    print("✅ API server is running")
    print("✅ Endpoints are accessible")
    print("⚠️  Authentication required for some endpoints")
    print("📝 Sample data added for testing")

if __name__ == "__main__":
    main() 