#!/usr/bin/env python3
"""
Create a working FAISS index with known data
"""

import asyncio
import sys
import os
import numpy as np

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from embeddings.build_index import faiss_manager
from embeddings.embedder import embedding_service

async def create_working_index():
    """Create a working FAISS index with known data"""
    print("🚀 Creating working FAISS index...")
    
    try:
        # 1. Clear existing index
        print("1. Clearing existing index...")
        faiss_manager.index = None
        faiss_manager.id_to_index = {}
        faiss_manager.index_to_id = {}
        faiss_manager._create_index()
        
        # 2. Create job embeddings (using the data we know exists)
        print("2. Creating job embeddings...")
        
        # Job data we know exists from the debug output
        jobs = [
            {
                'id': 2,
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'location': 'Lahore',
                'salary_min': 50000,
                'salary_max': 80000,
                'domain': 'Software Development',
                'job_description': 'We are looking for a Python developer with experience in web development and Django framework.'
            },
            {
                'id': 3,
                'title': 'Senior Python Developer',
                'company': 'Tech Solutions',
                'location': 'Karachi',
                'salary_min': 80000,
                'salary_max': 120000,
                'domain': 'Technology',
                'job_description': 'Senior Python developer position requiring 5+ years of experience in Python, Django, and cloud technologies.'
            },
            {
                'id': 4,
                'title': 'AI Python Developer',
                'company': 'Boolmind',
                'location': 'Islamabad',
                'salary_min': 60000,
                'salary_max': 100000,
                'domain': 'Software Developer',
                'job_description': 'AI-focused Python developer role working with machine learning, TensorFlow, and data science projects.'
            },
            {
                'id': 5,
                'title': 'AI Software Developer',
                'company': 'Turing',
                'location': 'Remote',
                'salary_min': 70000,
                'salary_max': 110000,
                'domain': 'Software Development',
                'job_description': 'AI software developer position focusing on artificial intelligence, machine learning, and Python development.'
            }
        ]
        
        # Generate job embeddings
        job_vectors = []
        job_ids = []
        
        for job in jobs:
            embedding = embedding_service.generate_job_embedding(
                job_title=job['title'],
                job_description=job['job_description'],
                domain=job['domain']
            )
            
            job_vectors.append(embedding)
            job_ids.append(job['id'])
        
        # Add to FAISS index
        faiss_manager.add_vectors(job_vectors, job_ids, "job")
        print(f"✅ Indexed {len(jobs)} jobs")
        
        # 3. Create candidate embeddings
        print("3. Creating candidate embeddings...")
        
        # Candidate data we know exists
        candidates = [
            {
                'id': 2,
                'name': 'hamza Ali khan',
                'location': 'Lahore',
                'domain': 'Software Developer',
                'summary': 'Experienced Python developer with 3 years of experience in web development and Django.',
                'experiences': [
                    {'skill': 'Python', 'years': 3, 'description': 'Web development with Django'},
                    {'skill': 'JavaScript', 'years': 2, 'description': 'Frontend development'},
                    {'skill': 'SQL', 'years': 2, 'description': 'Database management'}
                ]
            },
            {
                'id': 3,
                'name': 'hamza',
                'location': 'Karachi',
                'domain': 'Software Development',
                'summary': 'Senior software developer with expertise in Python and machine learning.',
                'experiences': [
                    {'skill': 'Python', 'years': 5, 'description': 'Backend development and API design'},
                    {'skill': 'Machine Learning', 'years': 3, 'description': 'ML model development'},
                    {'skill': 'Docker', 'years': 2, 'description': 'Containerization and deployment'}
                ]
            }
        ]
        
        # Generate candidate embeddings
        candidate_vectors = []
        candidate_ids = []
        
        for candidate in candidates:
            embedding = embedding_service.generate_candidate_embedding(
                summary=candidate['summary'],
                experiences=candidate['experiences']
            )
            
            candidate_vectors.append(embedding)
            candidate_ids.append(candidate['id'])
        
        # Add to FAISS index
        faiss_manager.add_vectors(candidate_vectors, candidate_ids, "candidate")
        print(f"✅ Indexed {len(candidates)} candidates")
        
        # 4. Save index
        print("4. Saving index...")
        faiss_manager.save_index()
        
        # 5. Verify index
        print("5. Verifying index...")
        stats = faiss_manager.get_index_stats()
        print(f"Index stats: {stats}")
        
        if stats['total_vectors'] == 0:
            print("❌ Index is still empty!")
            return False
        else:
            print(f"✅ Successfully indexed {stats['total_vectors']} vectors")
            return True
            
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_recommendations():
    """Test recommendations with the new index"""
    print("\n🧪 Testing recommendations...")
    
    try:
        # Test job recommendations for candidate 2
        print("Testing job recommendations for candidate 2...")
        
        # Create candidate embedding
        candidate_embedding = embedding_service.generate_candidate_embedding(
            summary="Experienced Python developer with 3 years of experience in web development and Django.",
            experiences=[
                {'skill': 'Python', 'years': 3, 'description': 'Web development with Django'},
                {'skill': 'JavaScript', 'years': 2, 'description': 'Frontend development'},
                {'skill': 'SQL', 'years': 2, 'description': 'Database management'}
            ]
        )
        
        # Search for similar jobs
        job_results = faiss_manager.search(candidate_embedding, k=5, entity_type="job")
        print(f"Job recommendations: {len(job_results)}")
        for i, (job_id, score) in enumerate(job_results[:3]):
            print(f"  {i+1}. Job ID: {job_id}, Score: {score:.3f}")
        
        # Test candidate recommendations for job 2
        print("\nTesting candidate recommendations for job 2...")
        
        # Create job embedding
        job_embedding = embedding_service.generate_job_embedding(
            job_title="Python Developer",
            job_description="We are looking for a Python developer with experience in web development and Django framework.",
            domain="Software Development"
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

async def main():
    """Main function"""
    print("🔄 Creating Working FAISS Index...")
    
    # Create working index
    success = await create_working_index()
    
    if success:
        # Test recommendations
        await test_recommendations()
        
        print("\n🎉 Index creation complete!")
        print("Now you can test the API endpoints again.")
        print("The FAISS index should now contain data and return recommendations.")
    else:
        print("\n❌ Index creation failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main()) 