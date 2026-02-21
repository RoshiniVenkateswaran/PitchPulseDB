from typing import List, Dict, Any, Optional
import numpy as np
import json
import logging
import os

logger = logging.getLogger(__name__)


class VectorStoreBase:
    """Base interface for vector storage backends."""

    def upsert(self, doc_id: str, text: str, embedding: Optional[List[float]] = None,
               metadata: Optional[Dict[str, Any]] = None):
        """
        Upsert a document. If `embedding` is provided (from Keerthi's embed_text()),
        use it directly. Otherwise fall back to internal mock embedding.
        """
        pass

    def search(self, query_text: str, query_embedding: Optional[List[float]] = None,
               k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents. If `query_embedding` is provided (from embed_text()),
        use it directly. Otherwise fall back to internal mock embedding.
        """
        pass


class ActianVectorAI(VectorStoreBase):
    """
    Client for Actian VectorAI DB.
    In a real implementation, this would connect to the Actian DB
    and execute vector insertion and retrieval queries using their Python SDK or REST API.
    """

    def __init__(self, db_url: str, token: Optional[str] = None):
        self.db_url = db_url
        self.token = token
        self.docs = []  # In-memory fallback until real SDK is wired
        logger.info(f"Initialized Actian VectorAI DB client at {db_url}")

    def upsert(self, doc_id: str, text: str, embedding: Optional[List[float]] = None,
               metadata: Optional[Dict[str, Any]] = None):
        # TODO: Replace with actual Actian SDK/REST call
        # For now, store in memory so the demo works
        self.docs.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {},
            "embedding": np.array(embedding) if embedding else self._mock_embed(text)
        })
        logger.info(f"Upserted doc {doc_id} to Actian VectorAI DB (in-memory mode)")

    def search(self, query_text: str, query_embedding: Optional[List[float]] = None,
               k: int = 5) -> List[Dict[str, Any]]:
        # TODO: Replace with actual Actian SDK/REST call
        if not self.docs:
            return []
        q_vec = np.array(query_embedding) if query_embedding else self._mock_embed(query_text)
        q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-10)
        scored = []
        for doc in self.docs:
            d_vec = doc["embedding"]
            d_vec = d_vec / (np.linalg.norm(d_vec) + 1e-10)
            sim = float(np.dot(q_vec, d_vec))
            scored.append((sim, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"similarity": sim, "metadata": doc["metadata"], "text": doc["text"]}
            for sim, doc in scored[:k]
        ]

    def _mock_embed(self, text: str) -> np.ndarray:
        np.random.seed(len(text) % (2 ** 31))
        vec = np.random.rand(128)
        return vec / np.linalg.norm(vec)


class LocalFallbackVectorStore(VectorStoreBase):
    """
    Fallback in-memory cosine similarity store for hackathon dev safety.
    Works with both real Gemini embeddings (3072-dim) and mock embeddings.
    """

    def __init__(self):
        self.docs = []

    def _mock_embed(self, text: str) -> np.ndarray:
        np.random.seed(len(text) % (2 ** 31))
        vec = np.random.rand(128)
        return vec / np.linalg.norm(vec)

    def upsert(self, doc_id: str, text: str, embedding: Optional[List[float]] = None,
               metadata: Optional[Dict[str, Any]] = None):
        if embedding is not None:
            emb = np.array(embedding)
        else:
            emb = self._mock_embed(text)

        # Remove existing doc with same id (update semantics)
        self.docs = [d for d in self.docs if d["id"] != doc_id]

        self.docs.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {},
            "embedding": emb
        })
        logger.info(f"Upserted document {doc_id} into LocalFallbackVectorStore (dim={len(emb)})")

    def search(self, query_text: str, query_embedding: Optional[List[float]] = None,
               k: int = 5) -> List[Dict[str, Any]]:
        if not self.docs:
            return []

        if query_embedding is not None:
            q_vec = np.array(query_embedding)
        else:
            q_vec = self._mock_embed(query_text)

        q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-10)

        scored = []
        for doc in self.docs:
            d_vec = doc["embedding"]
            # Handle dimension mismatch (mock 128 vs real 3072) gracefully
            if len(q_vec) != len(d_vec):
                # Can't compare different dims; assign low similarity
                scored.append((0.1, doc))
                continue
            d_vec = d_vec / (np.linalg.norm(d_vec) + 1e-10)
            sim = float(np.dot(q_vec, d_vec))
            scored.append((sim, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"similarity": sim, "metadata": doc["metadata"], "text": doc["text"]}
            for sim, doc in scored[:k]
        ]


# ---------------------------------------------------------------------------
# Singleton instance initialized based on settings
# ---------------------------------------------------------------------------
from backend.core.config import settings

if settings.VECTOR_DB_URL:
    vector_db = ActianVectorAI(settings.VECTOR_DB_URL, settings.VECTOR_DB_TOKEN)
else:
    logger.warning("No VECTOR_DB_URL provided, using LocalFallbackVectorStore")
    vector_db = LocalFallbackVectorStore()

# Seed playbook docs for demo (these use mock embeddings since they're static text)
vector_db.upsert(
    doc_id="playbook_1",
    text="When acute load spikes significantly (ACWR > 1.5), the player is in the danger zone. The recommendation is always to reduce training volume, avoid high-speed running drills, and potentially rest for the upcoming fixture.",
    metadata={"source": "Medical Playbook", "topic": "ACWR Spikes"}
)
vector_db.upsert(
    doc_id="playbook_2",
    text="A low acute load (ACWR < 0.8) indicates the player is under-prepared. The action plan should gradually increase match load, starting with 45 minutes in lower stakes games before demanding full 90-minute performances.",
    metadata={"source": "Medical Playbook", "topic": "Under-prepared"}
)
vector_db.upsert(
    doc_id="playbook_3",
    text="Winger Protocol: If Sprint Distance exceeds baseline by 20%+, limit subsequent Match Day -2 technical drills. Monitor hamstring tightness indicators pre and post session.",
    metadata={"source": "Medical Playbook", "topic": "Winger Sprint Protocol"}
)


def get_embedding_safe(text: str) -> Optional[List[float]]:
    """
    Attempt to generate a real Gemini embedding via Keerthi's module.
    Returns None if GEMINI_API_KEY is not set or embedding fails.
    """
    if not settings.GEMINI_API_KEY:
        return None
    try:
        from backend.ai.embeddings import embed_text
        return embed_text(text)
    except Exception as e:
        logger.warning(f"Real embedding failed, falling back to mock: {e}")
        return None
