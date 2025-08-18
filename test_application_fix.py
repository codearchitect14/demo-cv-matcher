#!/usr/bin/env python3
"""
Test script to verify application creation works with updated schema
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schemas.application import ApplicationCreate
from models.application import ApplicationStatusEnum

def test_application_schema():
    """Test the updated ApplicationCreate schema"""
    print("🧪 Testing ApplicationCreate Schema")
    print("=" * 40)
    
    # Test 1: Valid application with candidate_id
    try:
        app1 = ApplicationCreate(
            job_id=1,
            candidate_id=1,
            status=ApplicationStatusEnum.APPLIED
        )
        print("✅ Test 1 PASSED: Application with candidate_id")
        print(f"   job_id: {app1.job_id}")
        print(f"   candidate_id: {app1.candidate_id}")
        print(f"   status: {app1.status}")
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
    
    # Test 2: Valid application without candidate_id (should work now)
    try:
        app2 = ApplicationCreate(
            job_id=2,
            status=ApplicationStatusEnum.APPLIED
        )
        print("✅ Test 2 PASSED: Application without candidate_id")
        print(f"   job_id: {app2.job_id}")
        print(f"   candidate_id: {app2.candidate_id} (None)")
        print(f"   status: {app2.status}")
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
    
    # Test 3: Valid application with None candidate_id
    try:
        app3 = ApplicationCreate(
            job_id=3,
            candidate_id=None,
            status=ApplicationStatusEnum.APPLIED
        )
        print("✅ Test 3 PASSED: Application with None candidate_id")
        print(f"   job_id: {app3.job_id}")
        print(f"   candidate_id: {app3.candidate_id}")
        print(f"   status: {app3.status}")
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
    
    print("\n🎉 Schema tests completed!")
    print("The frontend should now be able to send requests without candidate_id")

if __name__ == "__main__":
    test_application_schema()
