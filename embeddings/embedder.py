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
        """Validate embedding quality with comprehensive checks"""
        try:
            # Check embedding norm
            norm = np.linalg.norm(embedding)
            if norm < self.min_embedding_norm or norm > self.max_embedding_norm:
                logger.warning(f"Embedding norm {norm:.4f} outside valid range [{self.min_embedding_norm}, {self.max_embedding_norm}]")
                return False, norm
            
            # Check for NaN or infinite values
            if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
                logger.warning("Embedding contains NaN or infinite values")
                return False, norm
            
            # Check for zero vectors
            if norm == 0:
                logger.warning("Embedding is a zero vector")
                return False, norm
            
            # Distribution analysis
            mean_val = np.mean(embedding)
            std_val = np.std(embedding)
            
            # Check for reasonable distribution (not all same values)
            if std_val < 1e-6:
                logger.warning("Embedding has very low variance")
                return False, norm
            
            # Outlier detection using IQR method
            q1 = np.percentile(embedding, 25)
            q3 = np.percentile(embedding, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = np.sum((embedding < lower_bound) | (embedding > upper_bound))
            outlier_ratio = outliers / len(embedding)
            
            # Allow up to 10% outliers
            if outlier_ratio > 0.1:
                logger.warning(f"Embedding has {outlier_ratio:.2%} outliers")
                return False, norm
            
            # Check for reasonable value ranges
            min_val = np.min(embedding)
            max_val = np.max(embedding)
            
            # Embeddings should typically be in reasonable range
            if abs(min_val) > 10 or abs(max_val) > 10:
                logger.warning(f"Embedding values outside expected range: [{min_val:.4f}, {max_val:.4f}]")
                return False, norm
            
            # Calculate quality score based on multiple factors
            quality_factors = []
            
            # Norm quality (closer to 1 is better)
            norm_quality = 1.0 / (1.0 + abs(norm - 1.0))
            quality_factors.append(norm_quality)
            
            # Variance quality (higher variance is better for embeddings)
            variance_quality = min(1.0, std_val / 2.0)  # Normalize to [0, 1]
            quality_factors.append(variance_quality)
            
            # Outlier quality (fewer outliers is better)
            outlier_quality = 1.0 - outlier_ratio
            quality_factors.append(outlier_quality)
            
            # Distribution symmetry (closer to 0 mean is better)
            symmetry_quality = 1.0 / (1.0 + abs(mean_val))
            quality_factors.append(symmetry_quality)
            
            # Overall quality score (geometric mean of factors)
            quality_score = np.power(np.prod(quality_factors), 1.0 / len(quality_factors))
            
            # Log quality metrics for monitoring
            logger.debug(f"Embedding quality metrics: norm={norm:.4f}, std={std_val:.4f}, "
                        f"outlier_ratio={outlier_ratio:.4f}, mean={mean_val:.4f}, quality={quality_score:.4f}")
            
            return True, quality_score
            
        except Exception as e:
            logger.error(f"Error validating embedding quality: {e}")
            return False, 0.0
    
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
        batch_size: Optional[int] = None,
        chunk_size: Optional[int] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts with chunked batch processing"""
        if not texts:
            return []
        
        batch_size = batch_size or self.batch_size
        chunk_size = chunk_size or min(100, len(texts))  # Default chunk size
        results = []
        
        # Process in chunks to avoid memory issues
        for i in range(0, len(texts), chunk_size):
            chunk_texts = texts[i:i + chunk_size]
            chunk_results = await self._process_chunk(chunk_texts, batch_size)
            results.extend(chunk_results)
            
            # Log progress for large datasets
            if len(texts) > 100:
                progress = min(100, (i + chunk_size) / len(texts) * 100)
                logger.info(f"Embedding generation progress: {progress:.1f}% ({i + len(chunk_texts)}/{len(texts)})")
        
        return results
    
    async def _process_chunk(self, texts: List[str], batch_size: int) -> List[EmbeddingResult]:
        """Process a chunk of texts with batch processing"""
        chunk_results = []
        
        # Process chunk in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_results = await self._process_batch(batch_texts)
            chunk_results.extend(batch_results)
        
        return chunk_results
    
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
                # Validate embedding quality
                is_valid, quality_score = self._validate_embedding_quality(embedding)
                
                if is_valid:
                    # Cache the embedding
                    await self._cache_embedding(text, embedding, {
                        'model_name': self.model_name,
                        'quality_score': quality_score,
                        'generation_time': generation_time
                    })
                    
                    batch_results.append(EmbeddingResult(
                        embedding=embedding,
                        text=text,
                        model_name=self.model_name,
                        generation_time=generation_time,
                        quality_score=quality_score,
                        cache_hit=False
                    ))
                else:
                    logger.warning(f"Invalid embedding generated for text: {text[:100]}...")
                    # Return zero embedding for invalid results
                    batch_results.append(EmbeddingResult(
                        embedding=np.zeros(self.model.get_sentence_embedding_dimension()),
                        text=text,
                        model_name=self.model_name,
                        generation_time=generation_time,
                        quality_score=0.0,
                        cache_hit=False
                    ))
        
        # Add cache results
        batch_results.extend(cache_results)
        
        return batch_results
    
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
        get_entity_data_func,
        batch_size: Optional[int] = None,
        chunk_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update embeddings incrementally with chunked processing"""
        batch_size = batch_size or self.batch_size
        chunk_size = chunk_size or min(50, len(entity_ids))  # Smaller chunks for incremental updates
        
        results = {
            'total_entities': len(entity_ids),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processing_time': 0.0
        }
        
        start_time = time.time()
        
        try:
            # Process entities in chunks
            for i in range(0, len(entity_ids), chunk_size):
                chunk_ids = entity_ids[i:i + chunk_size]
                
                # Get entity data for chunk
                chunk_data = []
                for entity_id in chunk_ids:
                    try:
                        entity_data = await get_entity_data_func(entity_id)
                        if entity_data:
                            chunk_data.append((entity_id, entity_data))
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to get data for {entity_type} {entity_id}: {e}")
                
                # Process chunk
                chunk_results = await self._process_entity_chunk(
                    entity_type, chunk_data, batch_size
                )
                
                # Update results
                results['processed'] += len(chunk_data)
                results['successful'] += chunk_results['successful']
                results['failed'] += chunk_results['failed']
                results['errors'].extend(chunk_results['errors'])
                
                # Log progress
                progress = min(100, (i + chunk_size) / len(entity_ids) * 100)
                logger.info(f"Incremental embedding update progress: {progress:.1f}% "
                           f"({results['processed']}/{len(entity_ids)})")
        
        except Exception as e:
            logger.error(f"Error in incremental embedding update: {e}")
            results['errors'].append(f"General error: {e}")
        
        results['processing_time'] = time.time() - start_time
        
        logger.info(f"Incremental embedding update completed: "
                   f"{results['successful']} successful, {results['failed']} failed, "
                   f"time: {results['processing_time']:.2f}s")
        
        return results
    
    async def _process_entity_chunk(
        self, 
        entity_type: str, 
        chunk_data: List[Tuple[int, Dict]], 
        batch_size: int
    ) -> Dict[str, Any]:
        """Process a chunk of entities for embedding generation"""
        results = {
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Extract text data from entities
            texts = []
            entity_map = []
            
            for entity_id, entity_data in chunk_data:
                try:
                    # Extract text based on entity type
                    if entity_type == 'job':
                        text = self._extract_job_text(entity_data)
                    elif entity_type == 'candidate':
                        text = self._extract_candidate_text(entity_data)
                    else:
                        text = str(entity_data)
                    
                    if text:
                        texts.append(text)
                        entity_map.append(entity_id)
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to extract text for {entity_type} {entity_id}: {e}")
            
            if texts:
                # Generate embeddings for texts
                embedding_results = await self._process_batch(texts)
                
                # Map results back to entities
                for i, (entity_id, embedding_result) in enumerate(zip(entity_map, embedding_results)):
                    if embedding_result.quality_score > 0.5:  # Only consider good quality embeddings
                        results['successful'] += 1
                        # Here you would save the embedding to the database
                        # await save_embedding_to_db(entity_type, entity_id, embedding_result.embedding)
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Low quality embedding for {entity_type} {entity_id}")
        
        except Exception as e:
            logger.error(f"Error processing entity chunk: {e}")
            results['errors'].append(f"Chunk processing error: {e}")
        
        return results
    
    def _extract_job_text(self, job_data: Dict) -> str:
        """Extract text from job data for embedding"""
        text_parts = []
        
        if job_data.get('title'):
            text_parts.append(job_data['title'])
        
        if job_data.get('description'):
            text_parts.append(job_data['description'])
        
        if job_data.get('requirements'):
            text_parts.append(job_data['requirements'])
        
        if job_data.get('skills'):
            if isinstance(job_data['skills'], list):
                text_parts.extend(job_data['skills'])
            else:
                text_parts.append(str(job_data['skills']))
        
        return ' '.join(text_parts)
    
    def _extract_candidate_text(self, candidate_data: Dict) -> str:
        """Extract text from candidate data for embedding"""
        text_parts = []
        
        if candidate_data.get('summary'):
            text_parts.append(candidate_data['summary'])
        
        if candidate_data.get('experiences'):
            for exp in candidate_data['experiences']:
                if exp.get('skill'):
                    text_parts.append(exp['skill'])
                if exp.get('description'):
                    text_parts.append(exp['description'])
        
        if candidate_data.get('skills'):
            if isinstance(candidate_data['skills'], list):
                text_parts.extend(candidate_data['skills'])
            else:
                text_parts.append(str(candidate_data['skills']))
        
        return ' '.join(text_parts)
    
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
