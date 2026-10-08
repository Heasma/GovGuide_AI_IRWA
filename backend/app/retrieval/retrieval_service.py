"""
GovGuide AI — Retrieval Service

Coordinates the complete information retrieval pipeline:
1. Query preprocessing and normalization
2. BM25 lexical retrieval
3. Semantic vector retrieval
4. Hybrid Reciprocal Rank Fusion (RRF)
5. Source attribution validation
6. Structured EvidenceBundle assembly
"""

from typing import Any, Dict, List, Optional
import structlog

from app.config import get_settings
from app.nlp.preprocessor import preprocess, normalize_for_retrieval, expand_query
from app.nlp.intent_classifier import classify_intent
from app.retrieval.chunker import ServiceChunk
from app.retrieval.chunk_generator import generate_chunks_from_db
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.semantic_retriever import SemanticRetriever, LocalDeterministicEmbeddingProvider
from app.retrieval.hybrid_retriever import HybridRetriever, HybridResult
from app.retrieval.source_attribution import filter_attributed_results
from app.orchestrator.message_schema import (
    EvidenceBundle,
    EvidenceResult,
    SourceReference,
)

logger = structlog.get_logger(__name__)


class RetrievalService:
    """
    Unified service for information retrieval across the government service corpus.
    """

    def __init__(
        self,
        chunks: Optional[List[ServiceChunk]] = None,
        rrf_k: Optional[int] = None,
        auto_load: bool = True,
    ):
        settings = get_settings()
        self.top_k = settings.RETRIEVAL_TOP_K
        self.rrf_k = rrf_k or settings.RRF_K
        self.confidence_threshold = settings.RETRIEVAL_CONFIDENCE_THRESHOLD

        self.bm25_retriever = BM25Retriever(k1=settings.BM25_K1, b=settings.BM25_B)
        self.semantic_retriever = SemanticRetriever(provider=LocalDeterministicEmbeddingProvider())
        self.hybrid_retriever = HybridRetriever(
            bm25_retriever=self.bm25_retriever,
            semantic_retriever=self.semantic_retriever,
            rrf_k=self.rrf_k,
        )

        self._chunks: List[ServiceChunk] = []
        self._indexed = False

        if chunks:
            self.index(chunks)
        elif auto_load:
            self._try_load_db()

    def _try_load_db(self) -> None:
        """Attempt to load and index chunks from PostgreSQL at startup."""
        try:
            chunks = generate_chunks_from_db()
            if chunks:
                self.index(chunks)
                logger.info(
                    "retrieval_service_db_loaded",
                    chunks_count=len(chunks),
                )
        except Exception as exc:
            logger.warning(
                "retrieval_service_db_load_deferred",
                reason=str(exc),
            )

    def index(self, chunks: List[ServiceChunk]) -> None:
        """Index a corpus of ServiceChunk items."""
        self._chunks = list(chunks)
        self.hybrid_retriever.index(self._chunks)
        self._indexed = True
        logger.info("retrieval_service_indexed", chunk_count=len(self._chunks))

    @property
    def is_indexed(self) -> bool:
        return self._indexed and len(self._chunks) > 0

    @property
    def total_chunks(self) -> int:
        return len(self._chunks)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        mode: Optional[str] = None,
    ) -> EvidenceBundle:
        """
        Execute full retrieval pipeline and return an EvidenceBundle.

        Args:
            query:  Raw user query.
            top_k:  Number of results to retrieve (default: settings.RETRIEVAL_TOP_K).
            mode:   Retrieval mode ("hybrid" | "bm25" | "semantic").

        Returns:
            EvidenceBundle with verified source attribution and confidence score.
        """
        k = top_k or self.top_k
        clean_query = preprocess(query)
        expanded = expand_query(clean_query)
        from app.nlp.intent_classifier import classify_intent, classify_intents
        classified_intents = classify_intents(clean_query)
        intent = classified_intents[0].value if hasattr(classified_intents[0], "value") else str(classified_intents[0])
        intents_list = [i.value if hasattr(i, "value") else str(i) for i in classified_intents]

        if not self.is_indexed:
            self._try_load_db()

        if not clean_query or not self.is_indexed:
            return EvidenceBundle(
                query=query,
                intent=intent,
                intents=intents_list,
                total_retrieved=0,
                confidence=0.0,
                retrieval_method=mode or "hybrid",
                results=[],
                sources=[],
            )

        settings = get_settings()
        retrieval_mode = (mode or settings.RETRIEVAL_MODE).lower()

        # Execute search based on mode
        raw_candidates = []
        if retrieval_mode == "bm25":
            bm25_res = self.bm25_retriever.search(norm_query, top_k=k)
            for r in bm25_res:
                raw_candidates.append(r)
        elif retrieval_mode == "semantic":
            sem_res = self.semantic_retriever.search(expanded, top_k=k)
            for r in sem_res:
                raw_candidates.append(r)
        else:  # hybrid (default)
            retrieval_mode = "hybrid"
            hybrid_res = self.hybrid_retriever.search(expanded, top_k=k)
            for r in hybrid_res:
                raw_candidates.append(r)

        # ── Source Attribution Validation ─────────────────────────────────────
        attributed_candidates = filter_attributed_results(raw_candidates)

        # ── Assemble EvidenceResult items and SourceReferences ───────────────
        evidence_results: List[EvidenceResult] = []
        seen_source_ids = set()
        source_references: List[SourceReference] = []

        for item in attributed_candidates:
            # Determine score and retrieval method
            if isinstance(item, HybridResult):
                score = item.rrf_score
                method = "hybrid"
            elif hasattr(item, "score"):
                score = item.score
                method = retrieval_mode
            else:
                score = 0.0
                method = retrieval_mode

            result = EvidenceResult(
                chunk_id=item.chunk_id,
                service_id=item.service_id,
                service_code=item.service_code,
                service_name=item.service_name,
                section=item.section,
                content=item.text,
                text=item.text,
                relevance_score=score,
                score=score,
                source_id=item.source_id,
                source_url=item.source_url,
                source_title=item.source_title,
                source_confidence=item.source_confidence,
                retrieval_method=method,
            )
            evidence_results.append(result)

            if item.source_id not in seen_source_ids:
                seen_source_ids.add(item.source_id)
                source_references.append(
                    SourceReference(
                        source_id=item.source_id,
                        title=item.source_title,
                        url=item.source_url,
                        excerpt=item.text[:200] + "..." if len(item.text) > 200 else item.text,
                    )
                )

        # ── Calculate Confidence ──────────────────────────────────────────────
        confidence = 0.0
        if evidence_results:
            top_res = attributed_candidates[0] if attributed_candidates else None
            top_score = evidence_results[0].score or evidence_results[0].relevance_score

            if retrieval_mode == "hybrid" and isinstance(top_res, HybridResult):
                bm25_s = top_res.bm25_score
                sem_s = top_res.semantic_score
                if sem_s < 0.15 or bm25_s < 1.5:
                    # Insufficient semantic agreement or lexical overlap -> Out-of-domain / irrelevant match
                    confidence = round(min(0.12, max(0.02, sem_s * 0.2)), 3)
                elif bm25_s >= 3.0 and sem_s >= 0.20:
                    # Strong multi-modal agreement
                    confidence = round(min(1.0, 0.6 + (top_score / 0.0328) * 0.38), 3)
                elif bm25_s >= 1.5 and sem_s >= 0.15:
                    # Moderate lexical and semantic match
                    confidence = round(min(0.85, 0.4 + (bm25_s / 10.0) * 0.4), 3)
                else:
                    confidence = round(min(0.14, max(0.05, sem_s * 0.1)), 3)
            elif retrieval_mode == "semantic":
                confidence = round(top_score if top_score >= 0.40 else top_score * 0.15, 3)
            else:
                confidence = round(min(1.0, top_score / 10.0) if top_score >= 2.0 else 0.05, 3)

        return EvidenceBundle(
            query=query,
            intent=intent,
            intents=intents_list,
            total_retrieved=len(evidence_results),
            confidence=confidence,
            retrieval_method=retrieval_mode,
            results=evidence_results,
            sources=source_references,
        )
