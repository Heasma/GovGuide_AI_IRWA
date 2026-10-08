"""
GovGuide AI — Retrieval Engine

Unified interface for information retrieval delegating to RetrievalService.
Maintains backward compatibility with Phase 1/2 callers.
"""

from typing import Optional
from app.orchestrator.message_schema import EvidenceBundle
from app.retrieval.retrieval_service import RetrievalService
import structlog

logger = structlog.get_logger(__name__)


class RetrievalEngine:
    """
    Unified retrieval interface.
    Routes queries through the RetrievalService (BM25, Semantic, or Hybrid).
    """

    def __init__(self, mode: str = "hybrid", service: Optional[RetrievalService] = None):
        self.mode = mode
        self._service = service or RetrievalService()
        logger.info(
            "retrieval_engine_initialized",
            mode=mode,
            status="active",
        )

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict = None,
        intent: Optional[str] = None,
        target_service: Optional[str] = None,
    ) -> EvidenceBundle:
        """
        Execute a retrieval query via RetrievalService.
        """
        logger.debug(
            "retrieval_search_called",
            query_length=len(query),
            top_k=top_k,
            mode=self.mode,
            intent=intent,
            target_service=target_service,
        )
        return self._service.search(
            query=query,
            top_k=top_k,
            mode=self.mode,
            intent=intent,
            target_service=target_service,
        )
