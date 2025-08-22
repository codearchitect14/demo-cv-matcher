#!/usr/bin/env python3
import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from config.database import get_db_session

async def debug_interactions():
    async for db in get_db_session():
        try:
            print("=== Database Debug ===")
            
            # Check table structure
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'interaction_log'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print("\nTable structure:")
            for col in columns:
                print(f"  {col.column_name}: {col.data_type} (nullable: {col.is_nullable}, default: {col.column_default})")
            
            # Check current data
            result = await db.execute(text("SELECT COUNT(*) FROM interaction_log"))
            count = result.scalar()
            print(f"\nCurrent interactions: {count}")
            
            if count == 0:
                print("\nNo interactions found. Adding test data...")
                
                # Check if we have candidates and jobs
                result = await db.execute(text("SELECT COUNT(*) FROM candidates"))
                candidate_count = result.scalar()
                print(f"Candidates in database: {candidate_count}")
                
                result = await db.execute(text("SELECT COUNT(*) FROM jobs"))
                job_count = result.scalar()
                print(f"Jobs in database: {job_count}")
                
                if candidate_count > 0 and job_count > 0:
                    # Get sample data
                    result = await db.execute(text("SELECT id, name FROM candidates LIMIT 2"))
                    candidates = result.fetchall()
                    print(f"Sample candidates: {[(c.id, c.name) for c in candidates]}")
                    
                    result = await db.execute(text("SELECT id, title FROM jobs LIMIT 2"))
                    jobs = result.fetchall()
                    print(f"Sample jobs: {[(j.id, j.title) for j in jobs]}")
                    
                    # Add test interactions
                    for i, candidate in enumerate(candidates):
                        for j, job in enumerate(jobs):
                            interaction_type = ['viewed', 'applied', 'rejected'][(i + j) % 3]
                            timestamp = datetime.now() - timedelta(days=(i + j) % 30)
                            
                            print(f"Adding interaction: Candidate {candidate.id} -> Job {job.id} ({interaction_type})")
                            
                            await db.execute(text("""
                                INSERT INTO interaction_log (user_id, user_type, job_id, interaction_type, timestamp, created_at, updated_at)
                                VALUES (:user_id, :user_type, :job_id, :interaction_type, :timestamp, :created_at, :updated_at)
                            """), {
                                "user_id": candidate.id,
                                "user_type": "candidate",
                                "job_id": job.id,
                                "interaction_type": interaction_type,
                                "timestamp": timestamp,
                                "created_at": timestamp,
                                "updated_at": timestamp
                            })
                    
                    await db.commit()
                    print("Test interactions added successfully!")
                    
                    # Verify
                    result = await db.execute(text("SELECT COUNT(*) FROM interaction_log"))
                    new_count = result.scalar()
                    print(f"New total interactions: {new_count}")
                    
                    # Show sample interactions
                    result = await db.execute(text("""
                        SELECT i.user_id, i.user_type, i.interaction_type, i.timestamp, c.name as candidate_name, j.title as job_title
                        FROM interaction_log i
                        LEFT JOIN candidates c ON i.user_id = c.id
                        LEFT JOIN jobs j ON i.job_id = j.id
                        LIMIT 5
                    """))
                    interactions = result.fetchall()
                    print("\nSample interactions:")
                    for interaction in interactions:
                        print(f"  {interaction.candidate_name} ({interaction.user_id}) - {interaction.user_type} - {interaction.interaction_type} - {interaction.job_title} - {interaction.timestamp}")
                else:
                    print("No candidates or jobs found in database!")
            else:
                print("Interactions already exist")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(debug_interactions())
