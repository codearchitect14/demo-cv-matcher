#!/usr/bin/env python3
"""
Simple reindexing script using direct asyncpg connection
"""

import asyncio
import sys
import os
import asyncpg
import numpy as np
from typing import List, Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from embeddings.build_index import faiss_manager
from embeddings.embedder import embedding_service
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def get_direct_connection():
    """Get direct asyncpg connection"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not found in environment")
    
    # Parse connection string
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "")
    
    # Extract connection details
    if "@" in DATABASE_URL:
        auth_part, rest = DATABASE_URL.split("@", 1)
        if ":" in auth_part:
            user, password = auth_part.split(":", 1)
        else:
            user, password = auth_part, ""
        
        if "/" in rest:
            host_port, database = rest.split("/", 1)
            if ":" in host_port:
                host, port = host_port.split(":", 1)
                port = int(port)
            else:
                host, port = host_port, 5432
        else:
            host, port, database = rest, 5432, ""
    else:
        raise ValueError("Invalid DATABASE_URL format")
    
    # Connect with minimal settings to avoid prepared statement issues
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        statement_cache_size=0,  # Disable prepared statements
        command_timeout=60,
        ssl="require" if "supabase.com" in host else False
    )
    
    return conn

async def get_jobs_data(conn):
    """Get all jobs data"""
    rows = await conn.fetch("""
        SELECT id, title, company, location, salary_min, salary_max, 
               domain, total_years_required, job_description
        FROM jobs
    """)
    
    jobs = []
    for row in rows:
        jobs.append({
            'id': row['id'],
            'title': row['title'],
            'company': row['company'],
            'location': row['location'],
            'salary_min': row['salary_min'],
            'salary_max': row['salary_max'],
            'domain': row['domain'],
            'total_years_required': row['total_years_required'],
            'job_description': row['job_description']
        })
    
    return jobs

async def get_candidates_data(conn):
    """Get all candidates data"""
    rows = await conn.fetch("""
        SELECT id, name, location, expected_salary_min, expected_salary_max, 
               domain, summary, email
        FROM candidates
    """)
    
    candidates = []
    for row in rows:
        candidates.append({
            'id': row['id'],
            'name': row['name'],
            'location': row['location'],
            'expected_salary_min': row['expected_salary_min'],
            'expected_salary_max': row['expected_salary_max'],
            'domain': row['domain'],
            'summary': row['summary'],
            'email': row['email']
        })
    
    return candidates

async def get_candidate_experiences(conn, candidate_id):
    """Get experiences for a candidate"""
    rows = await conn.fetch("""
        SELECT skill, years, description
        FROM candidate_experience
        WHERE candidate_id = $1
    """, candidate_id)
    
    experiences = []
    for row in rows:
        experiences.append({
            'skill': row['skill'],
            'years': row['years'],
            'description': row['description']
        })
    
    return experiences

async def reindex_data():
    """Reindex all data into FAISS"""
    print("🚀 Reindexing data using direct connection...")
    
    try:
        # Get direct connection
        conn = await get_direct_connection()
        print("✅ Connected to database")
        
        # 1. Clear existing index
        print("1. Clearing existing index...")
        faiss_manager.index = None
        faiss_manager.id_to_index = {}
        faiss_manager.index_to_id = {}
        faiss_manager._create_index()
        
        # 2. Get jobs data
        print("2. Getting jobs data...")
        jobs = await get_jobs_data(conn)
        print(f"Found {len(jobs)} jobs")
        
        # 3. Index jobs
        print("3. Indexing jobs...")
        job_vectors = []
        job_ids = []
        
        for job in jobs:
            # Generate job embedding
            embedding = embedding_service.generate_job_embedding(
                job_title=job['title'],
                job_description=job['job_description'] or "",
                domain=job['domain'] or ""
            )
            
            job_vectors.append(embedding)
            job_ids.append(job['id'])
        
        # Add to FAISS index
        faiss_manager.add_vectors(job_vectors, job_ids, "job")
        print(f"✅ Indexed {len(jobs)} jobs")
        
        # 4. Get candidates data
        print("4. Getting candidates data...")
        candidates = await get_candidates_data(conn)
        print(f"Found {len(candidates)} candidates")
        
        # 5. Index candidates
        print("5. Indexing candidates...")
        candidate_vectors = []
        candidate_ids = []
        
        for candidate in candidates:
            # Get candidate experiences
            experiences = await get_candidate_experiences(conn, candidate['id'])
            
            # Generate candidate embedding
            embedding = embedding_service.generate_candidate_embedding(
                summary=candidate['summary'] or "",
                experiences=experiences
            )
            
            candidate_vectors.append(embedding)
            candidate_ids.append(candidate['id'])
        
        # Add to FAISS index
        faiss_manager.add_vectors(candidate_vectors, candidate_ids, "candidate")
        print(f"✅ Indexed {len(candidates)} candidates")
        
        # 6. Save index
        print("6. Saving index...")
        faiss_manager.save_index()
        
        # 7. Verify index
        print("7. Verifying index...")
        stats = faiss_manager.get_index_stats()
        print(f"Index stats: {stats}")
        
        if stats['total_vectors'] == 0:
            print("❌ Index is still empty!")
            return False
        else:
            print(f"✅ Successfully indexed {stats['total_vectors']} vectors")
            return True
            
    except Exception as e:
        print(f"❌ Error reindexing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            await conn.close()

async def test_recommendations():
    """Test recommendations after reindexing"""
    print("\n🧪 Testing recommendations...")
    
    try:
        conn = await get_direct_connection()
        
        # Test job recommendations for candidate 2
        print("Testing job recommendations for candidate 2...")
        
        # Get candidate 2 data
        candidate_row = await conn.fetchrow("""
            SELECT id, name, summary FROM candidates WHERE id = 2
        """)
        
        if candidate_row:
            candidate = {
                'id': candidate_row['id'],
                'name': candidate_row['name'],
                'summary': candidate_row['summary']
            }
            
            # Get candidate experiences
            experiences = await get_candidate_experiences(conn, candidate['id'])
            
            # Generate candidate embedding
            candidate_embedding = embedding_service.generate_candidate_embedding(
                summary=candidate['summary'] or "",
                experiences=experiences
            )
            
            # Search for similar jobs
            job_results = faiss_manager.search(candidate_embedding, k=5, entity_type="job")
            print(f"Job recommendations: {len(job_results)}")
            for i, (job_id, score) in enumerate(job_results[:3]):
                print(f"  {i+1}. Job ID: {job_id}, Score: {score:.3f}")
        
        # Test candidate recommendations for job 2
        print("\nTesting candidate recommendations for job 2...")
        
        # Get job 2 data
        job_row = await conn.fetchrow("""
            SELECT id, title, job_description, domain FROM jobs WHERE id = 2
        """)
        
        if job_row:
            job = {
                'id': job_row['id'],
                'title': job_row['title'],
                'job_description': job_row['job_description'],
                'domain': job_row['domain']
            }
            
            # Generate job embedding
            job_embedding = embedding_service.generate_job_embedding(
                job_title=job['title'],
                job_description=job['job_description'] or "",
                domain=job['domain'] or ""
            )
            
            # Search for similar candidates
            candidate_results = faiss_manager.search(job_embedding, k=5, entity_type="candidate")
            print(f"Candidate recommendations: {len(candidate_results)}")
            for i, (candidate_id, score) in enumerate(candidate_results[:3]):
                print(f"  {i+1}. Candidate ID: {candidate_id}, Score: {score:.3f}")
        
    except Exception as e:
        print(f"❌ Error testing recommendations: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            await conn.close()

async def main():
    """Main function"""
    print("🔄 Simple Reindexing and Testing...")
    
    # Reindex all data
    success = await reindex_data()
    
    if success:
        # Test recommendations
        await test_recommendations()
        
        print("\n🎉 Reindexing complete!")
        print("Now you can test the API endpoints again.")
    else:
        print("\n❌ Reindexing failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main()) 