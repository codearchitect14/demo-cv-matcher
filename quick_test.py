#!/usr/bin/env python3
import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from config.database import get_db_session

async def quick_test():
    async for db in get_db_session():
        try:
            # Check if there are any interactions
            result = await db.execute(text("SELECT COUNT(*) FROM interaction_log"))
            count = result.scalar()
            print(f"Current interactions: {count}")
            
            if count == 0:
                print("No interactions found. Adding test data...")
                
                # Get candidates and jobs
                result = await db.execute(text("SELECT id FROM candidates LIMIT 2"))
                candidates = result.fetchall()
                
                result = await db.execute(text("SELECT id FROM jobs LIMIT 2"))
                jobs = result.fetchall()
                
                if candidates and jobs:
                    # Add test interactions
                    for i, candidate in enumerate(candidates):
                        for j, job in enumerate(jobs):
                            interaction_type = ['viewed', 'applied', 'rejected'][(i + j) % 3]
                            timestamp = datetime.now() - timedelta(days=(i + j) % 30)
                            
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
                    print("Test interactions added!")
                    
                    # Verify
                    result = await db.execute(text("SELECT COUNT(*) FROM interaction_log"))
                    new_count = result.scalar()
                    print(f"New total: {new_count}")
                else:
                    print("No candidates or jobs found!")
            else:
                print("Interactions already exist")
                
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(quick_test())
