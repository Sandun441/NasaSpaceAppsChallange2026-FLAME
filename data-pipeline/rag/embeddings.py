"""
NASA FLAME — Local Semantic Embedding Service (Phase R2)
Generates, persists, and queries local dense vector embeddings for scientific knowledge records.
Preferred model: sentence-transformers/all-MiniLM-L6-v2 (384-dimensional dense vectors).
Uses pure NumPy cosine similarity for fast, dependency-light in-memory retrieval.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import json
import logging
import numpy as np

logger = logging.getLogger("flame.rag.embeddings")

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EXPECTED_DIMENSION = 384


class LocalEmbeddingService:
    """
    Manages local dense vector embeddings for scientific knowledge records.
    Provides deterministic indexing, cache invalidation via SHA256 fingerprints,
    and fast cosine similarity ranking via NumPy.
    """

    def __init__(
        self,
        base_dir: Path,
        model_name: str = DEFAULT_MODEL_NAME,
        batch_size: int = 32,
    ):
        self.base_dir = Path(base_dir).resolve()
        self.rag_dir = self.base_dir / "processed_data" / "rag"
        self.rag_dir.mkdir(parents=True, exist_ok=True)

        self.model_name = model_name
        self.batch_size = batch_size
        self.expected_dim = EXPECTED_DIMENSION

        self.embeddings_path = self.rag_dir / "embeddings.npy"
        self.manifest_path = self.rag_dir / "embeddings_manifest.json"
        self.records_path = self.rag_dir / "scientific_knowledge_records.json"

        self._model = None
        self._embeddings: Optional[np.ndarray] = None
        self._record_ids: List[str] = []
        self._id_to_index: Dict[str, int] = {}
        self._manifest: Dict[str, Any] = {}
        self.is_ready = False

    def get_model(self):
        """Lazy loader for SentenceTransformer model to prevent startup latency."""
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading local embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            return self._model
        except ImportError as e:
            logger.warning("sentence-transformers not installed: %s", e)
            return None
        except Exception as e:
            logger.error("Failed to load sentence-transformers model %s: %s", self.model_name, e)
            return None

    def compute_records_fingerprint(self, records: Optional[List[Dict[str, Any]]] = None) -> str:
        """Compute SHA256 hash of the scientific knowledge records for cache validation."""
        if self.records_path.is_file():
            hasher = hashlib.sha256()
            with open(self.records_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()

        if records is not None:
            serialized = json.dumps(
                [{"id": r.get("record_id"), "text": r.get("searchable_text", "")} for r in records],
                sort_keys=True
            ).encode("utf-8")
            return hashlib.sha256(serialized).hexdigest()

        return ""

    def is_index_ready(self) -> bool:
        """Check if precomputed embeddings exist, match current records, and are valid."""
        if not self.embeddings_path.is_file() or not self.manifest_path.is_file():
            return False

        try:
            with open(self.manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)

            current_fingerprint = self.compute_records_fingerprint()
            if manifest.get("records_sha256") != current_fingerprint:
                logger.info("Records content changed; index requires rebuilding.")
                return False

            if manifest.get("embedding_dimension") != self.expected_dim:
                return False

            return True
        except Exception:
            return False

    def load_index(self) -> bool:
        """Load precomputed embeddings and manifest into memory."""
        if not self.is_index_ready():
            return False

        try:
            with open(self.manifest_path, encoding="utf-8") as f:
                self._manifest = json.load(f)

            self._record_ids = self._manifest.get("record_ids", [])
            self._id_to_index = {rid: i for i, rid in enumerate(self._record_ids)}
            self._embeddings = np.load(self.embeddings_path)

            if self._embeddings.shape[0] != len(self._record_ids):
                logger.error("Embedding count mismatch: %d rows vs %d IDs",
                             self._embeddings.shape[0], len(self._record_ids))
                return False

            if self._embeddings.shape[1] != self.expected_dim:
                logger.error("Embedding dimension mismatch: %d vs expected %d",
                             self._embeddings.shape[1], self.expected_dim)
                return False

            self.is_ready = True
            logger.info("Successfully loaded %d semantic embeddings (dim=%d)",
                        len(self._record_ids), self.expected_dim)
            return True
        except Exception as e:
            logger.error("Failed to load embeddings index: %s", e)
            self.is_ready = False
            return False

    def build_index(
        self,
        records: List[Dict[str, Any]],
        force_rebuild: bool = False
    ) -> Dict[str, Any]:
        """
        Generate dense embeddings for all records using searchable_text,
        normalize to unit length (L2 norm), and persist to disk.
        """
        fingerprint = self.compute_records_fingerprint(records)

        # Check if rebuild is needed
        if not force_rebuild and self.is_index_ready():
            self.load_index()
            return {
                "status": "cached",
                "record_count": len(self._record_ids),
                "embedding_dimension": self.expected_dim,
                "manifest": self._manifest,
            }

        model = self.get_model()
        if model is None:
            raise RuntimeError(
                f"Embedding model '{self.model_name}' could not be loaded. "
                "Ensure sentence-transformers is installed."
            )

        record_ids = [r["record_id"] for r in records]
        texts = [r.get("searchable_text", r.get("title", "")) for r in records]

        logger.info("Encoding %d scientific records using %s...", len(texts), self.model_name)
        raw_embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization ensures dot product == cosine similarity
        )

        embeddings_array = np.asarray(raw_embeddings, dtype=np.float32)

        # Sanity check dimensions
        assert embeddings_array.shape[0] == len(records), "Row count mismatch"
        assert embeddings_array.shape[1] == self.expected_dim, f"Expected dim {self.expected_dim}"

        # Save to disk
        np.save(self.embeddings_path, embeddings_array)

        from datetime import datetime, timezone
        manifest = {
            "model_name": self.model_name,
            "embedding_dimension": self.expected_dim,
            "record_count": len(records),
            "records_sha256": fingerprint,
            "record_ids": record_ids,
            "generation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "is_l2_normalized": True,
        }

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        self._embeddings = embeddings_array
        self._record_ids = record_ids
        self._id_to_index = {rid: i for i, rid in enumerate(record_ids)}
        self._manifest = manifest
        self.is_ready = True

        logger.info("Semantic index successfully built: %d records saved to %s",
                    len(records), self.embeddings_path)

        return {
            "status": "generated",
            "record_count": len(records),
            "embedding_dimension": self.expected_dim,
            "manifest": manifest,
        }

    def embed_query(self, query: str) -> Optional[np.ndarray]:
        """Encode a single natural-language user query into an L2-normalized 384-d vector."""
        model = self.get_model()
        if model is None:
            return None

        clean_query = query.strip()
        if not clean_query:
            return None

        emb = model.encode([clean_query], convert_to_numpy=True, normalize_embeddings=True)
        return np.asarray(emb[0], dtype=np.float32)

    def similarity_search(
        self,
        query: str,
        candidate_ids: Optional[List[str]] = None,
        top_k: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Perform cosine similarity search against indexed records.
        Returns list of (record_id, similarity_score) sorted descending.
        """
        if not self.is_ready:
            if not self.load_index():
                return []

        query_vec = self.embed_query(query)
        if query_vec is None or self._embeddings is None:
            return []

        # Vectorized cosine similarity: dot product of L2 normalized vectors
        if candidate_ids is not None:
            indices = [self._id_to_index[cid] for cid in candidate_ids if cid in self._id_to_index]
            if not indices:
                return []
            sub_embeddings = self._embeddings[indices]
            scores = np.dot(sub_embeddings, query_vec)
            scored = list(zip([self._record_ids[i] for i in indices], [float(s) for s in scores]))
        else:
            scores = np.dot(self._embeddings, query_vec)
            scored = list(zip(self._record_ids, [float(s) for s in scores]))

        # Sort descending by score, tie-break deterministically by record_id
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored[:top_k]
