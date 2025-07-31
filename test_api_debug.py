#!/usr/bin/env python3
"""
Debug script to test the API call step by step
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session
from recommender.semantic import semantic_search_service
from embeddings.build_index import faiss_manager
from embeddings.embedder import embedding_service
from db.crud.candidate import candidate as candidate_crud

async def debug_api_call():
    """Debug the API call step by step"""
    print("🔍 Debugging API call...")
    
    async for db in get_db_session():
        try:
            candidate_id = 2
            
            # 1. Check if candidate exists
            print("1. Checking candidate...")
            candidate = await candidate_crud.get_with_experiences(db, id=candidate_id)
            if not candidate:
                print("❌ Candidate not found")
                return
            print(f"✅ Candidate found: {candidate.name}")
            
            # 2. Check FAISS index stats
            print("\n2. Checking FAISS index...")
            stats = faiss_manager.get_index_stats()
            print(f"Index stats: {stats}")
            
            if stats['total_vectors'] == 0:
                print("❌ FAISS index is empty!")
                return
            
            # 3. Generate candidate embedding
            print("\n3. Generating candidate embedding...")
            experiences = []
            for exp in candidate.experiences:
                experiences.append({
                    "skill": exp.skill,
                    "years": exp.years,
                    "description": exp.description or ""
                })
            
            candidate_embedding = embedding_service.generate_candidate_embedding(
                summary=candidate.summary or "",
                experiences=experiences
            )
            print(f"✅ Candidate embedding shape: {candidate_embedding.shape}")
            
            # 4. Test direct FAISS search
            print("\n4. Testing direct FAISS search...")
            job_results = faiss_manager.search(candidate_embedding, k=5, entity_type="job")
            print(f"Direct FAISS results: {len(job_results)}")
            for i, (job_id, score) in enumerate(job_results[:3]):
                print(f"  {i+1}. Job ID: {job_id}, Score: {score:.3f}")
            
            # 5. Test semantic search service
            print("\n5. Testing semantic search service...")
            semantic_results = await semantic_search_service.find_similar_jobs(
                candidate_id, db, k=5, apply_filters=False, strict_mode=False, use_ml_ranking=False
            )
            print(f"Semantic search results: {len(semantic_results)}")
            for i, result in enumerate(semantic_results[:3]):
                print(f"  {i+1}. Job ID: {result.get('job_id')}, Score: {result.get('similarity_score', 0):.3f}")
            
            # 6. Test with different parameters
            print("\n6. Testing with different search parameters...")
            
            # Test with higher k
            high_k_results = faiss_manager.search(candidate_embedding, k=10, entity_type="job")
            print(f"High k results: {len(high_k_results)}")
            
            # Test without entity type filter
            all_results = faiss_manager.search(candidate_embedding, k=10)
            print(f"All entity results: {len(all_results)}")
            
            # 7. Check if there are any jobs in the index
            print("\n7. Checking job entities in index...")
            job_entities = 0
            for faiss_idx in range(faiss_manager.index.ntotal):
                entity_info = faiss_manager.index_to_id.get(faiss_idx)
                if entity_info and entity_info["type"] == "job":
                    job_entities += 1
            print(f"Job entities in index: {job_entities}")
            
        except Exception as e:
            print(f"❌ Error debugging: {e}")
            import traceback
            traceback.print_exc()

async def test_simple_search():
    """Test a very simple search"""
    print("\n🧪 Testing simple search...")
    
    try:
        # Create a simple test vector
        test_vector = np.random.rand(384).astype(np.float32)
        print(f"Test vector shape: {test_vector.shape}")
        
        # Search
        results = faiss_manager.search(test_vector, k=5, entity_type="job")
        print(f"Simple search results: {len(results)}")
        
        if results:
            print("✅ Simple search works!")
        else:
            print("❌ Simple search returns no results")
            
    except Exception as e:
        print(f"❌ Error in simple search: {e}")

async def main():
    """Main function"""
    print("🚀 Debugging API Call...")
    
    # Debug the API call
    await debug_api_call()
    
    # Test simple search
    await test_simple_search()
    
    print("\n📋 Summary:")
    print("Check the output above to see where the issue is")

if __name__ == "__main__":
    asyncio.run(main()) 