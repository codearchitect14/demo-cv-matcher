#!/usr/bin/env python3
"""
Simple test script using asyncpg directly to bypass SQLAlchemy issues
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_database():
    """Test database connection with asyncpg directly"""
    try:
        # Get database connection parameters
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/job_matcher')

        # Remove asyncpg prefix if present and add it back with proper settings
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

        print(f"Connecting to: {database_url}")

        # Connect with pgbouncer-compatible settings
        conn = await asyncpg.connect(
            database_url,
            statement_cache_size=0,  # Disable prepared statements
            server_settings={
                'statement_timeout': '10000',
                'idle_in_transaction_session_timeout': '15000'
            }
        )

        print("✅ Connected successfully!")

        # Test basic queries
        print("\n=== Testing Basic Queries ===")

        # Check if tables exist
        result = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        print(f"Found {len(result)} tables:")
        for row in result:
            print(f"  - {row['table_name']}")

        # Check candidates table
        candidates_count = await conn.fetchval("SELECT COUNT(*) FROM candidates")
        print(f"\nCandidates in database: {candidates_count}")

        # Check interaction_log table
        try:
            interactions_count = await conn.fetchval("SELECT COUNT(*) FROM interaction_log")
            print(f"Interactions in database: {interactions_count}")

            # Check what enum values are available
            enum_values = await conn.fetch("""
                SELECT enumlabel
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'interactiontypeenum'
                ORDER BY e.enumsortorder
            """)

            print(f"Available interaction types: {[row['enumlabel'] for row in enum_values]}")

        except Exception as e:
            print(f"Error checking interactions: {e}")

            # Create interaction_log table if it doesn't exist
            print("Creating interaction_log table...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS interaction_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    user_type VARCHAR(50) DEFAULT 'candidate',
                    job_id INTEGER,
                    interaction_type interactiontypeenum NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created interaction_log table")

        # Add some test interactions
        if candidates_count > 0:
            # Get some candidates
            candidates = await conn.fetch("SELECT id FROM candidates LIMIT 3")
            candidate_ids = [c['id'] for c in candidates]

            if candidate_ids:
                print(f"\nAdding test interactions for candidates: {candidate_ids}")

                # Get available enum values first
                enum_values = await conn.fetch("""
                    SELECT enumlabel
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'interactiontypeenum'
                    ORDER BY e.enumsortorder
                """)

                valid_interaction_types = [row['enumlabel'] for row in enum_values]
                print(f"Using interaction types: {valid_interaction_types}")

                if valid_interaction_types:
                    # Get some jobs
                    try:
                        jobs = await conn.fetch("SELECT id FROM jobs LIMIT 3")
                        job_ids = [j['id'] for j in jobs] if jobs else []

                        if job_ids:
                            # Add test interactions
                            for i, candidate_id in enumerate(candidate_ids):
                                job_id = job_ids[i % len(job_ids)]
                                interaction_type = valid_interaction_types[i % len(valid_interaction_types)]

                                await conn.execute("""
                                    INSERT INTO interaction_log (user_id, user_type, job_id, interaction_type)
                                    VALUES ($1, 'candidate', $2, $3)
                                """, candidate_id, job_id, interaction_type)

                            print("✅ Added test interactions")
                        else:
                            print("⚠️ No jobs found, adding interactions without job_id")
                            for i, candidate_id in enumerate(candidate_ids):
                                interaction_type = valid_interaction_types[i % len(valid_interaction_types)]
                                await conn.execute("""
                                    INSERT INTO interaction_log (user_id, user_type, interaction_type)
                                    VALUES ($1, 'candidate', $2)
                                """, candidate_id, interaction_type)
                            print("✅ Added test interactions (without job_id)")
                    except Exception as e:
                        print(f"Error with jobs table: {e}")
                        # Add interactions without job_id
                        for i, candidate_id in enumerate(candidate_ids):
                            interaction_type = valid_interaction_types[i % len(valid_interaction_types)]
                            await conn.execute("""
                                INSERT INTO interaction_log (user_id, user_type, interaction_type)
                                VALUES ($1, 'candidate', $2)
                            """, candidate_id, interaction_type)
                        print("✅ Added test interactions (without job_id)")
                else:
                    print("❌ No valid interaction types found")

        # Verify interactions were added
        interactions_count = await conn.fetchval("SELECT COUNT(*) FROM interaction_log")
        print(f"\nTotal interactions now: {interactions_count}")

        # Show some sample interactions
        if interactions_count > 0:
            interactions = await conn.fetch("""
                SELECT id, user_id, user_type, job_id, interaction_type, timestamp
                FROM interaction_log
                ORDER BY timestamp DESC
                LIMIT 5
            """)

            print("\nRecent interactions:")
            for interaction in interactions:
                print(f"  ID: {interaction['id']}, User: {interaction['user_id']}, Type: {interaction['interaction_type']}, Time: {interaction['timestamp']}")

        await conn.close()
        print("\n✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database())
