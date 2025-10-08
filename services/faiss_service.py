import logging
from typing import List, Dict, Any, Optional

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
import os

from embeddings.embedder import OptimizedEmbeddingService
from embeddings.build_index import index_manager
from db.crud.job import job as job_crud

logger = logging.getLogger(__name__)


class FaissService:
    """Service to manage FAISS indices and queries for recommendations."""

    def __init__(self):
        self.embedding_service = OptimizedEmbeddingService()
        self.jobs_index_ready: bool = False
        self.disabled: bool = os.getenv("DISABLE_FAISS", "0") in ("1", "true", "True")

    async def ensure_jobs_index(self, db: AsyncSession) -> bool:
        """Ensure the jobs FAISS index is built and loaded. Build lazily if missing."""
        try:
            if self.disabled:
                logger.info("FAISS disabled via DISABLE_FAISS env; skipping index ensure.")
                self.jobs_index_ready = False
                return True
            # If an index is already in memory with vectors, consider it ready
            if getattr(index_manager, "index", None) is not None and getattr(index_manager, "metadata", None):
                if getattr(index_manager.metadata, "total_vectors", 0) > 0:
                    self.jobs_index_ready = True
                    return True

            # Try to load the latest index version from disk
            loaded = await index_manager.load_index()
            if loaded and getattr(index_manager.metadata, "total_vectors", 0) > 0:
                self.jobs_index_ready = True
                logger.info("FAISS jobs index loaded from disk")
                return True

            # Build a fresh index from active jobs
            logger.info("Building FAISS jobs index from active jobs")
            await self.build_jobs_index(db)
            self.jobs_index_ready = True
            return True
        except Exception as e:
            logger.error(f"Failed to ensure jobs index: {e}")
            self.jobs_index_ready = False
            return False

    async def build_jobs_index(self, db: AsyncSession, limit: int = 1000) -> None:
        """Build the jobs FAISS index from active jobs."""
        if self.disabled:
            logger.info("FAISS disabled; skipping build_jobs_index.")
            return
        # Fetch active jobs
        jobs = await job_crud.get_active_jobs(db, limit=limit)
        if not jobs:
            logger.warning("No active jobs found for FAISS index build")
            return

        # Generate job texts and embeddings
        job_texts: List[str] = []
        job_ids: List[int] = []
        for job in jobs:
            title = getattr(job, "title", "") or ""
            desc = getattr(job, "description", getattr(job, "job_description", "")) or ""
            company = getattr(job, "company", "") or ""
            domain = getattr(job, "domain", "") or ""
            location = getattr(job, "location", "") or ""
            job_texts.append(f"{title} {company} {location} {domain} {desc}")
            job_ids.append(getattr(job, "id", 0))

        # Batch embed
        embedding_results = await self.embedding_service.generate_embedding_batch(job_texts)
        vectors: List[np.ndarray] = []
        vector_ids: List[str] = []
        for job_id, result in zip(job_ids, embedding_results):
            if result.embedding is not None and result.quality_score > 0.0:
                vectors.append(result.embedding)
                vector_ids.append(f"job:{job_id}")

        if not vectors:
            logger.warning("No valid job embeddings to add to FAISS index")
            return

        # Create index with proper dimension
        dimension = len(vectors[0])
        created = await index_manager.create_index(dimension=dimension)
        if not created:
            logger.error("Failed to create FAISS index for jobs")
            return

        # Add vectors
        success = await index_manager.add_vectors(np.array(vectors), vector_ids)
        if success:
            logger.info(f"Added {len(vectors)} job vectors to FAISS index")
        else:
            logger.error("Failed to add job vectors to FAISS index")

    async def search_jobs_for_candidate(
        self, db: AsyncSession, candidate_id: int, k: int = 50
    ) -> List[Dict[str, Any]]:
        """Return FAISS search results for a candidate against jobs index."""
        try:
            if self.disabled:
                logger.info("FAISS disabled; returning empty FAISS results.")
                return []
            ready = await self.ensure_jobs_index(db)
            if not ready:
                return []

            # Build candidate text similar to semantic service
            from models.candidate import Candidate
            from sqlalchemy import select

            result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
            candidate = result.scalar_one_or_none()
            if not candidate:
                return []

            candidate_text = f"{getattr(candidate, 'summary', '')} {getattr(candidate, 'domain', '')} {getattr(candidate, 'role', '')}"
            # Generate embedding
            emb_results = await self.embedding_service.generate_embedding_batch([candidate_text])
            if not emb_results or emb_results[0].embedding is None:
                return []
            query_vec = np.array(emb_results[0].embedding, dtype=np.float32)

            # Search
            results = await index_manager.search_vectors(query_vec, k=k, search_type="similarity")
            return results or []
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []

    async def add_or_update_job(self, db: AsyncSession, job_id: int) -> bool:
        """Add or update a single job vector in the FAISS index (append-only if update)."""
        try:
            if self.disabled:
                logger.info(f"FAISS disabled; skipping add_or_update_job for {job_id}.")
                return True
            ready = await self.ensure_jobs_index(db)
            if not ready:
                return False

            job_obj = await job_crud.get(db, job_id)
            if not job_obj:
                return False

            title = getattr(job_obj, "title", "") or ""
            desc = getattr(job_obj, "description", getattr(job_obj, "job_description", "")) or ""
            company = getattr(job_obj, "company", "") or ""
            domain = getattr(job_obj, "domain", "") or ""
            location = getattr(job_obj, "location", "") or ""
            text = f"{title} {company} {location} {domain} {desc}"

            emb_results = await self.embedding_service.generate_embedding_batch([text])
            if not emb_results or emb_results[0].embedding is None:
                return False

            vectors = np.array([emb_results[0].embedding])
            vector_ids = [f"job:{job_id}"]
            ok = await index_manager.add_vectors(vectors, vector_ids)
            return ok
        except Exception as e:
            logger.error(f"Failed to add/update job {job_id} in FAISS: {e}")
            return False


# Global instance
faiss_service = FaissService()


