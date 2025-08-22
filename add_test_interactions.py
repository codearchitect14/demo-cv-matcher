#!/usr/bin/env python3
"""
Script to add test interactions to the database for testing analytics
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from config.database import get_db
from models.interaction import InteractionTypeEnum

async def add_test_interactions():
    """Add test interactions to the database"""
    async for db in get_db():
        try:
            # First, let's check if we have any candidates and jobs
            result = await db.execute(text("SELECT id FROM candidates LIMIT 5"))
            candidates = result.fetchall()
            
            result = await db.execute(text("SELECT id FROM jobs LIMIT 5"))
            jobs = result.fetchall()
            
            if not candidates or not jobs:
                print("No candidates or jobs found in database")
                return
            
            print(f"Found {len(candidates)} candidates and {len(jobs)} jobs")
            
            # Add some test interactions
            interaction_types = ['viewed', 'applied', 'rejected']
            
            for i, candidate in enumerate(candidates):
                for j, job in enumerate(jobs):
                    # Add different types of interactions
                    interaction_type = interaction_types[(i + j) % len(interaction_types)]
                    
                    # Create timestamp within last 30 days
                    days_ago = (i + j) % 30
                    timestamp = datetime.now() - timedelta(days=days_ago)
                    
                    sql = text("""
                        INSERT INTO interaction_log (user_id, user_type, job_id, interaction_type, timestamp, created_at, updated_at)
                        VALUES (:user_id, :user_type, :job_id, :interaction_type, :timestamp, :created_at, :updated_at)
                        ON CONFLICT DO NOTHING
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
            
            # Verify the interactions were added
            result = await db.execute(text("SELECT COUNT(*) FROM interaction_log"))
            count = result.scalar()
            print(f"Total interactions in database: {count}")
            
        except Exception as e:
            print(f"Error adding test interactions: {e}")
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(add_test_interactions())
