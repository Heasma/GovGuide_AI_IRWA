"""
GovGuide AI — Semantic Embedding & Vector Retrieval Interface

Defines the pluggable EmbeddingProvider abstract interface and a deterministic
local embedding provider for development & testing.

Design:
- Zero external API dependencies (no paid keys, no network calls).
- Deterministic and reproducible vectors.
- Cosine similarity matching between query and indexed document chunks.
- Replaceable in future phases with SentenceTransformers, OpenAI embeddings, or pgvector.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import hashlib
import math
import re
from typing import Any, Dict, List, Optional

from app.retrieval.chunker import ServiceChunk


class EmbeddingProvider(ABC):
    """
    Abstract interface for generating dense semantic vector embeddings.
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a normalized embedding vector for a single query text."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized embedding vectors for a list of document texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality."""
        pass


class LocalDeterministicEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic local embedding provider using hashed character & word n-grams
    with L2 normalization.

    Characteristics:
    - Fixed dimensional vector (default: 128 dimensions)
    - Subword and word n-gram feature hashing (handles spelling variations and morphology)
    - 100% deterministic: identical strings always yield identical vectors
    - Cosine similarity between related phrases is smooth and positive
    """

    def __init__(self, dimension: int = 128):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def _text_to_vector(self, text: str) -> List[float]:
        """Convert text to a dense L2-normalized float vector."""
        if not text or not text.strip():
            return [0.0] * self._dim

        vec = [0.0] * self._dim
        clean = text.lower().strip()

        # 1. Word tokens
        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", clean)
        for w in words:
            # Hash word to a bucket
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if ((h >> 4) % 2 == 0) else -1.0
            vec[idx] += 2.0 * sign

            # Word character trigrams for subword robustness
            padded = f"^{w}$"
            for i in range(len(padded) - 2):
                tri = padded[i : i + 3]
                th = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16)
                tidx = th % self._dim
                tsign = 1.0 if ((th >> 3) % 2 == 0) else -1.0
                vec[tidx] += 0.5 * tsign

        # 2. Character 4-grams across full string
        for i in range(len(clean) - 3):
            quad = clean[i : i + 4]
            qh = int(hashlib.sha1(quad.encode("utf-8")).hexdigest(), 16)
            qidx = qh % self._dim
            qsign = 1.0 if ((qh >> 2) % 2 == 0) else -1.0
            vec[qidx] += 0.25 * qsign

        # 3. L2 Normalize vector
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            return [round(x / norm, 6) for x in vec]
        return [0.0] * self._dim

    def embed_text(self, text: str) -> List[float]:
        return self._text_to_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two unit vectors (dot product)."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    return max(0.0, min(1.0, dot))


@dataclass
class SemanticResult:
    """A scored result from semantic retrieval."""
    chunk_id: str
    service_id: str
    service_code: str
    service_name: str
    category: str
    section: str
    text: str
    score: float
    source_id: str
    source_url: str
    source_title: str
    source_confidence: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "service_id": self.service_id,
            "service_code": self.service_code,
            "service_name": self.service_name,
            "category": self.category,
            "section": self.section,
            "text": self.text,
            "score": self.score,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "source_confidence": self.source_confidence,
        }


class SemanticRetriever:
    """
    Vector-based semantic retriever operating over ServiceChunk embeddings.
    """

    def __init__(
        self,
        chunks: Optional[List[ServiceChunk]] = None,
        provider: Optional[EmbeddingProvider] = None,
    ):
        self.provider = provider or LocalDeterministicEmbeddingProvider()
        self.chunks: List[ServiceChunk] = []
        self.embeddings: List[List[float]] = []

        if chunks:
            self.index(chunks)

    def index(self, chunks: List[ServiceChunk]) -> None:
        """Embed and index the provided ServiceChunk objects."""
        self.chunks = list(chunks)
        # Prepare rich embedding input string per chunk
        doc_texts = [
            f"{c.service_name} ({c.service_code}) - {c.category} - Section: {c.section}\n{c.text}"
            for c in self.chunks
        ]
        self.embeddings = self.provider.embed_documents(doc_texts)

    def search(self, query: str, top_k: int = 10) -> List[SemanticResult]:
        """
        Search indexed chunks by semantic cosine similarity.
        Returns top_k results sorted by score descending.
        """
        if not self.chunks or not query or not query.strip():
            return []

        query_vec = self.provider.embed_text(query)
        scored_candidates: List[tuple[int, float]] = []

        for idx, doc_vec in enumerate(self.embeddings):
            sim = cosine_similarity(query_vec, doc_vec)
            if sim > 0.01:
                scored_candidates.append((idx, sim))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        results: List[SemanticResult] = []
        for idx, sim in scored_candidates[:top_k]:
            chunk = self.chunks[idx]
            results.append(
                SemanticResult(
                    chunk_id=chunk.chunk_id,
                    service_id=chunk.service_id,
                    service_code=chunk.service_code,
                    service_name=chunk.service_name,
                    category=chunk.category,
                    section=chunk.section,
                    text=chunk.text,
                    score=round(sim, 4),
                    source_id=chunk.source_id,
                    source_url=chunk.source_url,
                    source_title=chunk.source_title,
                    source_confidence=chunk.source_confidence,
                )
            )

        return results
