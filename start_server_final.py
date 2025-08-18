#!/usr/bin/env python3
"""
Final startup script for CV Matcher API with large file upload support
"""
import uvicorn
import os

if __name__ == "__main__":
    # Set environment variables for large file uploads
    os.environ["UVICORN_MAX_CONTENT_SIZE"] = "52428800"  # 50MB
    os.environ["STARLETTE_MAX_CONTENT_SIZE"] = "52428800"  # 50MB
    os.environ["ASGI_MAX_CONTENT_SIZE"] = "52428800"  # 50MB
    
    print("🚀 Starting CV Matcher API with large file upload support...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📁 File upload limit: 50MB")
    print("✅ Ready for CV uploads!")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
