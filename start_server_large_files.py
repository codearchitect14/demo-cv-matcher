#!/usr/bin/env python3
"""
Startup script for CV Matcher API with large file upload support
"""
import uvicorn
import os

if __name__ == "__main__":
    # Set environment variable for larger request body size
    os.environ["UVICORN_MAX_CONTENT_SIZE"] = "52428800"  # 50MB in bytes
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # Increase request body size limit for file uploads
        limit_request_line=8192,
        limit_request_fields=100,
        limit_request_field_size=8192,
        # Increase timeout for large uploads
        timeout_keep_alive=60,
        timeout_graceful_shutdown=30,
        # Log level
        log_level="info",
        # Additional settings for large files
        access_log=True,
        use_colors=True
    )
