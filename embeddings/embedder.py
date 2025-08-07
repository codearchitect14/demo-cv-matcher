import numpy as np
from sentence_transformers import SentenceTransformer
import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Any
import hashlib
import json
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import redis.asyncio as redis
from config.security import SecurityConfig

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    """Result of embedding generation with metadata"""
    embedding: np.ndarray
    text: str
    model_name: str
    generation_time: float
    quality_score: float
    cache_hit: bool = False

class OptimizedEmbeddingService:
    """Optimized embedding service with batch processing and caching"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.redis_client = redis.from_url(SecurityConfig.REDIS_URL, decode_responses=True)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.batch_size = 32
        self.cache_ttl = 86400  # 24 hours
        
        # Quality thresholds
        self.min_embedding_norm = 0.1
        self.max_embedding_norm = 10.0
        
        logger.info(f"Initialized OptimizedEmbeddingService with model: {model_name}")
    
    def _generate_cache_key(self, text: str, model_name: str) -> str:
        """Generate cache key for embedding"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embedding:{model_name}:{text_hash}"
    
    async def _get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get cached embedding using advanced cache service"""
        try:
            from services.cache_service import cache_service
            cached_embedding = await cache_service.get_cached_embedding(text, self.model_name)
            if cached_embedding is not None:
                return np.array(cached_embedding)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None
    
    async def _cache_embedding(self, text: str, embedding: np.ndarray, metadata: Dict[str, Any]):
        """Cache embedding with metadata using advanced cache service"""
        try:
            from services.cache_service import cache_service
            await cache_service.cache_embedding(text, embedding.tolist(), self.model_name)
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def _validate_embedding_quality(self, embedding: np.ndarray) -> Tuple[bool, float]:
        """Validate embedding quality"""
        # Check embedding norm
        norm = np.linalg.norm(embedding)
        if norm < self.min_embedding_norm or norm > self.max_embedding_norm:
            return False, norm
        
        # Check for NaN or infinite values
        if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
            return False, norm
        
        # Calculate quality score (higher is better)
        quality_score = 1.0 / (1.0 + norm)  # Normalize between 0 and 1
        return True, quality_score
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for embedding generation"""
        if not text:
            return ""
        
        # Basic preprocessing
        text = text.strip()
        text = text.replace('\n', ' ')
        text = ' '.join(text.split())  # Remove extra whitespace
        
        # Truncate if too long (model has limits)
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    async def generate_embedding_batch(
        self, 
        texts: List[str], 
        batch_size: Optional[int] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts with batch processing"""
        if not texts:
            return []
        
        batch_size = batch_size or self.batch_size
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_results = await self._process_batch(batch_texts)
            results.extend(batch_results)
        
        return results
    
    async def _process_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Process a batch of texts for embedding generation"""
        batch_results = []
        
        # Check cache first
        cache_results = []
        texts_to_process = []
        
        for text in texts:
            cached_embedding = await self._get_cached_embedding(text)
            if cached_embedding is not None:
                cache_results.append(EmbeddingResult(
                    embedding=cached_embedding,
                    text=text,
                    model_name=self.model_name,
                    generation_time=0.0,
                    quality_score=1.0,
                    cache_hit=True
                ))
            else:
                texts_to_process.append(text)
        
        # Generate embeddings for uncached texts
        if texts_to_process:
            start_time = time.time()
            
            # Preprocess texts
            processed_texts = [self._preprocess_text(text) for text in texts_to_process]
            
            # Generate embeddings in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor, 
                self.model.encode, 
                processed_texts
            )
            
            generation_time = time.time() - start_time
            
            # Process results
            for i, (text, embedding) in enumerate(zip(texts_to_process, embeddings)):
                # Validate quality
                is_valid, quality_score = self._validate_embedding_quality(embedding)
                
                if is_valid:
                    # Cache the embedding
                    metadata = {
                        'quality_score': quality_score,
                        'generation_time': generation_time / len(texts_to_process)
                    }
                    await self._cache_embedding(text, embedding, metadata)
                    
                    batch_results.append(EmbeddingResult(
                        embedding=embedding,
                        text=text,
                        model_name=self.model_name,
                        generation_time=generation_time / len(texts_to_process),
                        quality_score=quality_score,
                        cache_hit=False
                    ))
                else:
                    logger.warning(f"Low quality embedding generated for text: {text[:100]}...")
                    # Return zero embedding for invalid results
                    batch_results.append(EmbeddingResult(
                        embedding=np.zeros(self.model.get_sentence_embedding_dimension()),
                        text=text,
                        model_name=self.model_name,
                        generation_time=generation_time / len(texts_to_process),
                        quality_score=0.0,
                        cache_hit=False
                    ))
        
        # Combine cache hits and new results
        return cache_results + batch_results
    
    async def generate_job_embedding(self, job_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """Generate embedding for job data with optimized processing"""
        try:
            # Combine relevant job fields
            job_text = f"{job_data.get('title', '')} {job_data.get('company', '')} {job_data.get('location', '')} {job_data.get('domain', '')} {job_data.get('job_description', '')}"
            
            results = await self.generate_embedding_batch([job_text])
            if results and results[0].quality_score > 0.5:
                return results[0].embedding
            else:
                logger.warning(f"Low quality job embedding generated for job ID: {job_data.get('id')}")
                return None
        except Exception as e:
            logger.error(f"Failed to generate job embedding: {e}")
            return None
    
    async def generate_candidate_embedding(self, candidate_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """Generate embedding for candidate data with optimized processing"""
        try:
            # Combine relevant candidate fields
            candidate_text = f"{candidate_data.get('name', '')} {candidate_data.get('location', '')} {candidate_data.get('domain', '')} {candidate_data.get('summary', '')}"
            
            # Add experience information
            if candidate_data.get('experiences'):
                experience_text = " ".join([
                    f"{exp.get('skill', '')} {exp.get('years', 0)} years"
                    for exp in candidate_data['experiences']
                ])
                candidate_text += f" {experience_text}"
            
            results = await self.generate_embedding_batch([candidate_text])
            if results and results[0].quality_score > 0.5:
                return results[0].embedding
            else:
                logger.warning(f"Low quality candidate embedding generated for candidate ID: {candidate_data.get('id')}")
                return None
        except Exception as e:
            logger.error(f"Failed to generate candidate embedding: {e}")
            return None
    
    async def update_embeddings_incremental(
        self, 
        entity_type: str, 
        entity_ids: List[int],
        get_entity_data_func
    ) -> Dict[str, Any]:
        """Update embeddings incrementally for specific entities"""
        try:
            start_time = time.time()
            updated_count = 0
            failed_count = 0
            
            # Get entity data
            entities_data = await get_entity_data_func(entity_ids)
            
            # Generate embeddings in batches
            texts = []
            entity_map = {}
            
            for entity in entities_data:
                if entity_type == "job":
                    text = f"{entity.get('title', '')} {entity.get('company', '')} {entity.get('location', '')} {entity.get('domain', '')} {entity.get('job_description', '')}"
                else:  # candidate
                    text = f"{entity.get('name', '')} {entity.get('location', '')} {entity.get('domain', '')} {entity.get('summary', '')}"
                
                texts.append(text)
                entity_map[text] = entity['id']
            
            # Generate embeddings
            embedding_results = await self.generate_embedding_batch(texts)
            
            # Process results
            for result in embedding_results:
                if result.quality_score > 0.5:
                    updated_count += 1
                else:
                    failed_count += 1
            
            processing_time = time.time() - start_time
            
            return {
                "entity_type": entity_type,
                "entities_processed": len(entity_ids),
                "embeddings_updated": updated_count,
                "embeddings_failed": failed_count,
                "processing_time": processing_time,
                "average_quality_score": np.mean([r.quality_score for r in embedding_results]) if embedding_results else 0.0
            }
            
        except Exception as e:
            logger.error(f"Incremental embedding update failed: {e}")
            return {
                "error": str(e),
                "entity_type": entity_type,
                "entities_processed": 0
            }
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics"""
        try:
            # Get cache statistics
            cache_keys = await self.redis_client.keys("embedding:*")
            cache_size = len(cache_keys)
            
            # Get model information
            model_info = {
                "model_name": self.model_name,
                "embedding_dimension": self.model.get_sentence_embedding_dimension(),
                "max_sequence_length": self.model.max_seq_length
            }
            
            return {
                "cache_size": cache_size,
                "cache_ttl": self.cache_ttl,
                "batch_size": self.batch_size,
                "model_info": model_info,
                "quality_thresholds": {
                    "min_norm": self.min_embedding_norm,
                    "max_norm": self.max_embedding_norm
                }
            }
        except Exception as e:
            logger.error(f"Failed to get embedding stats: {e}")
            return {"error": str(e)}
    
    async def clear_embedding_cache(self) -> bool:
        """Clear all cached embeddings"""
        try:
            cache_keys = await self.redis_client.keys("embedding:*")
            if cache_keys:
                await self.redis_client.delete(*cache_keys)
            return True
        except Exception as e:
            logger.error(f"Failed to clear embedding cache: {e}")
            return False

# Global embedding service instance
embedding_service = OptimizedEmbeddingService()
