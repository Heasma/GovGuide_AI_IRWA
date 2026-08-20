"""
GovGuide AI — Hybrid Reciprocal Rank Fusion (RRF) Retriever

Combines lexical (BM25) and semantic retrieval rankings using
Reciprocal Rank Fusion (RRF):

    RRF(d) = Σ 1 / (k + rank(d))

where k defaults to 60 (configurable).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.retrieval.chunker import ServiceChunk
from app.retrieval.bm25_retriever import BM25Retriever, BM25Result
from app.retrieval.semantic_retriever import SemanticRetriever, SemanticResult


@dataclass
class HybridResult:
    """A combined result from hybrid lexical + semantic retrieval."""
    chunk_id: str
    service_id: str
    service_code: str
    service_name: str
    category: str
    section: str
    text: str
    bm25_score: float
    semantic_score: float
    rrf_score: float
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
            "bm25_score": self.bm25_score,
            "semantic_score": self.semantic_score,
            "rrf_score": self.rrf_score,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "source_confidence": self.source_confidence,
        }


class HybridRetriever:
    """
    Combines BM25 and Semantic retrievers using Reciprocal Rank Fusion.
    """

    def __init__(
        self,
        chunks: Optional[List[ServiceChunk]] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        semantic_retriever: Optional[SemanticRetriever] = None,
        rrf_k: Optional[int] = None,
    ):
        settings = get_settings()
        self.rrf_k = rrf_k if rrf_k is not None else settings.RRF_K

        self.bm25 = bm25_retriever or BM25Retriever()
        self.semantic = semantic_retriever or SemanticRetriever()

        if chunks:
            self.index(chunks)

    def index(self, chunks: List[ServiceChunk]) -> None:
        """Index chunks in both BM25 and semantic engines."""
        self.bm25.index(chunks)
        self.semantic.index(chunks)

    def search(
        self,
        query: str,
        top_k: int = 10,
        candidate_multiplier: int = 3,
    ) -> List[HybridResult]:
        """
        Execute hybrid search using Reciprocal Rank Fusion (RRF).

        1. Retrieve top candidates from BM25 and Semantic retriever.
        2. Assign reciprocal rank scores: 1 / (k + rank) where rank is 1-indexed.
        3. Accumulate RRF scores per chunk.
        4. Sort descending by fused RRF score and return top_k.
        """
        if not query or not query.strip():
            return []

        # Retrieve a broader candidate pool from both retrievers
        candidate_k = max(top_k * candidate_multiplier, 20)
        bm25_results = self.bm25.search(query, top_k=candidate_k)
        semantic_results = self.semantic.search(query, top_k=candidate_k)

        if not bm25_results and not semantic_results:
            return []

        # Map chunk_id to candidate objects & metadata
        chunk_map: Dict[str, Any] = {}
        bm25_scores: Dict[str, float] = {}
        semantic_scores: Dict[str, float] = {}
        rrf_scores: Dict[str, float] = {}

        # Process BM25 ranks (1-based)
        for rank, res in enumerate(bm25_results, start=1):
            cid = res.chunk_id
            chunk_map[cid] = res
            bm25_scores[cid] = res.score
            rrf_score = 1.0 / (self.rrf_k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score

        # Process Semantic ranks (1-based)
        for rank, res in enumerate(semantic_results, start=1):
            cid = res.chunk_id
            if cid not in chunk_map:
                chunk_map[cid] = res
            semantic_scores[cid] = res.score
            rrf_score = 1.0 / (self.rrf_k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score

        # Sort all unique candidates by accumulated RRF score descending
        sorted_chunk_ids = sorted(
            rrf_scores.keys(),
            key=lambda cid: rrf_scores[cid],
            reverse=True,
        )

        hybrid_results: List[HybridResult] = []
        for cid in sorted_chunk_ids[:top_k]:
            meta = chunk_map[cid]
            hybrid_results.append(
                HybridResult(
                    chunk_id=meta.chunk_id,
                    service_id=meta.service_id,
                    service_code=meta.service_code,
                    service_name=meta.service_name,
                    category=meta.category,
                    section=meta.section,
                    text=meta.text,
                    bm25_score=round(bm25_scores.get(cid, 0.0), 4),
                    semantic_score=round(semantic_scores.get(cid, 0.0), 4),
                    rrf_score=round(rrf_scores[cid], 6),
                    source_id=meta.source_id,
                    source_url=meta.source_url,
                    source_title=meta.source_title,
                    source_confidence=meta.source_confidence,
                )
            )

        return hybrid_results
