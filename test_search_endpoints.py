#!/usr/bin/env python3
"""
Test the semantic search endpoints
"""

import requests
import json

def test_job_search():
    """Test job search endpoint"""
    print("🧪 Testing Job Search Endpoint...")
    
    url = "http://localhost:8000/api/v1/recommendations/search/jobs"
    
    payload = {
        "query": "software engineer python",
        "limit": 10,
        "apply_filters": True,
        "strict_mode": False,
        "use_ml_ranking": True
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Job search successful! Found {len(results)} jobs")
            
            for i, job in enumerate(results[:3]):
                print(f"  {i+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                print(f"     Similarity: {job.get('similarity_score', 0):.3f}")
                print(f"     Location: {job.get('location', 'N/A')}")
                print(f"     Domain: {job.get('domain', 'N/A')}")
                print()
        else:
            print(f"❌ Job search failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing job search: {e}")

def test_candidate_search():
    """Test candidate search endpoint"""
    print("\n🧪 Testing Candidate Search Endpoint...")
    
    url = "http://localhost:8000/api/v1/recommendations/search/candidates"
    
    payload = {
        "query": "experienced developer react",
        "limit": 10,
        "apply_filters": True,
        "strict_mode": False,
        "use_ml_ranking": True
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Candidate search successful! Found {len(results)} candidates")
            
            for i, candidate in enumerate(results[:3]):
                print(f"  {i+1}. {candidate.get('name', 'N/A')}")
                print(f"     Similarity: {candidate.get('similarity_score', 0):.3f}")
                print(f"     Location: {candidate.get('location', 'N/A')}")
                print(f"     Domain: {candidate.get('domain', 'N/A')}")
                print()
        else:
            print(f"❌ Candidate search failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing candidate search: {e}")

def test_without_filters():
    """Test search without filters"""
    print("\n🧪 Testing Search Without Filters...")
    
    url = "http://localhost:8000/api/v1/recommendations/search/jobs"
    
    payload = {
        "query": "python developer",
        "limit": 5,
        "apply_filters": False,
        "strict_mode": False,
        "use_ml_ranking": False
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Raw search successful! Found {len(results)} jobs")
            
            for i, job in enumerate(results[:3]):
                print(f"  {i+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                print(f"     Similarity: {job.get('similarity_score', 0):.3f}")
                print()
        else:
            print(f"❌ Raw search failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing raw search: {e}")

def main():
    """Main function"""
    print("🚀 Testing Semantic Search Endpoints...")
    
    # Test job search
    test_job_search()
    
    # Test candidate search
    test_candidate_search()
    
    # Test without filters
    test_without_filters()
    
    print("\n📋 Summary:")
    print("Check the results above to see if the search endpoints work properly")

if __name__ == "__main__":
    main() 