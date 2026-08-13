"""
GovGuide AI — Research Agent
Processes user queries through the NLP pipeline and IR layer,
returning a structured EvidenceBundle.

Phase 1: NLP and IR are stub interfaces. The agent returns an empty
EvidenceBundle with sufficient_evidence=False until the real dataset
is integrated and indexed.
"""

import structlog
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    ResearchResultPayload, NLPAnalysis, EvidenceBundle,
    Intent,
)

logger = structlog.get_logger(__name__)


class ResearchAgent:
    """
    Responsible for:
    1. Receiving a sanitized user query
    2. Running it through the NLP pipeline (intent, NER, query expansion)
    3. Calling the information retrieval layer
    4. Returning a structured EvidenceBundle with source metadata

    The agent NEVER generates answers — it only retrieves evidence.
    """

    AGENT_ID = AgentId.RESEARCH_AGENT

    def __init__(self):
        # NLP and IR components are imported lazily to allow stub replacement
        from app.nlp.preprocessor import preprocess
        from app.nlp.intent_classifier import classify_intent
        from app.retrieval.retrieval_engine import RetrievalEngine

        self._preprocess = preprocess
        self._classify_intent = classify_intent
        self._retrieval_engine = RetrievalEngine()

        logger.info("research_agent_initialized")

    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Main entry point. Receives an orchestrator task message,
        returns a result message with the EvidenceBundle.
        """
        payload = message.payload
        query: str = payload.get("user_query", "")
        retrieval_config: dict = payload.get("retrieval_config", {})

        logger.info(
            "research_agent_processing",
            request_id=message.request_id,
            query_length=len(query),
        )

        # ── NLP Pipeline ──────────────────────────────────────────────────────
        clean_query = self._preprocess(query)
        intent = self._classify_intent(clean_query)

        nlp_analysis = NLPAnalysis(
            intent=intent,
            entities=[],       # NER stub — populated when spaCy model is configured
            expanded_query=clean_query,
            keywords=[],       # Keyword extraction stub
        )

        # ── Information Retrieval ─────────────────────────────────────────────
        top_k = retrieval_config.get("top_k", 10)
        evidence_bundle = await self._retrieval_engine.search(
            query=clean_query,
            top_k=top_k,
        )

        # ── Confidence Assessment ─────────────────────────────────────────────
        retrieval_confidence = self._compute_confidence(evidence_bundle)
        sufficient = evidence_bundle.total_retrieved > 0 and retrieval_confidence >= 0.5

        result_payload = ResearchResultPayload(
            nlp_analysis=nlp_analysis,
            evidence_bundle=evidence_bundle,
            retrieval_confidence=retrieval_confidence,
            sufficient_evidence=sufficient,
        )

        logger.info(
            "research_agent_complete",
            request_id=message.request_id,
            retrieved=evidence_bundle.total_retrieved,
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
        Computes a retrieval confidence score.
        Phase 1: Simple heuristic based on number of results.
        Phase 2: Use top-K relevance scores + diversity metrics.
        """
        if evidence_bundle.total_retrieved == 0:
            return 0.0
        top_score = max(
            (r.relevance_score for r in evidence_bundle.results),
            default=0.0,
        )
        return round(top_score, 3)
