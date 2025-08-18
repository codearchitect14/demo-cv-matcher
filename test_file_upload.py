#!/usr/bin/env python3
"""
Test script for file upload functionality
"""
import requests
import os

def test_file_upload():
    """Test file upload with different file sizes"""
    
    # Test files
    test_files = [
        ("sample_cv_minimal.csv", "text/csv"),
        ("sample_cv_single.csv", "text/csv"),
        ("sample_cv_simple.csv", "text/csv")
    ]
    
    # API endpoint
    url = "http://localhost:8000/api/v1/candidates/upload-cv"
    
    # You'll need to get a valid token first
    # For testing, you can temporarily disable authentication in the endpoint
    
    for filename, content_type in test_files:
        if os.path.exists(filename):
            print(f"\nTesting upload of {filename}...")
            
            try:
                with open(filename, 'rb') as f:
                    files = {'cv_file': (filename, f, content_type)}
                    
                    # For testing without authentication, you might need to modify the endpoint temporarily
                    response = requests.post(url, files=files)
                    
                    print(f"Status Code: {response.status_code}")
                    print(f"Response: {response.text}")
                    
                    if response.status_code == 200:
                        print(f"✅ Successfully uploaded {filename}")
                    else:
                        print(f"❌ Failed to upload {filename}")
                        
            except Exception as e:
                print(f"❌ Error uploading {filename}: {e}")
        else:
            print(f"❌ File {filename} not found")

if __name__ == "__main__":
    print("Testing file upload functionality...")
    test_file_upload()
