from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service with specified model
        
        Args:
            model_name: HuggingFace model name for sentence embeddings
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array of embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of input texts
            
        Returns:
            List of numpy arrays (embeddings)
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        
        if not valid_texts:
            raise ValueError("No valid texts provided")
        
        try:
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
            return list(embeddings)
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def generate_job_embedding(self, job_title: str, job_description: str, domain: str = "") -> np.ndarray:
        """
        Generate embedding for job data
        
        Args:
            job_title: Job title
            job_description: Job description
            domain: Job domain/category
            
        Returns:
            numpy array of job embedding
        """
        # Combine job information for embedding
        job_text = f"Title: {job_title}. Domain: {domain}. Description: {job_description}"
        return self.generate_embedding(job_text)
    
    def generate_candidate_embedding(self, summary: str, experiences: List[dict]) -> np.ndarray:
        """
        Generate embedding for candidate profile
        
        Args:
            summary: Candidate summary
            experiences: List of experience dictionaries with 'skill', 'years', 'description'
            
        Returns:
            numpy array of candidate embedding
        """
        # Combine candidate information
        experience_text = ""
        for exp in experiences:
            exp_text = f"Skill: {exp.get('skill', '')}. Years: {exp.get('years', 0)}. Description: {exp.get('description', '')}. "
            experience_text += exp_text
        
        candidate_text = f"Summary: {summary}. Experience: {experience_text}"
        return self.generate_embedding(candidate_text)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of generated embeddings"""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        return self.model.get_sentence_embedding_dimension()

# Global instance
embedding_service = EmbeddingService()
