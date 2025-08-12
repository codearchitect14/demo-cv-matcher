#!/usr/bin/env python3
"""
Simple script to restart the server with clean database settings
"""

import subprocess
import sys
import time
import os

def restart_server():
    """Restart the FastAPI server with clean settings"""
    
    print("🔄 Restarting server with clean database settings...")
    
    try:
        # Kill any existing Python processes (be careful with this on Windows)
        print("1. Stopping existing server...")
        if os.name == 'nt':  # Windows
            subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
        else:  # Linux/Mac
            subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
        
        time.sleep(3)
        
        # Start the server
        print("2. Starting server with updated database configuration...")
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print("\n🌐 Server will be available at: http://localhost:8000")
        print("📊 API docs: http://localhost:8000/docs")
        print("💡 Press Ctrl+C to stop the server")
        
        # Start the server
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to restart server: {e}")

if __name__ == "__main__":
    restart_server() 