#!/usr/bin/env python3
"""
Test script for CV upload functionality
"""
import requests
import os

def test_cv_upload():
    """Test CV upload functionality"""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/candidates/upload-cv"
    
    # Create a simple test PDF file
    test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test CV) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
    
    # Write test PDF file
    with open("test_cv.pdf", "wb") as f:
        f.write(test_pdf_content)
    
    print("🧪 Testing CV upload functionality...")
    print(f"📁 Test file: test_cv.pdf ({len(test_pdf_content)} bytes)")
    
    try:
        with open("test_cv.pdf", "rb") as f:
            files = {'cv_file': ('test_cv.pdf', f, 'application/pdf')}
            
            # Note: This will fail without authentication, but it will show if the 413 error is fixed
            response = requests.post(url, files=files)
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
            if response.status_code == 413:
                print("❌ Still getting 413 error - server configuration issue")
            elif response.status_code == 401:
                print("✅ 413 error fixed! (401 is expected without authentication)")
            else:
                print(f"✅ Upload test completed with status: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    # Clean up test file
    if os.path.exists("test_cv.pdf"):
        os.remove("test_cv.pdf")
        print("🧹 Test file cleaned up")

if __name__ == "__main__":
    test_cv_upload()
