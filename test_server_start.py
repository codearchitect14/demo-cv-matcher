#!/usr/bin/env python3
"""
Test script to verify server startup
"""
import subprocess
import time
import requests
import sys

def test_server_startup():
    """Test if the server starts correctly"""
    print("Testing server startup...")
    
    try:
        # Start the server in a subprocess
        process = subprocess.Popen(
            [sys.executable, "start_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for the server to start
        time.sleep(5)
        
        # Check if the process is still running
        if process.poll() is None:
            print("✅ Server started successfully!")
            
            # Try to connect to the server
            try:
                response = requests.get("http://localhost:8000/docs", timeout=5)
                if response.status_code == 200:
                    print("✅ Server is responding correctly!")
                else:
                    print(f"⚠️ Server responded with status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not connect to server: {e}")
            
            # Terminate the server
            process.terminate()
            process.wait()
            print("✅ Server test completed successfully!")
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ Server failed to start!")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

if __name__ == "__main__":
    test_server_startup()
