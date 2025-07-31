#!/usr/bin/env python3
"""
Reindex all data into FAISS for semantic search
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db_session
from recommender.semantic import semantic_search_service
from embeddings.build_index import faiss_manager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reindex_all_data():
    """Reindex all jobs and candidates into FAISS"""
    print("🚀 Reindexing all data into FAISS...")
    
    async for db in get_db_session():
        try:
            # 1. Clear existing index
            print("1. Clearing existing index...")
            faiss_manager.index = None
            faiss_manager.id_to_index = {}
            faiss_manager.index_to_id = {}
            faiss_manager._create_index()
            
            # 2. Index jobs
            print("2. Indexing jobs...")
            await semantic_search_service.index_jobs(db)
            
            # 3. Index candidates
            print("3. Indexing candidates...")
            await semantic_search_service.index_candidates(db)
            
            # 4. Save index
            print("4. Saving index...")
            faiss_manager.save_index()
            
            # 5. Verify index
            print("5. Verifying index...")
            stats = faiss_manager.get_index_stats()
            print(f"Index stats: {stats}")
            
            if stats['total_vectors'] == 0:
                print("❌ Index is still empty! Something went wrong.")
                return False
            else:
                print(f"✅ Successfully indexed {stats['total_vectors']} vectors")
                return True
                
        except Exception as e:
            print(f"❌ Error reindexing: {e}")
            import traceback
            traceback.print_exc()
            return False

async def test_recommendations_after_reindex():
    """Test recommendations after reindexing"""
    print("\n🧪 Testing recommendations after reindex...")
    
    async for db in get_db_session():
        try:
            # Test job recommendations for candidate 2
            print("Testing job recommendations for candidate 2...")
            job_recommendations = await semantic_search_service.find_similar_jobs(
                candidate_id=2, 
                db=db, 
                k=5, 
                apply_filters=False,  # Skip filtering for now
                strict_mode=False,
                use_ml_ranking=False
            )
            
            print(f"Job recommendations: {len(job_recommendations)}")
            for i, rec in enumerate(job_recommendations[:3]):
                print(f"  {i+1}. Job ID: {rec.get('job_id')}, Score: {rec.get('similarity_score', 0):.3f}")
            
            # Test candidate recommendations for job 2
            print("\nTesting candidate recommendations for job 2...")
            candidate_recommendations = await semantic_search_service.find_similar_candidates(
                job_id=2, 
                db=db, 
                k=5, 
                apply_filters=False,  # Skip filtering for now
                strict_mode=False,
                use_ml_ranking=False
            )
            
            print(f"Candidate recommendations: {len(candidate_recommendations)}")
            for i, rec in enumerate(candidate_recommendations[:3]):
                print(f"  {i+1}. Candidate ID: {rec.get('candidate_id')}, Score: {rec.get('similarity_score', 0):.3f}")
                
        except Exception as e:
            print(f"❌ Error testing recommendations: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main function"""
    print("🔄 Reindexing FAISS and Testing Recommendations...")
    
    # Reindex all data
    success = await reindex_all_data()
    
    if success:
        # Test recommendations
        await test_recommendations_after_reindex()
        
        print("\n🎉 Reindexing complete!")
        print("Now you can test the API endpoints again.")
    else:
        print("\n❌ Reindexing failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main()) 