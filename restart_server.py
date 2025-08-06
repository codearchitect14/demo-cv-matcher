#!/usr/bin/env python3
"""
Script to restart the server and clear database connections
"""

import subprocess
import sys
import time
import os
import platform

def restart_server():
    """Restart the FastAPI server"""
    
    print("🔄 Restarting FastAPI server...")
    
    try:
        # Kill any existing uvicorn processes
        print("1. Stopping existing server...")
        
        if platform.system() == "Windows":
            # Windows-specific commands
            subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
            subprocess.run(["taskkill", "/f", "/im", "uvicorn.exe"], capture_output=True)
        else:
            # Linux/Mac commands
            subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
        
        time.sleep(2)
        
        # Start the server with the new database configuration
        print("2. Starting server with updated configuration...")
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        # Use subprocess.Popen for Windows compatibility
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Check if the process is still running
        if process.poll() is None:
            print("✅ Server restarted successfully!")
            print("🌐 Server should be available at: http://localhost:8000")
            print("📊 API docs available at: http://localhost:8000/docs")
            print("\n💡 To stop the server, press Ctrl+C")
            
            # Keep the script running to show server output
            try:
                while True:
                    output = process.stdout.readline()
                    if output:
                        print(output.strip())
                    if process.poll() is not None:
                        break
            except KeyboardInterrupt:
                print("\n🛑 Stopping server...")
                process.terminate()
        else:
            # Process failed to start
            stderr_output = process.stderr.read()
            print(f"❌ Server failed to start: {stderr_output}")
        
    except Exception as e:
        print(f"❌ Failed to restart server: {e}")

if __name__ == "__main__":
    restart_server() 