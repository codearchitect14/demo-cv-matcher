#!/usr/bin/env python3
"""
Script to check and add test interactions to the database
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from config.database import get_db

async def check_and_add_interactions():
    """Check if there are interactions and add some if needed"""
    async for db in get_db():
        try:
            # Check if there are any interactions
            result = await db.execute(text("SELECT COUNT(*) FROM interaction_log"))
            total_interactions = result.scalar()
            print(f"Total interactions in database: {total_interactions}")
            
            if total_interactions == 0:
                print("No interactions found. Adding test interactions...")
                
                # Get some candidates and jobs
                result = await db.execute(text("SELECT id FROM candidates LIMIT 3"))
                candidates = result.fetchall()
                
                result = await db.execute(text("SELECT id FROM jobs LIMIT 3"))
                jobs = result.fetchall()
                
                if not candidates or not jobs:
                    print("No candidates or jobs found!")
                    return
                
                print(f"Found {len(candidates)} candidates and {len(jobs)} jobs")
                
                # Add test interactions
                interaction_types = ['viewed', 'applied', 'rejected']
                
                for i, candidate in enumerate(candidates):
                    for j, job in enumerate(jobs):
                        interaction_type = interaction_types[(i + j) % len(interaction_types)]
                        days_ago = (i + j) % 30
                        timestamp = datetime.now() - timedelta(days=days_ago)
                        
                        sql = text("""
                            INSERT INTO interaction_log (user_id, user_type, job_id, interaction_type, timestamp, created_at, updated_at)
                            VALUES (:user_id, :user_type, :job_id, :interaction_type, :timestamp, :created_at, :updated_at)
                        """)
                        
                        await db.execute(sql, {
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
                
                # Show some sample interactions
                result = await db.execute(text("""
                    SELECT i.user_id, i.interaction_type, i.timestamp, c.name as candidate_name, j.title as job_title
                    FROM interaction_log i
                    LEFT JOIN candidates c ON i.user_id = c.id
                    LEFT JOIN jobs j ON i.job_id = j.id
                    WHERE i.user_type = 'candidate'
                    LIMIT 5
                """))
                
                interactions = result.fetchall()
                print("\nSample interactions:")
                for interaction in interactions:
                    print(f"  Candidate {interaction.candidate_name} ({interaction.user_id}) - {interaction.interaction_type} - {interaction.job_title} - {interaction.timestamp}")
            else:
                print("Interactions already exist in database")
                
                # Show some existing interactions
                result = await db.execute(text("""
                    SELECT i.user_id, i.interaction_type, i.timestamp, c.name as candidate_name, j.title as job_title
                    FROM interaction_log i
                    LEFT JOIN candidates c ON i.user_id = c.id
                    LEFT JOIN jobs j ON i.job_id = j.id
                    WHERE i.user_type = 'candidate'
                    ORDER BY i.timestamp DESC
                    LIMIT 5
                """))
                
                interactions = result.fetchall()
                print("\nRecent interactions:")
                for interaction in interactions:
                    print(f"  Candidate {interaction.candidate_name} ({interaction.user_id}) - {interaction.interaction_type} - {interaction.job_title} - {interaction.timestamp}")
                
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(check_and_add_interactions())
