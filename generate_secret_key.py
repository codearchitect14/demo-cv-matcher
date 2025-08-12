#!/usr/bin/env python3
"""
Generate Secure Secret Key Script
Generates a secure SECRET_KEY for the application.
"""

import secrets
import base64

def generate_secret_key():
    """Generate a secure secret key"""
    # Generate 32 bytes of random data
    random_bytes = secrets.token_bytes(32)
    
    # Encode as base64 for URL-safe string
    secret_key = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    
    # Remove padding characters
    secret_key = secret_key.rstrip('=')
    
    return secret_key

def main():
    """Generate and display the secret key"""
    print("🔐 Generating Secure Secret Key...")
    print("=" * 50)
    
    secret_key = generate_secret_key()
    
    print(f"✅ Generated SECRET_KEY: {secret_key}")
    print("\n📝 Add this to your .env file:")
    print(f"SECRET_KEY={secret_key}")
    print("\n💡 Or set it as an environment variable:")
    print(f"export SECRET_KEY={secret_key}")
    print("\n🔒 Keep this key secure and never share it!")

if __name__ == "__main__":
    main() 