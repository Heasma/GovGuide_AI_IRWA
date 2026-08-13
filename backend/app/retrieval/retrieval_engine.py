"""
GovGuide AI — Retrieval Engine (Stub)
Unified interface for information retrieval.

Phase 1: Returns empty EvidenceBundle (no dataset, no index).
Phase 2: Connect real BM25 + vector + hybrid retrievers after dataset indexing.

The interface is deliberately stable so Phase 2 is a drop-in replacement.
"""

from app.orchestrator.message_schema import EvidenceBundle
import structlog

logger = structlog.get_logger(__name__)


class RetrievalEngine:
    """
    Unified retrieval interface.
    Supports: bm25 | vector | hybrid (configurable).

    Phase 1: Stub — always returns empty bundle.
    Phase 2: Route to real retrievers based on RETRIEVAL_MODE config.
    """

    def __init__(self, mode: str = "hybrid"):
        self.mode = mode
        logger.info(
            "retrieval_engine_initialized",
            mode=mode,
            status="stub — dataset integration pending",
        )

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict = None,
    ) -> EvidenceBundle:
        """
        Execute a retrieval query.

        Phase 1: Returns empty bundle.
        Phase 2: Routes to BM25Retriever, VectorRetriever, or HybridRetriever.
        """
        logger.debug(
            "retrieval_search_called",
            query_length=len(query),
            top_k=top_k,
            mode=self.mode,
            status="stub",
        )
        # Phase 2: implement real retrieval here
        return EvidenceBundle(total_retrieved=0, results=[])
