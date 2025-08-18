#!/usr/bin/env python3
"""
Fixed startup script for CV Matcher API with large file upload support
"""
import uvicorn
import os

if __name__ == "__main__":
    # Set environment variables for large file uploads
    os.environ["UVICORN_MAX_CONTENT_SIZE"] = "52428800"  # 50MB
    os.environ["STARLETTE_MAX_CONTENT_SIZE"] = "52428800"  # 50MB
    
    print("Starting CV Matcher API with large file upload support...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("File upload limit: 50MB")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        # Increase request limits
        limit_request_line=8192,
        limit_request_fields=100,
        limit_request_field_size=8192,
        # Increase timeouts
        timeout_keep_alive=60,
        timeout_graceful_shutdown=30
    )
