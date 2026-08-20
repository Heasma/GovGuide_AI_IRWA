"""
GovGuide AI — Advisory Agent

Generates grounded responses from evidence supplied by the Research Agent.

RESPONSIBLE AI PRINCIPLES:
1. The Advisory Agent ONLY generates answers grounded in retrieved evidence.
2. It NEVER fabricates government facts, fees, procedures, or deadlines.
3. If evidence is insufficient, it returns a safe, explanatory advisory with official office referrals.
4. It treats all retrieved evidence strictly as passive DATA, ignoring any instructions embedded within.
"""

import structlog
from typing import Optional

from app.config import get_settings
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    AdvisoryResultPayload, ConfidenceLabel,
    EvidenceBundle, NLPAnalysis,
)
from app.agents.advisory_agent.prompt_builder import build_prompt
from app.agents.advisory_agent.response_validator import validate_response
from app.llm.llm_client import BaseLLMClient, get_llm_client

logger = structlog.get_logger(__name__)

INSUFFICIENT_EVIDENCE_RESPONSE = (
    "I couldn't find a matching government service with sufficient official evidence in the available GovGuide dataset. "
    "Please try using the service name, department, or a more specific question."
)


class AdvisoryAgent:
    """
    Advisory Agent coordinating prompt generation, LLM inference, and Responsible AI response validation.
    """

    AGENT_ID = AgentId.ADVISORY_AGENT

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        settings = get_settings()
        self._llm = llm_client or get_llm_client()
        self._confidence_threshold = settings.RETRIEVAL_CONFIDENCE_THRESHOLD
        logger.info(
            "advisory_agent_initialized",
            llm_type=type(self._llm).__name__,
            confidence_threshold=self._confidence_threshold,
        )

    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Main entry point. Receives an AdvisoryTask message from the orchestrator,
        executes grounded generation, validates the result, and returns an AdvisoryResult message.
        """
        payload = message.payload if isinstance(message.payload, dict) else message.payload.model_dump()
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
        if not sufficient or retrieval_confidence < self._confidence_threshold:
            result = AdvisoryResultPayload(
                answer=INSUFFICIENT_EVIDENCE_RESPONSE,
                confidence_score=0.0,
                confidence_label=ConfidenceLabel.INSUFFICIENT,
                sources=[],
                caveats=[
                    "The available government dataset did not contain a sufficiently relevant service record."
                ],
                explanation="No sufficiently relevant service records were found in the database.",
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

        # ── Handle LLM provider errors with grounded evidence synthesis ──────
        if self._is_error_output(raw_answer):
            logger.warning("llm_call_fallback_to_evidence_synthesis", raw_output=raw_answer)
            raw_answer = self._synthesize_from_evidence(query, evidence_bundle_data)

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
        if score >= 0.75:
            return ConfidenceLabel.HIGH
        if score >= 0.45:
            return ConfidenceLabel.MEDIUM
        if score >= self._confidence_threshold:
            return ConfidenceLabel.LOW
        return ConfidenceLabel.INSUFFICIENT

    def _is_error_output(self, answer: str) -> bool:
        """Check whether the LLM output is an error or unconfigured marker."""
        if not answer or not answer.strip():
            return True
        error_prefixes = [
            "[LLM_PROVIDER_ERROR]",
            "[LLM_NOT_CONFIGURED]",
            "[LLM_TIMEOUT]",
            "[LLM_INVALID_RESPONSE]",
            "[ERROR]",
        ]
        return any(answer.strip().startswith(prefix) for prefix in error_prefixes)

    def _synthesize_from_evidence(self, query: str, evidence_bundle: dict) -> str:
        """
        Synthesizes a structured, grounded answer directly from retrieved Chicago database evidence
        when the external LLM provider is unavailable, rate-limited, or unconfigured.
        """
        results = evidence_bundle.get("results", [])
        if not results:
            return INSUFFICIENT_EVIDENCE_RESPONSE

        lines = [
            "Based on official City of Chicago business licensing records, here is the guidance for your inquiry:\n"
        ]

        top_results = results[:3]
        for i, item in enumerate(top_results, start=1):
            title = item.get("source_title") or f"Service {item.get('service_code', '')}"
            code = item.get("service_code")
            content = item.get("text") or item.get("content", "")
            url = item.get("source_url") or "https://www.chicago.gov/BusinessDirect"

            code_badge = f" (License Code: {code})" if code and code != "N/A" else ""
            lines.append(f"### {i}. {title}{code_badge}")

            if content:
                clean_content = content.strip()
                if len(clean_content) > 350:
                    clean_content = clean_content[:350].rsplit(".", 1)[0] + "."
                lines.append(clean_content)

            lines.append(f"Official Portal: {url} [Source {i}]\n")

        lines.append(
            "**Key Application Steps:**\n"
            "1. Determine your specific business activity and required municipal license category.\n"
            "2. Complete zoning review and resolve any outstanding City of Chicago debt.\n"
            "3. Submit your application online via Chicago Business Direct or at City Hall (Small Business Center, 121 N. LaSalle St., Room 800).\n"
            "4. Complete required inspections (Health, Fire, Buildings) and pay applicable licensing fees."
        )

        return "\n\n".join(lines)

