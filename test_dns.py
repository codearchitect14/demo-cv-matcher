#!/usr/bin/env python3
"""
DNS resolution test for Supabase
"""
import socket
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_dns_resolution():
    """Test DNS resolution for Supabase host"""
    print("🔍 Testing DNS Resolution...")
    print("=" * 50)
    
    # Get the host from environment
    db_host = os.getenv("DB_HOST")
    if not db_host:
        print("❌ DB_HOST not found in .env file")
        return False
    
    print(f"Testing hostname: {db_host}")
    
    try:
        # Try to resolve the hostname
        ip_address = socket.gethostbyname(db_host)
        print(f"✅ DNS Resolution successful!")
        print(f"   Hostname: {db_host}")
        print(f"   IP Address: {ip_address}")
        return True
        
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        print("\nPossible solutions:")
        print("1. Check your internet connection")
        print("2. Try using a different DNS server")
        print("3. Verify the Supabase hostname is correct")
        print("4. Check if your firewall is blocking the connection")
        return False

def test_network_connectivity():
    """Test basic network connectivity"""
    print("\n🔍 Testing Network Connectivity...")
    print("=" * 50)
    
    # Test common hosts
    test_hosts = [
        "8.8.8.8",  # Google DNS
        "1.1.1.1",  # Cloudflare DNS
        "google.com",
        "github.com"
    ]
    
    for host in test_hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"✅ {host} -> {ip}")
        except socket.gaierror as e:
            print(f"❌ {host} -> Failed: {e}")
    
    print("=" * 50)

def main():
    """Main test function"""
    print("🚀 Starting Network Diagnostics")
    print("=" * 50)
    
    # Test basic network connectivity first
    test_network_connectivity()
    
    # Test Supabase DNS resolution
    dns_ok = test_dns_resolution()
    
    if dns_ok:
        print("\n🎉 DNS resolution is working!")
        print("The issue might be with SSL or authentication")
    else:
        print("\n❌ DNS resolution failed!")
        print("Please check your internet connection and try again")

if __name__ == "__main__":
    main() 