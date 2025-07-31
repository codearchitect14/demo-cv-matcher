#!/usr/bin/env python3
"""
Create All Tables in Supabase Database
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def create_all_tables():
    """Create all tables in the database"""
    print("🚀 Creating All Tables in Supabase Database")
    print("=" * 60)
    
    try:
        # Import database configuration
        from config.database import engine, Base
        # Import all models
        from models import (
            BaseModel, Candidate, CandidateExperience, 
            Job, JobMandatorySkill, Application, InteractionLog
        )
        
        print("📋 Models found:")
        print("   - BaseModel")
        print("   - Candidate")
        print("   - CandidateExperience")
        print("   - Job")
        print("   - JobMandatorySkill")
        print("   - Application")
        print("   - InteractionLog")
        
        print("\n🔄 Creating tables...")
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ All tables created successfully!")
        
        # List created tables
        await list_tables()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

async def list_tables():
    """List all tables in the database"""
    print("\n📋 Tables in database:")
    print("=" * 40)
    
    try:
        from config.database import engine
        
        async with engine.begin() as conn:
            # Get all tables
            result = await conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
            )
            tables = result.fetchall()
            
            if tables:
                for table in tables:
                    print(f"   ✅ {table[0]}")
            else:
                print("   ⚠️  No tables found")
                
    except Exception as e:
        print(f"❌ Error listing tables: {e}")

async def check_table_structure():
    """Check the structure of created tables"""
    print("\n🔍 Checking Table Structure:")
    print("=" * 40)
    
    try:
        from config.database import engine
        
        async with engine.begin() as conn:
            # Check each table structure
            tables_to_check = [
                "candidates", "candidate_experience", "jobs", 
                "job_mandatory_skills", "applications", "interaction_log"
            ]
            
            for table in tables_to_check:
                try:
                    result = await conn.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position")
                    columns = result.fetchall()
                    
                    if columns:
                        print(f"\n📋 {table}:")
                        for col in columns:
                            print(f"   - {col[0]}: {col[1]}")
                    else:
                        print(f"\n⚠️  {table}: Table not found")
                        
                except Exception as e:
                    print(f"\n❌ Error checking {table}: {e}")
                    
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")

async def test_data_insertion():
    """Test inserting sample data"""
    print("\n🧪 Testing Data Insertion:")
    print("=" * 40)
    
    try:
        from config.database import AsyncSessionLocal
        from models import Candidate, Job
        
        async with AsyncSessionLocal() as session:
            # Test candidate insertion
            test_candidate = Candidate(
                name="Test Candidate",
                location="Test City",
                domain="Technology",
                email="test@example.com",
                consent_given=True
            )
            session.add(test_candidate)
            await session.commit()
            print("✅ Test candidate created")
            
            # Test job insertion
            test_job = Job(
                title="Test Job",
                company="Test Company",
                location="Test City",
                domain="Technology",
                job_description="Test job description",
                total_years_required=2
            )
            session.add(test_job)
            await session.commit()
            print("✅ Test job created")
            
            # Clean up test data
            await session.delete(test_candidate)
            await session.delete(test_job)
            await session.commit()
            print("✅ Test data cleaned up")
            
    except Exception as e:
        print(f"❌ Error testing data insertion: {e}")

def show_table_schema():
    """Show the expected table schema"""
    print("\n📋 Expected Table Schema:")
    print("=" * 40)
    
    schema_info = {
        "candidates": [
            "id (SERIAL PRIMARY KEY)",
            "name (VARCHAR(100))",
            "location (VARCHAR(100))",
            "password_hash (VARCHAR(255))",
            "expected_salary_min (INTEGER)",
            "expected_salary_max (INTEGER)",
            "domain (VARCHAR(100))",
            "summary (TEXT)",
            "email (VARCHAR(255) UNIQUE)",
            "consent_given (BOOLEAN)",
            "created_at (TIMESTAMP)",
            "updated_at (TIMESTAMP)"
        ],
        "candidate_experience": [
            "id (SERIAL PRIMARY KEY)",
            "candidate_id (INTEGER FOREIGN KEY)",
            "skill (VARCHAR(100))",
            "years (INTEGER)",
            "description (TEXT)",
            "created_at (TIMESTAMP)",
            "updated_at (TIMESTAMP)"
        ],
        "jobs": [
            "id (SERIAL PRIMARY KEY)",
            "title (VARCHAR(255))",
            "company (VARCHAR(100))",
            "location (VARCHAR(100))",
            "salary_min (INTEGER)",
            "salary_max (INTEGER)",
            "domain (VARCHAR(100))",
            "total_years_required (INTEGER)",
            "job_description (TEXT)",
            "created_at (TIMESTAMP)",
            "updated_at (TIMESTAMP)"
        ],
        "job_mandatory_skills": [
            "id (SERIAL PRIMARY KEY)",
            "job_id (INTEGER FOREIGN KEY)",
            "skill (VARCHAR(100))",
            "min_years_required (INTEGER)",
            "created_at (TIMESTAMP)",
            "updated_at (TIMESTAMP)"
        ],
        "applications": [
            "id (SERIAL PRIMARY KEY)",
            "job_id (INTEGER FOREIGN KEY)",
            "candidate_id (INTEGER FOREIGN KEY)",
            "status (ENUM)",
            "created_at (TIMESTAMP)",
            "updated_at (TIMESTAMP)"
        ],
        "interaction_log": [
            "id (SERIAL PRIMARY KEY)",
            "user_id (INTEGER FOREIGN KEY)",
            "job_id (INTEGER FOREIGN KEY)",
            "interaction_type (ENUM)",
            "timestamp (TIMESTAMP)",
            "created_at (TIMESTAMP)",
            "updated_at (TIMESTAMP)"
        ]
    }
    
    for table, columns in schema_info.items():
        print(f"\n📋 {table}:")
        for column in columns:
            print(f"   - {column}")

async def main():
    """Main function"""
    print("🚀 Supabase Database Table Creation")
    print("=" * 60)
    
    # Show expected schema
    show_table_schema()
    
    # Create tables
    success = await create_all_tables()
    
    if success:
        # Check table structure
        await check_table_structure()
        
        # Test data insertion
        await test_data_insertion()
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! All tables created in Supabase!")
        print("✅ Your database is ready for use!")
        print("✅ You can now run your FastAPI application:")
        print("   python -m uvicorn api.main:app --reload")
    else:
        print("\n❌ Failed to create tables")
        print("Please check your database connection")

if __name__ == "__main__":
    asyncio.run(main()) 