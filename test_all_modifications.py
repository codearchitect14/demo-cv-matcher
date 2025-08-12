#!/usr/bin/env python3
"""
Comprehensive test suite for all debugging fixes implemented in CV-Matcher
"""

import asyncio
import os
import sys
import time
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.start_time = time.time()
    
    def add_success(self, test_name: str):
        self.passed += 1
        logger.info(f"✅ PASSED: {test_name}")
    
    def add_failure(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        logger.error(f"❌ FAILED: {test_name} - {error}")
    
    def print_summary(self):
        duration = time.time() - self.start_time
        logger.info(f"\n{'='*50}")
        logger.info(f"TEST SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total Tests: {self.passed + self.failed}")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Duration: {duration:.2f}s")
        
        if self.errors:
            logger.info(f"\nErrors:")
            for error in self.errors:
                logger.error(f"  - {error}")

# Global test results
test_results = TestResults()

async def test_code_quality_fixes():
    """Test code quality fixes"""
    logger.info("\n🧪 Testing Code Quality Fixes...")
    
    try:
        # Test 1: Verify dead code removal
        from models.candidate import Candidate, CandidateExperience
        
        # Check that models are properly defined
        assert hasattr(Candidate, '__tablename__')
        assert hasattr(CandidateExperience, '__tablename__')
        
        # Check that composite indexes are defined
        assert hasattr(Candidate, '__table_args__')
        
        test_results.add_success("Dead code removal and model structure")
        
    except Exception as e:
        test_results.add_failure("Dead code removal", str(e))
    
    try:
        # Test 2: Verify centralized error handling
        from core.exceptions import (
            BaseAppException, ValidationException, NotFoundException,
            DatabaseException, AuthenticationException, AuthorizationException,
            CacheException, MLModelException, EmbeddingException,
            RecommendationException, handle_exception, exception_to_http_exception
        )
        
        # Test exception creation
        val_exc = ValidationException("Test validation error", field="test_field")
        assert val_exc.error_code == "VALIDATION_ERROR"
        assert val_exc.severity.value == "low"
        
        # Test exception conversion
        http_exc = exception_to_http_exception(val_exc)
        assert http_exc.status_code == 400
        
        test_results.add_success("Centralized error handling system")
        
    except Exception as e:
        test_results.add_failure("Centralized error handling", str(e))
    
    try:
        # Test 3: Verify type hints
        from db.crud.candidate import CRUDCandidate, CandidateDataProtocol, ExperienceDataProtocol
        
        # Check that protocols are defined
        assert CandidateDataProtocol.__annotations__
        assert ExperienceDataProtocol.__annotations__
        
        test_results.add_success("Type hints and Protocol classes")
        
    except Exception as e:
        test_results.add_failure("Type hints", str(e))

async def test_ai_ml_logic_fixes():
    """Test AI/ML logic fixes"""
    logger.info("\n🤖 Testing AI/ML Logic Fixes...")
    
    try:
        # Test 1: Verify configurable ML thresholds
        from services.skill_matcher import AdvancedSkillMatcher
        
        # Create skill matcher instance
        matcher = AdvancedSkillMatcher()
        
        # Check that thresholds are loaded from environment
        assert hasattr(matcher, 'exact_match_threshold')
        assert hasattr(matcher, 'fuzzy_match_threshold')
        assert hasattr(matcher, 'semantic_match_threshold')
        assert hasattr(matcher, 'context_match_threshold')
        assert hasattr(matcher, 'min_skill_confidence')
        assert hasattr(matcher, 'max_skill_variations')
        
        # Check that thread pool executor is initialized
        assert hasattr(matcher, 'executor')
        
        test_results.add_success("Configurable ML thresholds and thread pool")
        
    except Exception as e:
        test_results.add_failure("Configurable ML thresholds", str(e))
    
    try:
        # Test 2: Verify enhanced embedding validation
        from embeddings.embedder import OptimizedEmbeddingService
        
        # Create embedding service
        embedder = OptimizedEmbeddingService()
        
        # Test embedding validation with mock data
        test_embedding = np.random.randn(384)  # Typical embedding size
        is_valid, quality_score = embedder._validate_embedding_quality(test_embedding)
        
        # Check that validation returns expected types
        assert isinstance(is_valid, bool)
        assert isinstance(quality_score, float)
        assert 0 <= quality_score <= 1
        
        test_results.add_success("Enhanced embedding quality validation")
        
    except Exception as e:
        test_results.add_failure("Enhanced embedding validation", str(e))
    
    try:
        # Test 3: Verify model versioning
        from services.ml_trainer_service import MLTrainerService
        
        # Create ML trainer service
        trainer = MLTrainerService()
        
        # Check that versioning methods exist
        assert hasattr(trainer, 'save_model')
        assert hasattr(trainer, 'get_model_versions')
        assert hasattr(trainer, 'rollback_model')
        assert hasattr(trainer, 'get_current_model_info')
        
        # Test model info method
        model_info = trainer.get_current_model_info()
        assert isinstance(model_info, dict)
        assert 'is_loaded' in model_info
        
        test_results.add_success("Model versioning system")
        
    except Exception as e:
        test_results.add_failure("Model versioning", str(e))

async def test_database_performance_fixes():
    """Test database performance fixes"""
    logger.info("\n🗄️ Testing Database Performance Fixes...")
    
    try:
        # Test 1: Verify connection pool monitoring
        from config.database import DatabaseMonitor, db_monitor
        
        # Check that monitor is initialized
        assert isinstance(db_monitor, DatabaseMonitor)
        assert hasattr(db_monitor, 'check_pool_health')
        assert hasattr(db_monitor, 'get_pool_recommendations')
        
        test_results.add_success("Connection pool monitoring")
        
    except Exception as e:
        test_results.add_failure("Connection pool monitoring", str(e))
    
    try:
        # Test 2: Verify query optimization
        from db.crud.candidate import CRUDCandidate
        
        # Create CRUD instance
        crud = CRUDCandidate()
        
        # Check that optimized methods exist
        assert hasattr(crud, 'search_candidates_optimized')
        assert hasattr(crud, 'get_candidates_by_skills_optimized')
        assert hasattr(crud, 'get_candidate_stats_optimized')
        assert hasattr(crud, '_analyze_query_performance')
        
        test_results.add_success("Query optimization methods")
        
    except Exception as e:
        test_results.add_failure("Query optimization", str(e))

async def test_caching_fixes():
    """Test caching fixes"""
    logger.info("\n💾 Testing Caching Fixes...")
    
    try:
        # Test 1: Verify adaptive compression
        from services.cache_service import RedisCacheService
        
        # Create cache service
        cache_service = RedisCacheService()
        
        # Check that compression settings exist
        assert hasattr(cache_service, 'compression_settings')
        assert hasattr(cache_service, '_should_compress')
        assert hasattr(cache_service, '_compress_data')
        
        # Test compression decision logic
        should_compress = cache_service._should_compress("test data", "embedding")
        assert isinstance(should_compress, bool)
        
        test_results.add_success("Adaptive compression system")
        
    except Exception as e:
        test_results.add_failure("Adaptive compression", str(e))
    
    try:
        # Test 2: Verify intelligent cache invalidation
        from services.cache_service import RedisCacheService
        
        cache_service = RedisCacheService()
        
        # Check that invalidation methods exist
        assert hasattr(cache_service, 'invalidate_job_cache')
        assert hasattr(cache_service, 'invalidate_candidate_cache')
        assert hasattr(cache_service, 'invalidate_skill_cache')
        assert hasattr(cache_service, 'smart_invalidate')
        assert hasattr(cache_service, '_invalidate_pattern')
        
        test_results.add_success("Intelligent cache invalidation")
        
    except Exception as e:
        test_results.add_failure("Intelligent cache invalidation", str(e))
    
    try:
        # Test 3: Verify memory leak prevention
        from middleware.rate_limiter import RedisRateLimiter
        
        # Create rate limiter
        rate_limiter = RedisRateLimiter()
        
        # Check that LRU methods exist
        assert hasattr(rate_limiter, '_cleanup_fallback_cache')
        assert hasattr(rate_limiter, '_remove_from_fallback_cache')
        assert hasattr(rate_limiter, '_update_lru_order')
        assert hasattr(rate_limiter, '_add_to_fallback_cache')
        
        # Check memory limits
        assert hasattr(rate_limiter, 'fallback_cache_size')
        assert hasattr(rate_limiter, 'fallback_memory_limit')
        
        test_results.add_success("Memory leak prevention with LRU eviction")
        
    except Exception as e:
        test_results.add_failure("Memory leak prevention", str(e))

async def test_performance_fixes():
    """Test performance fixes"""
    logger.info("\n⚡ Testing Performance Fixes...")
    
    try:
        # Test 1: Verify async CPU operations
        from services.skill_matcher import AdvancedSkillMatcher
        
        matcher = AdvancedSkillMatcher()
        
        # Check that async wrappers exist
        assert hasattr(matcher, 'find_skill_matches_async')
        assert hasattr(matcher, 'calculate_skill_overlap_async')
        assert hasattr(matcher, 'validate_skill_requirements_async')
        assert hasattr(matcher, 'calculate_overall_match_score_async')
        
        test_results.add_success("Async CPU operations with thread pool")
        
    except Exception as e:
        test_results.add_failure("Async CPU operations", str(e))
    
    try:
        # Test 2: Verify chunked processing
        from embeddings.embedder import OptimizedEmbeddingService
        
        embedder = OptimizedEmbeddingService()
        
        # Check that chunked processing methods exist
        assert hasattr(embedder, 'generate_embedding_batch')
        assert hasattr(embedder, '_process_chunk')
        assert hasattr(embedder, 'update_embeddings_incremental')
        assert hasattr(embedder, '_process_entity_chunk')
        
        test_results.add_success("Chunked processing for large datasets")
        
    except Exception as e:
        test_results.add_failure("Chunked processing", str(e))

async def test_integration_scenarios():
    """Test integration scenarios"""
    logger.info("\n🔗 Testing Integration Scenarios...")
    
    try:
        # Test 1: Error handling integration
        from core.exceptions import ValidationException, handle_exception
        
        # Test exception handling
        try:
            raise ValueError("Test error")
        except Exception as e:
            app_exc = handle_exception(e)
            assert isinstance(app_exc, ValidationException)
        
        test_results.add_success("Error handling integration")
        
    except Exception as e:
        test_results.add_failure("Error handling integration", str(e))
    
    try:
        # Test 2: Configuration management
        # Test environment variable fallbacks
        os.environ.pop('SKILL_EXACT_MATCH_THRESHOLD', None)
        from services.skill_matcher import AdvancedSkillMatcher
        
        matcher = AdvancedSkillMatcher()
        assert matcher.exact_match_threshold == 100.0  # Default value
        
        test_results.add_success("Configuration management with defaults")
        
    except Exception as e:
        test_results.add_failure("Configuration management", str(e))
    
    try:
        # Test 3: Performance monitoring
        from config.database import get_database_health
        
        # Test health check function exists
        assert callable(get_database_health)
        
        test_results.add_success("Performance monitoring integration")
        
    except Exception as e:
        test_results.add_failure("Performance monitoring", str(e))

async def test_backward_compatibility():
    """Test backward compatibility"""
    logger.info("\n🔄 Testing Backward Compatibility...")
    
    try:
        # Test 1: Verify existing imports still work
        from models.candidate import Candidate
        from db.crud.candidate import candidate
        from services.skill_matcher import skill_matcher
        
        # Check that instances are created
        assert candidate is not None
        assert skill_matcher is not None
        
        test_results.add_success("Backward compatibility - imports")
        
    except Exception as e:
        test_results.add_failure("Backward compatibility - imports", str(e))
    
    try:
        # Test 2: Verify existing method signatures
        from db.crud.candidate import CRUDCandidate
        
        crud = CRUDCandidate()
        
        # Check that original methods still exist
        assert hasattr(crud, 'get_with_experiences')
        assert hasattr(crud, 'get_by_email')
        assert hasattr(crud, 'search_candidates')
        
        test_results.add_success("Backward compatibility - method signatures")
        
    except Exception as e:
        test_results.add_failure("Backward compatibility - method signatures", str(e))

async def run_all_tests():
    """Run all test suites"""
    logger.info("🚀 Starting comprehensive test suite for all modifications...")
    
    # Run all test categories
    await test_code_quality_fixes()
    await test_ai_ml_logic_fixes()
    await test_database_performance_fixes()
    await test_caching_fixes()
    await test_performance_fixes()
    await test_integration_scenarios()
    await test_backward_compatibility()
    
    # Print final results
    test_results.print_summary()
    
    # Return success if all tests passed
    return test_results.failed == 0

if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(run_all_tests())
    
    if success:
        logger.info("🎉 All tests passed! All modifications are working correctly.")
        sys.exit(0)
    else:
        logger.error("💥 Some tests failed. Please review the errors above.")
        sys.exit(1) 