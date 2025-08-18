#!/usr/bin/env python3
"""
Simple working startup script for CV Matcher API
"""
import uvicorn
import os

if __name__ == "__main__":
    print("Starting CV Matcher API...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    
    # Set environment variables for large file uploads
    os.environ["UVICORN_MAX_CONTENT_SIZE"] = "104857600"  # 100MB
    os.environ["STARLETTE_MAX_CONTENT_SIZE"] = "104857600"  # 100MB
    
    # Start the server with only valid parameters
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
