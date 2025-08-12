import faiss
import numpy as np
import pickle
import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import shutil
from pathlib import Path
import asyncio
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from config.security import SecurityConfig

logger = logging.getLogger(__name__)

@dataclass
class IndexMetadata:
    """Metadata for FAISS index"""
    version: str
    created_at: datetime
    last_updated: datetime
    total_vectors: int
    dimension: int
    index_type: str
    model_name: str
    quality_score: float
    build_time: float
    backup_count: int = 0

class PersistentFAISSIndexManager:
    """Persistent FAISS index manager with versioning and monitoring"""
    
    def __init__(self, index_dir: str = "embeddings/faiss_index"):
        self.index_dir = Path(index_dir)
        # Handle case where directory already exists
        try:
            self.index_dir.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            # Directory already exists, which is fine
            pass
        
        # Redis for distributed coordination
        self.redis_client = redis.from_url(SecurityConfig.REDIS_URL, decode_responses=True)
        
        # Index configuration
        self.index_type = "IVFFlat"  # Can be changed to other types
        self.nlist = 100  # Number of clusters for IVF
        self.nprobe = 10  # Number of clusters to probe during search
        
        # Performance monitoring
        self.search_times = []
        self.add_times = []
        self.max_history_size = 1000
        
        # Current index state
        self.index = None
        self.metadata = None
        self.vector_ids = {}  # Map vector_id to index position
        self.reverse_map = {}  # Map index position to vector_id
        
        logger.info(f"Initialized PersistentFAISSIndexManager with index directory: {self.index_dir}")
    
    def _get_index_path(self, version: str = None) -> Path:
        """Get index file path for version"""
        if version is None:
            return self.index_dir / "current_index.faiss"
        return self.index_dir / f"index_v{version}.faiss"
    
    def _get_metadata_path(self, version: str = None) -> Path:
        """Get metadata file path for version"""
        if version is None:
            return self.index_dir / "current_metadata.json"
        return self.index_dir / f"metadata_v{version}.json"
    
    def _get_backup_path(self, version: str) -> Path:
        """Get backup directory path for version"""
        return self.index_dir / "backups" / f"v{version}"
    
    async def create_index(self, dimension: int, index_type: str = None) -> bool:
        """Create a new FAISS index"""
        try:
            index_type = index_type or self.index_type
            
            if index_type == "IVFFlat":
                # Create quantizer
                quantizer = faiss.IndexFlatL2(dimension)
                self.index = faiss.IndexIVFFlat(quantizer, dimension, self.nlist)
                self.index.nprobe = self.nprobe
            elif index_type == "Flat":
                self.index = faiss.IndexFlatL2(dimension)
            else:
                raise ValueError(f"Unsupported index type: {index_type}")
            
            # Initialize metadata
            self.metadata = IndexMetadata(
                version=self._generate_version(),
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                total_vectors=0,
                dimension=dimension,
                index_type=index_type,
                model_name="all-MiniLM-L6-v2",
                quality_score=0.0,
                build_time=0.0
            )
            
            # Save initial index
            await self._save_index()
            
            logger.info(f"Created new FAISS index: {index_type}, dimension: {dimension}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False
    
    def _generate_version(self) -> str:
        """Generate version string based on timestamp"""
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    async def _save_index(self) -> bool:
        """Save current index and metadata"""
        try:
            if self.index is None or self.metadata is None:
                return False
            
            # Save index
            index_path = self._get_index_path(self.metadata.version)
            faiss.write_index(self.index, str(index_path))
            
            # Save metadata
            metadata_path = self._get_metadata_path(self.metadata.version)
            with open(metadata_path, 'w') as f:
                json.dump(asdict(self.metadata), f, default=str)
            
            # Update current index symlink
            current_index_path = self._get_index_path()
            current_metadata_path = self._get_metadata_path()
            
            if current_index_path.exists():
                current_index_path.unlink()
            if current_metadata_path.exists():
                current_metadata_path.unlink()
            
            os.symlink(index_path, current_index_path)
            os.symlink(metadata_path, current_metadata_path)
            
            # Update Redis with current version
            await self.redis_client.set("faiss:current_version", self.metadata.version)
            await self.redis_client.set("faiss:last_updated", datetime.utcnow().isoformat())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False
    
    async def load_index(self, version: str = None) -> bool:
        """Load FAISS index from disk"""
        try:
            # Determine version to load
            if version is None:
                # Try to load current version
                current_version = await self.redis_client.get("faiss:current_version")
                if current_version:
                    version = current_version
                else:
                    # Load latest available version
                    metadata_files = list(self.index_dir.glob("metadata_v*.json"))
                    if not metadata_files:
                        return False
                    latest_file = max(metadata_files, key=lambda x: x.stat().st_mtime)
                    version = latest_file.stem.replace("metadata_v", "")
            
            # Load index
            index_path = self._get_index_path(version)
            if not index_path.exists():
                logger.error(f"Index file not found: {index_path}")
                return False
            
            self.index = faiss.read_index(str(index_path))
            
            # Load metadata
            metadata_path = self._get_metadata_path(version)
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata_dict = json.load(f)
                    self.metadata = IndexMetadata(**metadata_dict)
            else:
                logger.warning(f"Metadata file not found for version: {version}")
                return False
            
            # Load vector mappings
            mapping_path = self.index_dir / f"mapping_v{version}.pkl"
            if mapping_path.exists():
                with open(mapping_path, 'rb') as f:
                    mapping_data = pickle.load(f)
                    self.vector_ids = mapping_data.get('vector_ids', {})
                    self.reverse_map = mapping_data.get('reverse_map', {})
            
            logger.info(f"Loaded FAISS index version {version} with {self.metadata.total_vectors} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    async def add_vectors(self, vectors: List[np.ndarray], vector_ids: List[str]) -> bool:
        """Add vectors to the index with batching"""
        try:
            if self.index is None:
                logger.error("No index loaded")
                return False
            
            start_time = time.time()
            
            # Convert to numpy array if needed
            if not isinstance(vectors, np.ndarray):
                vectors = np.array(vectors)
            
            # Normalize vectors
            faiss.normalize_L2(vectors)
            
            # Add vectors to index
            if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                # Train the index if needed
                self.index.train(vectors)
            
            # Add vectors
            self.index.add(vectors)
            
            # Update mappings
            start_idx = len(self.vector_ids)
            for i, vector_id in enumerate(vector_ids):
                self.vector_ids[vector_id] = start_idx + i
                self.reverse_map[start_idx + i] = vector_id
            
            # Update metadata
            self.metadata.total_vectors += len(vectors)
            self.metadata.last_updated = datetime.utcnow()
            
            # Save updated index
            await self._save_index()
            
            # Save mappings
            mapping_path = self.index_dir / f"mapping_v{self.metadata.version}.pkl"
            with open(mapping_path, 'wb') as f:
                pickle.dump({
                    'vector_ids': self.vector_ids,
                    'reverse_map': self.reverse_map
                }, f)
            
            add_time = time.time() - start_time
            self.add_times.append(add_time)
            if len(self.add_times) > self.max_history_size:
                self.add_times.pop(0)
            
            logger.info(f"Added {len(vectors)} vectors to index in {add_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            return False
    
    async def search_vectors(
        self, 
        query_vectors: np.ndarray, 
        k: int = 10,
        search_type: str = "similarity"
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            if self.index is None:
                logger.error("No index loaded")
                return []
            
            start_time = time.time()
            
            # Normalize query vectors
            if query_vectors.ndim == 1:
                query_vectors = query_vectors.reshape(1, -1)
            faiss.normalize_L2(query_vectors)
            
            # Perform search
            if search_type == "similarity":
                distances, indices = self.index.search(query_vectors, k)
            else:
                # For other search types, implement as needed
                distances, indices = self.index.search(query_vectors, k)
            
            # Process results
            results = []
            for i, (dist_vec, idx_vec) in enumerate(zip(distances, indices)):
                query_results = []
                for dist, idx in zip(dist_vec, idx_vec):
                    if idx != -1:  # Valid result
                        vector_id = self.reverse_map.get(idx, f"unknown_{idx}")
                        query_results.append({
                            'vector_id': vector_id,
                            'distance': float(dist),
                            'similarity': float(1.0 / (1.0 + dist)),
                            'index_position': int(idx)
                        })
                results.append(query_results)
            
            search_time = time.time() - start_time
            self.search_times.append(search_time)
            if len(self.search_times) > self.max_history_size:
                self.search_times.pop(0)
            
            return results[0] if len(results) == 1 else results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
    async def create_backup(self, version: str = None) -> bool:
        """Create a backup of the current index"""
        try:
            version = version or self.metadata.version
            backup_dir = self._get_backup_path(version)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy index file
            index_path = self._get_index_path(version)
            backup_index_path = backup_dir / "index.faiss"
            shutil.copy2(index_path, backup_index_path)
            
            # Copy metadata
            metadata_path = self._get_metadata_path(version)
            backup_metadata_path = backup_dir / "metadata.json"
            shutil.copy2(metadata_path, backup_metadata_path)
            
            # Copy mappings
            mapping_path = self.index_dir / f"mapping_v{version}.pkl"
            if mapping_path.exists():
                backup_mapping_path = backup_dir / "mapping.pkl"
                shutil.copy2(mapping_path, backup_mapping_path)
            
            # Update backup count
            self.metadata.backup_count += 1
            await self._save_index()
            
            logger.info(f"Created backup for version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    async def restore_backup(self, version: str) -> bool:
        """Restore index from backup"""
        try:
            backup_dir = self._get_backup_path(version)
            if not backup_dir.exists():
                logger.error(f"Backup not found for version: {version}")
                return False
            
            # Restore index
            backup_index_path = backup_dir / "index.faiss"
            restored_index_path = self._get_index_path(version)
            shutil.copy2(backup_index_path, restored_index_path)
            
            # Restore metadata
            backup_metadata_path = backup_dir / "metadata.json"
            restored_metadata_path = self._get_metadata_path(version)
            shutil.copy2(backup_metadata_path, restored_metadata_path)
            
            # Load the restored index
            return await self.load_index(version)
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get comprehensive index statistics"""
        try:
            stats = {
                "index_loaded": self.index is not None,
                "total_vectors": self.metadata.total_vectors if self.metadata else 0,
                "dimension": self.metadata.dimension if self.metadata else 0,
                "index_type": self.metadata.index_type if self.metadata else None,
                "current_version": self.metadata.version if self.metadata else None,
                "last_updated": self.metadata.last_updated.isoformat() if self.metadata else None,
                "backup_count": self.metadata.backup_count if self.metadata else 0,
                "performance": {
                    "avg_search_time": np.mean(self.search_times) if self.search_times else 0.0,
                    "avg_add_time": np.mean(self.add_times) if self.add_times else 0.0,
                    "search_count": len(self.search_times),
                    "add_count": len(self.add_times)
                }
            }
            
            # Add Redis stats
            try:
                current_version = await self.redis_client.get("faiss:current_version")
                last_updated = await self.redis_client.get("faiss:last_updated")
                stats["redis"] = {
                    "current_version": current_version,
                    "last_updated": last_updated
                }
            except Exception as e:
                stats["redis"] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_versions(self, keep_versions: int = 5) -> bool:
        """Clean up old index versions, keeping only the most recent ones"""
        try:
            # Get all metadata files
            metadata_files = list(self.index_dir.glob("metadata_v*.json"))
            if len(metadata_files) <= keep_versions:
                return True
            
            # Sort by modification time
            metadata_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the most recent versions
            files_to_keep = metadata_files[:keep_versions]
            files_to_delete = metadata_files[keep_versions:]
            
            # Delete old files
            for metadata_file in files_to_delete:
                version = metadata_file.stem.replace("metadata_v", "")
                
                # Delete index file
                index_file = self._get_index_path(version)
                if index_file.exists():
                    index_file.unlink()
                
                # Delete metadata file
                metadata_file.unlink()
                
                # Delete mapping file
                mapping_file = self.index_dir / f"mapping_v{version}.pkl"
                if mapping_file.exists():
                    mapping_file.unlink()
                
                # Delete backup directory
                backup_dir = self._get_backup_path(version)
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                
                logger.info(f"Cleaned up old version: {version}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old versions: {e}")
            return False

# Global index manager instance
index_manager = PersistentFAISSIndexManager()
