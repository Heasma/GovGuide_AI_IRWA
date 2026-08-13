"""
GovGuide AI — Advisory Agent
Generates a grounded response from evidence supplied by the Research Agent.

RESPONSIBLE AI PRINCIPLE:
The Advisory Agent ONLY generates text from retrieved evidence.
It NEVER fabricates government information.
If evidence is insufficient, it returns a "cannot confirm" response.

Phase 1: LLM interface is a stub. The agent returns a structured placeholder response.
"""

import structlog
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    AdvisoryResultPayload, ConfidenceLabel,
    EvidenceBundle, NLPAnalysis,
)
from app.agents.advisory_agent.prompt_builder import build_prompt
from app.agents.advisory_agent.response_validator import validate_response

logger = structlog.get_logger(__name__)

# Threshold below which the system admits insufficient evidence
CONFIDENCE_THRESHOLD = 0.5

# Standard "insufficient evidence" response (mandated by Responsible AI policy)
INSUFFICIENT_EVIDENCE_RESPONSE = (
    "I could not find sufficient official evidence to provide a reliable answer to your query. "
    "Please consult the relevant government authority or official portal directly."
)


class AdvisoryAgent:
    """
    Responsible for:
    1. Receiving the EvidenceBundle from the Research Agent
    2. Building a grounded prompt (evidence → LLM)
    3. Generating a response using the LLM
    4. Validating the response for hallucination indicators
    5. Returning a structured, source-attributed answer

    The agent NEVER accesses external sources directly.
    It only processes the evidence supplied by the Research Agent.
    """

    AGENT_ID = AgentId.ADVISORY_AGENT

    def __init__(self):
        from app.llm.llm_client import get_llm_client
        self._llm = get_llm_client()
        logger.info("advisory_agent_initialized", llm_type=type(self._llm).__name__)

    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Main entry point. Receives a task message from the orchestrator,
        returns a result message with the validated answer.
        """
        payload = message.payload
        query: str = payload.get("user_query", "")
        sufficient: bool = payload.get("sufficient_evidence", False)
        retrieval_confidence: float = payload.get("retrieval_confidence", 0.0)
        evidence_bundle_data: dict = payload.get("evidence_bundle", {})
        nlp_analysis_data: dict = payload.get("nlp_analysis", {})

        logger.info(
            "advisory_agent_processing",
            request_id=message.request_id,
            sufficient_evidence=sufficient,
            retrieval_confidence=retrieval_confidence,
        )

        # ── Responsible AI: Insufficient evidence check ───────────────────────
        if not sufficient or retrieval_confidence < CONFIDENCE_THRESHOLD:
            result = AdvisoryResultPayload(
                answer=INSUFFICIENT_EVIDENCE_RESPONSE,
                confidence_score=0.0,
                confidence_label=ConfidenceLabel.INSUFFICIENT,
                sources=[],
                caveats=[
                    "No sufficient official evidence was found for this query.",
                    "Please verify with the relevant government authority.",
                ],
                explanation="Retrieval confidence was below the minimum threshold.",
                response_validated=True,
                fabrication_detected=False,
            )
            return self._wrap_result(message, result)

        # ── Build grounded prompt ─────────────────────────────────────────────
        prompt = build_prompt(
            query=query,
            evidence_bundle=evidence_bundle_data,
            nlp_analysis=nlp_analysis_data,
        )

        # ── Call LLM ──────────────────────────────────────────────────────────
        raw_answer = await self._llm.generate(prompt)

        # ── Validate response ─────────────────────────────────────────────────
        validation = validate_response(
            answer=raw_answer,
            evidence_bundle=evidence_bundle_data,
        )

        # ── Compute confidence label ───────────────────────────────────────────
        label = self._confidence_label(retrieval_confidence, validation.passed)

        result = AdvisoryResultPayload(
            answer=raw_answer if validation.passed else INSUFFICIENT_EVIDENCE_RESPONSE,
            confidence_score=round(retrieval_confidence, 3),
            confidence_label=label,
            sources=validation.attributed_sources,
            caveats=validation.caveats,
            explanation=validation.explanation,
            response_validated=validation.passed,
            fabrication_detected=not validation.passed,
        )

        logger.info(
            "advisory_agent_complete",
            request_id=message.request_id,
            confidence_label=label,
            validated=validation.passed,
        )

        return self._wrap_result(message, result)

    def _wrap_result(self, original: AgentMessage, result: AdvisoryResultPayload) -> AgentMessage:
        return AgentMessage(
            request_id=original.request_id,
            correlation_id=original.correlation_id,
            sender=self.AGENT_ID,
            recipient=AgentId.ORCHESTRATOR,
            message_type=MessageType.RESULT,
            payload=result.model_dump(),
        )

    def _confidence_label(self, score: float, validated: bool) -> ConfidenceLabel:
        if not validated:
            return ConfidenceLabel.INSUFFICIENT
        if score >= 0.8:
            return ConfidenceLabel.HIGH
        if score >= 0.6:
            return ConfidenceLabel.MEDIUM
        if score >= 0.4:
            return ConfidenceLabel.LOW
        return ConfidenceLabel.INSUFFICIENT
