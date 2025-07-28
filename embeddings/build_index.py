import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FAISSIndexManager:
    """Manages FAISS vector index for semantic search"""
    
    def __init__(self, dimension: int = 384, index_type: str = "cosine"):
        """
        Initialize FAISS index manager
        
        Args:
            dimension: Dimension of embedding vectors
            index_type: Type of similarity ('cosine', 'l2', 'ip')
        """
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.id_to_index = {}  # Maps entity ID to FAISS index position
        self.index_to_id = {}  # Maps FAISS index position to entity ID
        self.index_path = Path("embeddings/faiss_index")
        self.metadata_path = Path("embeddings/index_metadata.pkl")
        
        self._create_index()
    
    def _create_index(self):
        """Create FAISS index based on similarity type"""
        if self.index_type == "cosine":
            # Normalize vectors for cosine similarity
            self.index = faiss.IndexFlatIP(self.dimension)
        elif self.index_type == "l2":
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "ip":
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        logger.info(f"Created FAISS index: {self.index_type}, dimension: {self.dimension}")
    
    def add_vectors(self, vectors: List[np.ndarray], ids: List[int], entity_type: str = "job"):
        """
        Add vectors to the index
        
        Args:
            vectors: List of embedding vectors
            ids: List of entity IDs
            entity_type: Type of entity ('job', 'candidate')
        """
        if len(vectors) != len(ids):
            raise ValueError("Number of vectors must match number of IDs")
        
        if not vectors:
            return
        
        # Convert to numpy array
        vectors_array = np.array(vectors, dtype=np.float32)
        
        # Normalize for cosine similarity if needed
        if self.index_type == "cosine":
            faiss.normalize_L2(vectors_array)
        
        # Add to index
        start_idx = self.index.ntotal
        self.index.add(vectors_array)
        
        # Update ID mappings
        for i, entity_id in enumerate(ids):
            faiss_idx = start_idx + i
            self.id_to_index[f"{entity_type}_{entity_id}"] = faiss_idx
            self.index_to_id[faiss_idx] = {"id": entity_id, "type": entity_type}
        
        logger.info(f"Added {len(vectors)} {entity_type} vectors to index")
    
    def search(self, query_vector: np.ndarray, k: int = 10, entity_type: Optional[str] = None) -> List[Tuple[int, float]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            entity_type: Filter by entity type ('job', 'candidate')
            
        Returns:
            List of (entity_id, similarity_score) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        # Normalize query vector for cosine similarity
        if self.index_type == "cosine":
            query_vector = query_vector.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(query_vector)
        else:
            query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        # Search
        scores, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
            
            entity_info = self.index_to_id.get(idx)
            if entity_info is None:
                continue
            
            # Filter by entity type if specified
            if entity_type and entity_info["type"] != entity_type:
                continue
            
            results.append((entity_info["id"], float(score)))
        
        return results
    
    def remove_vectors(self, ids: List[int], entity_type: str = "job"):
        """
        Remove vectors from index (recreate index without specified IDs)
        
        Args:
            ids: List of entity IDs to remove
            entity_type: Type of entity
        """
        if not ids:
            return
        
        # Get all vectors except those to be removed
        all_vectors = []
        all_ids = []
        all_entity_types = []
        
        for faiss_idx in range(self.index.ntotal):
            entity_info = self.index_to_id.get(faiss_idx)
            if entity_info is None:
                continue
            
            entity_id = entity_info["id"]
            entity_type_info = entity_info["type"]
            
            # Skip if this entity should be removed
            if entity_type_info == entity_type and entity_id in ids:
                continue
            
            # Get vector from index (this is simplified - in practice you'd need to store vectors)
            all_vectors.append(self._get_vector_at_index(faiss_idx))
            all_ids.append(entity_id)
            all_entity_types.append(entity_type_info)
        
        # Recreate index
        self._create_index()
        self.id_to_index.clear()
        self.index_to_id.clear()
        
        # Re-add remaining vectors
        if all_vectors:
            self.add_vectors(all_vectors, all_ids, all_entity_types[0])
        
        logger.info(f"Removed {len(ids)} {entity_type} vectors from index")
    
    def _get_vector_at_index(self, idx: int) -> np.ndarray:
        """Get vector at specific index (simplified implementation)"""
        # This is a simplified version - in practice you'd need to store vectors separately
        # or use a more complex FAISS index that supports reconstruction
        raise NotImplementedError("Vector reconstruction not implemented")
    
    def save_index(self):
        """Save index and metadata to disk"""
        os.makedirs(self.index_path.parent, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        
        # Save metadata
        metadata = {
            "id_to_index": self.id_to_index,
            "index_to_id": self.index_to_id,
            "dimension": self.dimension,
            "index_type": self.index_type
        }
        
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Saved FAISS index to {self.index_path}")
    
    def load_index(self):
        """Load index and metadata from disk"""
        if not self.index_path.exists() or not self.metadata_path.exists():
            logger.warning("Index files not found, creating new index")
            return
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.id_to_index = metadata["id_to_index"]
            self.index_to_id = metadata["index_to_id"]
            self.dimension = metadata["dimension"]
            self.index_type = metadata["index_type"]
            
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            self._create_index()
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        stats = {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "entity_counts": {}
        }
        
        # Count entities by type
        for entity_info in self.index_to_id.values():
            entity_type = entity_info["type"]
            stats["entity_counts"][entity_type] = stats["entity_counts"].get(entity_type, 0) + 1
        
        return stats

# Global instance
faiss_manager = FAISSIndexManager()
