#!/usr/bin/env python3
"""
Script to recalculate qualification scores for all existing applications
using the actual similarity scoring system
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import sys
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def recalculate_all_qualifications():
    """Recalculate qualification scores for all existing applications"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database successfully")
        
        # Get all applications that need qualification scores
        print("📊 Fetching applications to recalculate...")
        applications = await conn.fetch("""
            SELECT a.id, a.candidate_id, a.job_id, a.status, a.candidate_score, a.is_qualified
            FROM applications a
            WHERE a.candidate_score IS NULL OR a.is_qualified IS NULL
            ORDER BY a.id
        """)
        
        print(f"📋 Found {len(applications)} applications to recalculate")
        
        if not applications:
            print("✅ All applications already have qualification scores")
            await conn.close()
            return True
        
        # Import the qualification service
        from services.qualification_service import qualification_service
        from config.database import get_db_session
        
        # Process each application
        success_count = 0
        error_count = 0
        
        for app in applications:
            try:
                app_id = app['id']
                candidate_id = app['candidate_id']
                job_id = app['job_id']
                
                print(f"🔄 Processing Application #{app_id} (Candidate: {candidate_id}, Job: {job_id})")
                
                # Get a database session
                async for db in get_db_session():
                    # Calculate the real similarity score
                    candidate_score = await qualification_service.calculate_candidate_score(
                        db, candidate_id, job_id
                    )
                    
                    if candidate_score is not None:
                        # Get job threshold
                        threshold = await qualification_service.get_job_threshold(db, job_id)
                        
                        # Determine qualification
                        is_qualified = candidate_score >= threshold
                        
                        # Determine new status
                        if is_qualified:
                            new_status = 'interview_scheduled'
                        else:
                            new_status = 'rejected'
                        
                        # Update the application
                        await conn.execute("""
                            UPDATE applications 
                            SET 
                                candidate_score = :candidate_score,
                                is_qualified = :is_qualified,
                                status = :status,
                                updated_at = NOW()
                            WHERE id = :app_id
                        """, {
                            "candidate_score": candidate_score,
                            "is_qualified": is_qualified,
                            "status": new_status,
                            "app_id": app_id
                        })
                        
                        print(f"✅ Application #{app_id}: Score={candidate_score:.1f}%, Qualified={is_qualified}, Status={new_status}")
                        success_count += 1
                    else:
                        print(f"⚠️  Application #{app_id}: Could not calculate score")
                        error_count += 1
                    
                    break  # Exit the async generator
                    
            except Exception as e:
                print(f"❌ Error processing Application #{app['id']}: {e}")
                error_count += 1
                continue
        
        # Summary
        print(f"\n📊 Recalculation Summary:")
        print(f"   ✅ Successfully processed: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📋 Total applications: {len(applications)}")
        
        # Close connection
        await conn.close()
        print("🔌 Database connection closed")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error recalculating qualifications: {e}")
        return False

async def verify_qualification_data():
    """Verify that qualification data was updated correctly"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        conn = await asyncpg.connect(database_url)
        
        print("\n🔍 Verifying qualification data...")
        
        # Check qualification statistics
        stats = await conn.fetch("""
            SELECT 
                COUNT(*) as total_applications,
                COUNT(CASE WHEN candidate_score IS NOT NULL THEN 1 END) as with_scores,
                COUNT(CASE WHEN is_qualified = true THEN 1 END) as qualified_count,
                COUNT(CASE WHEN is_qualified = false THEN 1 END) as rejected_count,
                AVG(candidate_score) as avg_score,
                MIN(candidate_score) as min_score,
                MAX(candidate_score) as max_score
            FROM applications
        """)
        
        if stats:
            stat = stats[0]
            print(f"📊 Qualification Statistics:")
            print(f"   Total Applications: {stat['total_applications']}")
            print(f"   With Scores: {stat['with_scores']}")
            print(f"   Qualified: {stat['qualified_count']}")
            print(f"   Rejected: {stat['rejected_count']}")
            print(f"   Average Score: {stat['avg_score']:.1f}%" if stat['avg_score'] else "   Average Score: N/A")
            print(f"   Score Range: {stat['min_score']:.1f}% - {stat['max_score']:.1f}%" if stat['min_score'] else "   Score Range: N/A")
        
        # Show some sample applications
        print(f"\n📋 Sample Applications:")
        samples = await conn.fetch("""
            SELECT a.id, a.candidate_score, a.is_qualified, a.status, c.name, j.title
            FROM applications a
            LEFT JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE a.candidate_score IS NOT NULL
            ORDER BY a.candidate_score DESC
            LIMIT 5
        """)
        
        for sample in samples:
            qualified_icon = "✅" if sample['is_qualified'] else "❌"
            print(f"   #{sample['id']}: {sample['candidate_score']:.1f}% {qualified_icon} {sample['name']} -> {sample['title']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting qualification recalculation...")
    print("=" * 60)
    
    # Run the recalculation
    success = asyncio.run(recalculate_all_qualifications())
    
    if success:
        # Verify the results
        asyncio.run(verify_qualification_data())
        print("\n🎉 Qualification recalculation completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Refresh your frontend to see the updated scores")
        print("   2. Check the qualification filters in the sidebar")
        print("   3. Verify that qualified candidates show green badges")
    else:
        print("\n❌ Qualification recalculation failed. Please check the error messages above.")



