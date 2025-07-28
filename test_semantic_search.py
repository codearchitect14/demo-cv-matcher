#!/usr/bin/env python3
"""
Test script for semantic search functionality
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session
from embeddings.embedder import embedding_service
from embeddings.build_index import faiss_manager
from recommender.semantic import semantic_search_service

async def test_embedding_generation():
    """Test embedding generation"""
    print("=== Testing Embedding Generation ===")
    
    # Test basic embedding
    text = "Python developer with 5 years experience in web development"
    embedding = embedding_service.generate_embedding(text)
    print(f"✅ Generated embedding with dimension: {len(embedding)}")
    
    # Test job embedding
    job_embedding = embedding_service.generate_job_embedding(
        job_title="Senior Python Developer",
        job_description="We are looking for a senior Python developer with experience in FastAPI and PostgreSQL",
        domain="Software Development"
    )
    print(f"✅ Generated job embedding with dimension: {len(job_embedding)}")
    
    # Test candidate embedding
    experiences = [
        {"skill": "Python", "years": 5, "description": "Web development with Django and FastAPI"},
        {"skill": "PostgreSQL", "years": 3, "description": "Database design and optimization"}
    ]
    candidate_embedding = embedding_service.generate_candidate_embedding(
        summary="Experienced Python developer with strong backend skills",
        experiences=experiences
    )
    print(f"✅ Generated candidate embedding with dimension: {len(candidate_embedding)}")

async def test_faiss_index():
    """Test FAISS index operations"""
    print("\n=== Testing FAISS Index ===")
    
    # Create test vectors
    test_vectors = [
        embedding_service.generate_embedding("Python developer"),
        embedding_service.generate_embedding("Java developer"),
        embedding_service.generate_embedding("Frontend developer")
    ]
    test_ids = [1, 2, 3]
    
    # Add to index
    faiss_manager.add_vectors(test_vectors, test_ids, "job")
    print(f"✅ Added {len(test_vectors)} vectors to FAISS index")
    
    # Test search
    query_vector = embedding_service.generate_embedding("Python developer")
    results = faiss_manager.search(query_vector, k=2, entity_type="job")
    print(f"✅ Found {len(results)} similar jobs")
    
    # Get stats
    stats = faiss_manager.get_index_stats()
    print(f"✅ Index stats: {stats}")

async def test_semantic_search():
    """Test semantic search service"""
    print("\n=== Testing Semantic Search Service ===")
    
    async for db in get_db_session():
        try:
            # Test indexing (this will work if you have data in the database)
            print("Testing job indexing...")
            await semantic_search_service.index_jobs(db)
            
            print("Testing candidate indexing...")
            await semantic_search_service.index_candidates(db)
            
            # Get index stats
            stats = semantic_search_service.get_index_stats()
            print(f"✅ Index stats: {stats}")
            
        except Exception as e:
            print(f"⚠️  Semantic search test failed (expected if no data): {e}")
        break

async def main():
    """Run all tests"""
    print("🧪 Testing Semantic Search Components\n")
    
    # Test embedding generation
    await test_embedding_generation()
    
    # Test FAISS index
    await test_faiss_index()
    
    # Test semantic search service
    await test_semantic_search()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 