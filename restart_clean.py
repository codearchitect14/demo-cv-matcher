#!/usr/bin/env python3
"""
Clean server restart script
"""
import os
import sys
import subprocess
import time
import signal

def kill_existing_server():
    """Kill any existing server process"""
    try:
        # Find and kill processes on port 8000
        if os.name == 'nt':  # Windows
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if ':8000' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        try:
                            subprocess.run(['taskkill', '/PID', pid, '/F'], check=True)
                            print(f"✅ Killed process {pid} on port 8000")
                        except:
                            pass
        else:  # Linux/Mac
            subprocess.run(['pkill', '-f', 'uvicorn'], check=False)
            print("✅ Killed existing uvicorn processes")
    except Exception as e:
        print(f"⚠️ Could not kill existing processes: {e}")

def start_server():
    """Start the server"""
    print("🚀 Starting CV Matcher API server...")
    print("📝 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📁 File upload limit: 100MB")
    print("=" * 50)
    
    # Set environment variables
    os.environ["UVICORN_MAX_CONTENT_SIZE"] = "104857600"  # 100MB
    os.environ["STARLETTE_MAX_CONTENT_SIZE"] = "104857600"  # 100MB
    
    # Start the server
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "info"
    ])

if __name__ == "__main__":
    print("🔄 Clean Server Restart")
    print("=" * 30)
    
    # Kill existing server
    kill_existing_server()
    
    # Wait a moment
    time.sleep(2)
    
    # Start new server
    start_server() 