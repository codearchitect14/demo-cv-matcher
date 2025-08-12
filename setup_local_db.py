#!/usr/bin/env python3
"""
Setup local PostgreSQL database for testing
"""
import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_postgres_installed():
    """Check if PostgreSQL is installed"""
    print("🔍 Checking PostgreSQL installation...")
    
    try:
        result = subprocess.run(["psql", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL is installed")
            print(f"   Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ PostgreSQL not found")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL not found in PATH")
        return False

def setup_local_env():
    """Setup local environment variables"""
    print("\n🔧 Setting up local database configuration...")
    
    # Create local .env.local file
    local_env_content = """# Local Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/job_matcher
DB_HOST=localhost
DB_PORT=5432
DB_NAME=job_matcher
DB_USER=postgres
DB_PASSWORD=password

# Application Settings
DEBUG=True
SECRET_KEY=local-secret-key-for-testing
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: Logging
LOG_LEVEL=INFO
"""
    
    try:
        with open(".env.local", "w") as f:
            f.write(local_env_content)
        print("✅ Created .env.local file")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env.local: {e}")
        return False

def create_database():
    """Create the local database"""
    print("\n🔄 Creating local database...")
    
    try:
        # Create database
        result = subprocess.run([
            "psql", "-U", "postgres", "-h", "localhost", 
            "-c", "CREATE DATABASE job_matcher;"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database 'job_matcher' created successfully")
            return True
        else:
            print(f"⚠️  Database creation result: {result.stderr}")
            # Database might already exist
            return True
            
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def install_postgres_instructions():
    """Show instructions for installing PostgreSQL"""
    print("\n📋 PostgreSQL Installation Instructions:")
    print("=" * 50)
    print("1. Download PostgreSQL from: https://www.postgresql.org/download/")
    print("2. Install with default settings")
    print("3. Remember the password you set for 'postgres' user")
    print("4. Add PostgreSQL bin directory to your PATH")
    print("5. Restart your terminal/command prompt")
    print("=" * 50)

def main():
    """Main setup function"""
    print("🚀 Setting up Local PostgreSQL Database")
    print("=" * 50)
    
    # Check if PostgreSQL is installed
    pg_installed = check_postgres_installed()
    
    if not pg_installed:
        install_postgres_instructions()
        return
    
    # Setup local environment
    env_ok = setup_local_env()
    if not env_ok:
        return
    
    # Create database
    db_ok = create_database()
    
    if db_ok:
        print("\n🎉 Local database setup completed!")
        print("\n📋 Next steps:")
        print("1. Copy .env.local to .env (or update your .env with local settings)")
        print("2. Run: python test_supabase_connection.py")
        print("3. Your app will now use local PostgreSQL instead of Supabase")
    else:
        print("\n❌ Database setup failed!")
        print("Please check PostgreSQL installation and try again")

if __name__ == "__main__":
    main() 