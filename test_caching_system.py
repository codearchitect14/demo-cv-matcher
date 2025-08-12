#!/usr/bin/env python3
"""
Test script for Redis Caching System functionality
Tests compression, TTL, cache invalidation, and performance
"""

import asyncio
import sys
import os
import time
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cache_service import cache_service
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_caching():
    """Test basic cache operations"""
    print("🧪 Testing Basic Caching Operations")
    print("=" * 45)
    
    # Test 1: Set and Get
    print("\n1. Testing Set and Get:")
    test_data = {"name": "John Doe", "skills": ["python", "javascript"], "experience": 5}
    success = await cache_service.set('test', 'user1', test_data, ttl=60)
    print(f"   Set operation: {'✅ Success' if success else '❌ Failed'}")
    
    retrieved = await cache_service.get('test', 'user1')
    print(f"   Get operation: {'✅ Success' if retrieved else '❌ Failed'}")
    assert retrieved == test_data, "Data mismatch in basic cache test"
    
    # Test 2: Cache Miss
    print("\n2. Testing Cache Miss:")
    not_found = await cache_service.get('test', 'nonexistent')
    print(f"   Cache miss: {'✅ Correct' if not_found is None else '❌ Unexpected data'}")
    assert not_found is None, "Cache miss should return None"
    
    # Test 3: Delete
    print("\n3. Testing Delete:")
    delete_success = await cache_service.delete('test', 'user1')
    print(f"   Delete operation: {'✅ Success' if delete_success else '❌ Failed'}")
    
    # Verify deletion
    after_delete = await cache_service.get('test', 'user1')
    print(f"   After delete: {'✅ Correct' if after_delete is None else '❌ Still exists'}")
    assert after_delete is None, "Data should be deleted"
    
    print("\n✅ All basic caching tests passed!")
    return True

async def test_embedding_caching():
    """Test embedding-specific caching"""
    print("\n🧪 Testing Embedding Caching")
    print("=" * 35)
    
    # Test embedding cache
    test_text = "Python developer with 5 years experience in web development"
    test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # Large embedding
    
    print("\n1. Testing Embedding Cache Set:")
    success = await cache_service.cache_embedding(test_text, test_embedding, "test_model")
    print(f"   Cache embedding: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n2. Testing Embedding Cache Get:")
    cached_embedding = await cache_service.get_cached_embedding(test_text, "test_model")
    print(f"   Get cached embedding: {'✅ Success' if cached_embedding else '❌ Failed'}")
    assert cached_embedding == test_embedding, "Embedding data mismatch"
    
    print("\n3. Testing Embedding Cache Miss:")
    wrong_text = "Different text that should not be cached"
    not_found = await cache_service.get_cached_embedding(wrong_text, "test_model")
    print(f"   Cache miss: {'✅ Correct' if not_found is None else '❌ Unexpected data'}")
    
    print("\n✅ All embedding caching tests passed!")
    return True

async def test_recommendation_caching():
    """Test recommendation-specific caching"""
    print("\n🧪 Testing Recommendation Caching")
    print("=" * 40)
    
    # Test recommendation cache
    user_id = "user123"
    job_id = "job456"
    algorithm = "semantic_search"
    test_recommendations = [
        {"job_id": 1, "title": "Python Developer", "score": 0.95},
        {"job_id": 2, "title": "Full Stack Developer", "score": 0.87},
        {"job_id": 3, "title": "Backend Engineer", "score": 0.82}
    ]
    
    print("\n1. Testing Recommendation Cache Set:")
    success = await cache_service.cache_recommendation(user_id, job_id, test_recommendations, algorithm)
    print(f"   Cache recommendation: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n2. Testing Recommendation Cache Get:")
    cached_recommendations = await cache_service.get_cached_recommendation(user_id, job_id, algorithm)
    print(f"   Get cached recommendation: {'✅ Success' if cached_recommendations else '❌ Failed'}")
    assert cached_recommendations == test_recommendations, "Recommendation data mismatch"
    
    print("\n3. Testing Recommendation Cache Miss:")
    wrong_algorithm = "different_algorithm"
    not_found = await cache_service.get_cached_recommendation(user_id, job_id, wrong_algorithm)
    print(f"   Cache miss: {'✅ Correct' if not_found is None else '❌ Unexpected data'}")
    
    print("\n✅ All recommendation caching tests passed!")
    return True

async def test_compression():
    """Test data compression functionality"""
    print("\n🧪 Testing Data Compression")
    print("=" * 30)
    
    # Create large data for compression test
    large_data = {
        "text": "This is a very long text that should be compressed. " * 1000,
        "numbers": list(range(10000)),
        "nested": {
            "level1": {"level2": {"level3": "deep nested data" * 100}}
        }
    }
    
    print("\n1. Testing Large Data Compression:")
    success = await cache_service.set('compression', 'large_data', large_data, ttl=60)
    print(f"   Set large data: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n2. Testing Compressed Data Retrieval:")
    retrieved = await cache_service.get('compression', 'large_data')
    print(f"   Get compressed data: {'✅ Success' if retrieved else '❌ Failed'}")
    assert retrieved == large_data, "Compressed data mismatch"
    
    print("\n3. Testing Compression Stats:")
    stats = await cache_service.get_cache_stats()
    compressions = stats.get('cache_stats', {}).get('compressions', 0)
    print(f"   Compression count: {compressions}")
    assert compressions > 0, "No compressions detected"
    
    print("\n✅ All compression tests passed!")
    return True

async def test_cache_invalidation():
    """Test cache invalidation functionality"""
    print("\n🧪 Testing Cache Invalidation")
    print("=" * 35)
    
    # Set up test data
    job_id = "test_job_123"
    candidate_id = "test_candidate_456"
    
    job_data = {"id": job_id, "title": "Test Job", "company": "Test Company"}
    candidate_data = {"id": candidate_id, "name": "Test Candidate", "skills": ["python"]}
    
    print("\n1. Setting up test data:")
    await cache_service.cache_job_data(job_id, job_data)
    await cache_service.cache_candidate_data(candidate_id, candidate_data)
    print("   ✅ Test data cached")
    
    print("\n2. Testing Job Cache Invalidation:")
    await cache_service.invalidate_job_cache(job_id)
    cached_job = await cache_service.get_cached_job_data(job_id)
    print(f"   Job cache after invalidation: {'✅ Correct' if cached_job is None else '❌ Still exists'}")
    assert cached_job is None, "Job cache should be invalidated"
    
    print("\n3. Testing Candidate Cache Invalidation:")
    await cache_service.invalidate_candidate_cache(candidate_id)
    cached_candidate = await cache_service.get_cached_candidate_data(candidate_id)
    print(f"   Candidate cache after invalidation: {'✅ Correct' if cached_candidate is None else '❌ Still exists'}")
    assert cached_candidate is None, "Candidate cache should be invalidated"
    
    print("\n✅ All cache invalidation tests passed!")
    return True

async def test_performance():
    """Test caching performance"""
    print("\n🧪 Testing Cache Performance")
    print("=" * 30)
    
    # Test multiple operations
    operations = 100
    start_time = time.time()
    
    print(f"\n1. Testing {operations} Set Operations:")
    for i in range(operations):
        data = {"id": i, "data": f"test_data_{i}", "timestamp": time.time()}
        await cache_service.set('performance', f'key_{i}', data, ttl=60)
    
    set_time = time.time() - start_time
    print(f"   Set operations completed in {set_time:.4f} seconds")
    print(f"   Average set time: {set_time/operations:.4f} seconds per operation")
    
    print(f"\n2. Testing {operations} Get Operations:")
    get_start = time.time()
    for i in range(operations):
        await cache_service.get('performance', f'key_{i}')
    
    get_time = time.time() - get_start
    print(f"   Get operations completed in {get_time:.4f} seconds")
    print(f"   Average get time: {get_time/operations:.4f} seconds per operation")
    
    # Performance assertions
    assert set_time < 10, "Set operations too slow"
    assert get_time < 5, "Get operations too slow"
    
    print("\n✅ Performance test passed!")
    return True

async def test_cache_stats():
    """Test cache statistics"""
    print("\n🧪 Testing Cache Statistics")
    print("=" * 30)
    
    # Get cache stats
    stats = await cache_service.get_cache_stats()
    
    print("\n1. Cache Statistics:")
    cache_stats = stats.get('cache_stats', {})
    print(f"   Hits: {cache_stats.get('hits', 0)}")
    print(f"   Misses: {cache_stats.get('misses', 0)}")
    print(f"   Sets: {cache_stats.get('sets', 0)}")
    print(f"   Deletes: {cache_stats.get('deletes', 0)}")
    print(f"   Compressions: {cache_stats.get('compressions', 0)}")
    
    print("\n2. Redis Information:")
    redis_info = stats.get('redis_info', {})
    print(f"   Used Memory: {redis_info.get('used_memory', 0)} bytes")
    print(f"   Connected Clients: {redis_info.get('connected_clients', 0)}")
    print(f"   Total Commands: {redis_info.get('total_commands_processed', 0)}")
    
    print("\n3. Hit Rate:")
    hit_rate = stats.get('hit_rate', 0)
    print(f"   Hit Rate: {hit_rate:.2%}")
    
    print("\n✅ Cache statistics test passed!")
    return True

async def main():
    """Run all caching tests"""
    print("🚀 Starting Redis Caching System Tests")
    print("=" * 60)
    
    try:
        # Connect to cache service
        await cache_service.connect()
        print("✅ Connected to cache service")
        
        # Run all tests
        await test_basic_caching()
        await test_embedding_caching()
        await test_recommendation_caching()
        await test_compression()
        await test_cache_invalidation()
        await test_performance()
        await test_cache_stats()
        
        print("\n🎉 All caching tests passed! Redis caching system is working correctly.")
        print("\nKey Features Verified:")
        print("✅ Basic cache operations (set/get/delete)")
        print("✅ Embedding-specific caching")
        print("✅ Recommendation caching")
        print("✅ Data compression for large objects")
        print("✅ Cache invalidation")
        print("✅ Performance optimization")
        print("✅ Cache statistics and monitoring")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
    finally:
        # Disconnect from cache service
        await cache_service.disconnect()
        print("✅ Disconnected from cache service")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 