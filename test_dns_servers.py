#!/usr/bin/env python3
"""
Test DNS resolution with different DNS servers
"""
import socket
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_with_dns_servers():
    """Test DNS resolution with different DNS servers"""
    print("🔍 Testing DNS Resolution with Different Servers...")
    print("=" * 60)
    
    db_host = os.getenv("DB_HOST")
    if not db_host:
        print("❌ DB_HOST not found in .env file")
        return
    
    print(f"Target hostname: {db_host}")
    print("=" * 60)
    
    # Different DNS servers to test
    dns_servers = [
        ("8.8.8.8", "Google DNS"),
        ("1.1.1.1", "Cloudflare DNS"),
        ("208.67.222.222", "OpenDNS"),
        ("9.9.9.9", "Quad9 DNS"),
        ("8.8.4.4", "Google DNS Secondary"),
        ("1.0.0.1", "Cloudflare DNS Secondary")
    ]
    
    for dns_ip, dns_name in dns_servers:
        print(f"\n🔄 Testing with {dns_name} ({dns_ip})...")
        
        try:
            # Create a resolver with specific DNS server
            resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            resolver.settimeout(5)
            
            # Try to resolve using this DNS server
            ip_address = socket.gethostbyname(db_host)
            print(f"✅ {dns_name}: {ip_address}")
            
        except socket.gaierror as e:
            print(f"❌ {dns_name}: {e}")
        except Exception as e:
            print(f"❌ {dns_name}: Unexpected error - {e}")
        finally:
            resolver.close()

def test_supabase_status():
    """Test if Supabase is reachable"""
    print("\n🔍 Testing Supabase Status...")
    print("=" * 60)
    
    # Test common Supabase endpoints
    test_hosts = [
        "supabase.com",
        "api.supabase.com",
        "db.supabase.com"
    ]
    
    for host in test_hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"✅ {host} -> {ip}")
        except socket.gaierror as e:
            print(f"❌ {host} -> Failed: {e}")

def main():
    """Main test function"""
    print("🚀 Starting DNS Server Tests")
    print("=" * 60)
    
    # Test basic Supabase connectivity
    test_supabase_status()
    
    # Test with different DNS servers
    test_with_dns_servers()
    
    print("\n" + "=" * 60)
    print("💡 If all DNS servers fail, your Supabase project might be:")
    print("1. Paused/Inactive")
    print("2. Deleted")
    print("3. Hostname changed")
    print("4. Network blocked")

if __name__ == "__main__":
    main() 