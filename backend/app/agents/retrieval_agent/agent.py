"""
GovGuide AI — Retrieval Agent (Agent 2)

Responsibilities:
1. Receives structured query payload from Query Understanding Agent.
2. Coordinates information retrieval through the hybrid search engine (BM25 + Semantic + RRF).
3. Ranks and compiles retrieved chunks into a structured EvidenceBundle.
4. Attaches verified source metadata and license identifiers.
5. Computes retrieval confidence score and decides evidence sufficiency.
6. Returns RetrievalResultPayload to downstream agents / orchestrator.

The Retrieval Agent NEVER generates natural-language final answers — it solely provides verified evidence.
"""

import structlog
from typing import Optional, Dict, Any

from app.config import get_settings
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType, TaskType,
    RetrievalTaskPayload, RetrievalResultPayload,
    EvidenceBundle, Domain, ErrorCode, ErrorPayload,
)
from app.nlp.domain_detector import SUPPORTED_DOMAINS, UNSUPPORTED_DOMAINS, classify_domain, is_domain_supported
from app.retrieval.retrieval_engine import RetrievalEngine

logger = structlog.get_logger(__name__)


class RetrievalAgent:
    """
    Intelligent Agent specialized in Information Retrieval, multi-mode search,
    hybrid fusion, domain-aware retrieval gating, and evidence compilation.
    """

    AGENT_ID = AgentId.RETRIEVAL_AGENT

    def __init__(self, retrieval_engine: Optional[RetrievalEngine] = None):
        settings = get_settings()
        self._retrieval_engine = retrieval_engine or RetrievalEngine()
        self._confidence_threshold = settings.RETRIEVAL_CONFIDENCE_THRESHOLD
        logger.info(
            "retrieval_agent_initialized",
            confidence_threshold=self._confidence_threshold,
        )

    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Processes a retrieval task message and returns an evidence bundle.
        """
        payload = message.payload if isinstance(message.payload, dict) else message.payload.model_dump()

        # Extract query text and domain metadata from structured_query payload or direct fields
        structured_query = payload.get("structured_query")
        if structured_query and isinstance(structured_query, dict):
            search_query = (
                structured_query.get("expanded_query")
                or structured_query.get("cleaned_query")
                or structured_query.get("original_query")
                or ""
            )
            intent = structured_query.get("intent")
            domain_val = structured_query.get("domain")
            is_domain_supported = structured_query.get("is_domain_supported", True)
        else:
            search_query = payload.get("user_query") or payload.get("query") or ""
            intent = payload.get("intent")
            domain_val = payload.get("domain")
            is_domain_supported = payload.get("is_domain_supported", True)

        # Parse Domain enum if provided as string
        detected_domain = Domain.UNKNOWN
        if isinstance(domain_val, Domain):
            detected_domain = domain_val
        elif isinstance(domain_val, str):
            try:
                detected_domain = Domain(domain_val)
            except ValueError:
                detected_domain = Domain.UNKNOWN

        # If domain was not classified upstream, perform inline classification
        if detected_domain in (Domain.UNKNOWN, None) and search_query:
            detected_domain = classify_domain(search_query)
            is_domain_supported = detected_domain in SUPPORTED_DOMAINS

        retrieval_config = payload.get("retrieval_config", {})
        top_k = retrieval_config.get("top_k", 10)

        logger.info(
            "retrieval_agent_processing",
            request_id=message.request_id,
            query_length=len(search_query),
            detected_domain=detected_domain.value if hasattr(detected_domain, "value") else str(detected_domain),
            is_domain_supported=is_domain_supported,
            top_k=top_k,
        )

        # ── Domain Gating: Prevent Cross-Domain Retrieval ────────────────────
        is_unsupported = (
            detected_domain in UNSUPPORTED_DOMAINS
            or (not is_domain_supported and detected_domain not in (Domain.UNKNOWN, Domain.BUSINESS_LICENSE, Domain.GOVERNMENT_SERVICE))
        )

        if is_unsupported:
            logger.info(
                "retrieval_agent_cross_domain_gated",
                request_id=message.request_id,
                query=search_query,
                detected_domain=detected_domain.value if hasattr(detected_domain, "value") else str(detected_domain),
                knowledge_base_domain_supported=False,
                retrieval_executed=False,
                evidence_sufficient=False,
            )

            empty_bundle = EvidenceBundle(
                query=search_query,
                intent=intent.value if hasattr(intent, "value") else str(intent) if intent else None,
                domain=detected_domain.value if hasattr(detected_domain, "value") else str(detected_domain),
                domain_supported=False,
                total_retrieved=0,
                confidence=0.0,
                retrieval_method="none",
                results=[],
                sources=[],
            )

            result_payload = RetrievalResultPayload(
                evidence_bundle=empty_bundle,
                retrieval_confidence=0.0,
                sufficient_evidence=False,
                domain=detected_domain,
                is_domain_supported=False,
            )

            return AgentMessage(
                request_id=message.request_id,
                correlation_id=message.correlation_id,
                sender=self.AGENT_ID,
                recipient=message.sender,
                message_type=MessageType.RESULT,
                payload=result_payload.model_dump(),
            )

        try:
            # ── Execute Hybrid Information Retrieval ──────────────────────────
            evidence_bundle: EvidenceBundle = await self._retrieval_engine.search(
                query=search_query,
                top_k=top_k,
            )
            evidence_bundle.domain = detected_domain.value if hasattr(detected_domain, "value") else str(detected_domain)
            evidence_bundle.domain_supported = True

            # ── Confidence Assessment & Domain Compatibility ──────────────────
            confidence = self._compute_confidence(evidence_bundle)
            sufficient = (
                evidence_bundle.total_retrieved > 0
                and confidence >= self._confidence_threshold
            )

            result_payload = RetrievalResultPayload(
                evidence_bundle=evidence_bundle,
                retrieval_confidence=confidence,
                sufficient_evidence=sufficient,
                domain=detected_domain,
                is_domain_supported=True,
            )

            top_title = "None"
            if evidence_bundle.results:
                top_title = (
                    evidence_bundle.results[0].service_name
                    or evidence_bundle.results[0].source_title
                    or "Government Record"
                )

            logger.info(
                "retrieval_agent_complete",
                request_id=message.request_id,
                detected_domain=detected_domain.value if hasattr(detected_domain, "value") else str(detected_domain),
                knowledge_base_domain_supported=True,
                retrieval_executed=True,
                total_retrieved=evidence_bundle.total_retrieved,
                top_service=top_title,
                confidence=confidence,
                evidence_sufficient=sufficient,
            )

            return AgentMessage(
                request_id=message.request_id,
                correlation_id=message.correlation_id,
                sender=self.AGENT_ID,
                recipient=message.sender,
                message_type=MessageType.RESULT,
                payload=result_payload.model_dump(),
            )

        except Exception as exc:
            logger.error("retrieval_agent_failed", error=str(exc))
            return AgentMessage(
                request_id=message.request_id,
                correlation_id=message.correlation_id,
                sender=self.AGENT_ID,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                payload=ErrorPayload(
                    error_code=ErrorCode.RETRIEVAL_FAILED,
                    error_message=f"Retrieval error: {str(exc)}",
                    fallback_response="I could not retrieve official evidence from the knowledge base.",
                ).model_dump(),
            )

    def _compute_confidence(self, evidence_bundle: EvidenceBundle) -> float:
        """
        Calculates normalized confidence score from the retrieved EvidenceBundle.
        """
        if not evidence_bundle or evidence_bundle.total_retrieved == 0:
            return 0.0
        if evidence_bundle.confidence > 0.0:
            return round(evidence_bundle.confidence, 3)
        top_score = max(
            (r.relevance_score for r in evidence_bundle.results),
            default=0.0,
        )
        return round(top_score, 3)
