"""
GovGuide AI — Research Agent

Processes user queries through the NLP pipeline and IR layer,
returning a structured EvidenceBundle.

Responsibilities:
1. Receiving a sanitized user query
2. Running it through the NLP pipeline (intent classification & normalization)
3. Calling the information retrieval layer (BM25 + Semantic Hybrid RRF)
4. Returning a structured EvidenceBundle with verified source metadata
5. Deciding sufficient_evidence based on RETRIEVAL_CONFIDENCE_THRESHOLD

The agent NEVER generates final answers — it only retrieves and validates evidence.
"""

import structlog
from app.config import get_settings
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    ResearchResultPayload, NLPAnalysis, EvidenceBundle,
    Intent,
)

logger = structlog.get_logger(__name__)


class ResearchAgent:
    """
    Research agent coordinating NLP query understanding and hybrid retrieval.
    """

    AGENT_ID = AgentId.RESEARCH_AGENT

    def __init__(self, retrieval_engine=None):
        from app.nlp.preprocessor import preprocess
        from app.nlp.intent_classifier import classify_intent
        from app.retrieval.retrieval_engine import RetrievalEngine

        settings = get_settings()
        self._preprocess = preprocess
        self._classify_intent = classify_intent
        self._retrieval_engine = retrieval_engine or RetrievalEngine()
        self._confidence_threshold = settings.RETRIEVAL_CONFIDENCE_THRESHOLD

        logger.info(
            "research_agent_initialized",
            confidence_threshold=self._confidence_threshold,
        )

    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Main entry point. Receives an orchestrator task message,
        returns a result message with the EvidenceBundle.
        """
        payload = message.payload if isinstance(message.payload, dict) else message.payload.model_dump()
        query: str = payload.get("user_query", "")
        retrieval_config: dict = payload.get("retrieval_config", {})

        logger.info(
            "research_agent_processing",
            request_id=message.request_id,
            query_length=len(query),
        )

        # ── NLP Pipeline ──────────────────────────────────────────────────────
        clean_query = self._preprocess(query)
        from app.nlp.intent_classifier import classify_intents
        classified_intents = classify_intents(clean_query)
        intent = classified_intents[0]
        from app.nlp.domain_detector import classify_domain, is_domain_supported, UNSUPPORTED_DOMAINS
        domain = classify_domain(clean_query)
        is_supported = is_domain_supported(domain)

        nlp_analysis = NLPAnalysis(
            intent=intent,
            intents=classified_intents,
            domain=domain,
            is_domain_supported=is_supported,
            entities=[],       # Entity extraction
            expanded_query=clean_query,
            keywords=[],
        )

        # ── Domain Gating ─────────────────────────────────────────────────────
        if domain in UNSUPPORTED_DOMAINS:
            evidence_bundle = EvidenceBundle(
                query=clean_query,
                intent=intent.value if hasattr(intent, "value") else str(intent),
                domain=domain.value if hasattr(domain, "value") else str(domain),
                domain_supported=False,
                total_retrieved=0,
                confidence=0.0,
                results=[],
                sources=[],
            )
            result_payload = ResearchResultPayload(
                nlp_analysis=nlp_analysis,
                evidence_bundle=evidence_bundle,
                retrieval_confidence=0.0,
                sufficient_evidence=False,
            )
            return AgentMessage(
                request_id=message.request_id,
                correlation_id=message.correlation_id,
                sender=self.AGENT_ID,
                recipient=AgentId.ORCHESTRATOR,
                message_type=MessageType.RESULT,
                payload=result_payload.model_dump(),
            )

        # ── Information Retrieval ─────────────────────────────────────────────
        top_k = retrieval_config.get("top_k", 10)
        evidence_bundle = await self._retrieval_engine.search(
            query=clean_query,
            top_k=top_k,
        )
        evidence_bundle.domain = domain.value if hasattr(domain, "value") else str(domain)
        evidence_bundle.domain_supported = True

        # ── Confidence Assessment ─────────────────────────────────────────────
        retrieval_confidence = self._compute_confidence(evidence_bundle)
        sufficient = (
            evidence_bundle.total_retrieved > 0
            and retrieval_confidence >= self._confidence_threshold
        )

        result_payload = ResearchResultPayload(
            nlp_analysis=nlp_analysis,
            evidence_bundle=evidence_bundle,
            retrieval_confidence=retrieval_confidence,
            sufficient_evidence=sufficient,
        )

        top_service_name = "None"
        if evidence_bundle.results:
            top_service_name = evidence_bundle.results[0].service_name or evidence_bundle.results[0].source_title or "Government Service"

        logger.info(
            "research_agent_complete",
            request_id=message.request_id,
            question_received=query,
            relevant_records_found=evidence_bundle.total_retrieved,
            selected_service=top_service_name,
            confidence=retrieval_confidence,
            sufficient=sufficient,
        )

        return AgentMessage(
            request_id=message.request_id,
            correlation_id=message.correlation_id,
            sender=self.AGENT_ID,
            recipient=AgentId.ORCHESTRATOR,
            message_type=MessageType.RESULT,
            payload=result_payload.model_dump(),
        )

    def _compute_confidence(self, evidence_bundle: EvidenceBundle) -> float:
        """
        Computes retrieval confidence score from the retrieved EvidenceBundle.
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
