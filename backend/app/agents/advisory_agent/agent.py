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
from typing import Optional, Dict, Any, List

from app.config import get_settings
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    AdvisoryResultPayload, ConfidenceLabel,
    EvidenceBundle, NLPAnalysis, Domain,
)
from app.agents.advisory_agent.prompt_builder import build_prompt
from app.agents.advisory_agent.response_validator import validate_response
from app.nlp.domain_detector import SUPPORTED_DOMAINS, UNSUPPORTED_DOMAINS
from app.llm.llm_client import BaseLLMClient, get_llm_client

logger = structlog.get_logger(__name__)

INSUFFICIENT_EVIDENCE_RESPONSE = (
    "I couldn't find a matching government service with sufficient official evidence in the available GovGuide dataset. "
    "Please try using the service name, department, or a more specific question."
)

DRIVER_LICENSE_RESPONSE = (
    "I couldn't find relevant information about driver's licences in the current GovGuide AI knowledge base.\n\n"
    "The available knowledge base currently focuses on City of Chicago government business licensing information.\n\n"
    "Please check the relevant official driver's licensing authority (such as the Illinois Secretary of State / DMV at https://www.ilsos.gov) for current licence class requirements and driving regulations."
)

AVIATION_LICENSE_RESPONSE = (
    "I couldn't find relevant information about aviation licensing in the current GovGuide AI knowledge base.\n\n"
    "The available knowledge base currently focuses on City of Chicago government business licensing information.\n\n"
    "Please consult the Federal Aviation Administration (FAA at https://www.faa.gov) for official pilot and aircraft licensing requirements."
)


def get_unsupported_domain_response(domain: Optional[str]) -> str:
    domain_str = (domain or "").lower()
    if domain_str in ("driver_license", "driver license", "driver's license", "driving license"):
        return DRIVER_LICENSE_RESPONSE
    if domain_str in ("aviation", "aviation_license", "helicopter", "pilot"):
        return AVIATION_LICENSE_RESPONSE
    domain_label = domain_str.replace("_", " ") if domain_str else "this service domain"
    return (
        f"I couldn't find relevant information about {domain_label} in the current GovGuide AI knowledge base.\n\n"
        "The available knowledge base currently focuses on City of Chicago government business licensing information.\n\n"
        "Please consult the relevant official government authority directly for service and licensing requirements."
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

        # ── Domain Check ──────────────────────────────────────────────────────
        domain_val = payload.get("domain")
        if not domain_val and isinstance(nlp_analysis_data, dict):
            domain_val = nlp_analysis_data.get("domain")
        if not domain_val and isinstance(evidence_bundle_data, dict):
            domain_val = evidence_bundle_data.get("domain")

        is_domain_supported = payload.get("is_domain_supported", True)
        if isinstance(nlp_analysis_data, dict) and "is_domain_supported" in nlp_analysis_data:
            is_domain_supported = nlp_analysis_data.get("is_domain_supported", True)
        if isinstance(evidence_bundle_data, dict) and "domain_supported" in evidence_bundle_data:
            is_domain_supported = evidence_bundle_data.get("domain_supported", True)

        domain_str = domain_val.value if hasattr(domain_val, "value") else str(domain_val) if domain_val else ""

        is_explicit_unsupported = (
            (domain_str and domain_str in [d.value for d in UNSUPPORTED_DOMAINS])
            or (not is_domain_supported and domain_str not in ("", "unknown", "business_license", "government_service"))
        )

        if is_explicit_unsupported:
            logger.info(
                "advisory_agent_unsupported_domain",
                request_id=message.request_id,
                domain=domain_str,
            )
            safe_msg = get_unsupported_domain_response(domain_str)
            domain_enum = Domain(domain_str) if domain_str in Domain._value2member_map_ else Domain.UNKNOWN
            result = AdvisoryResultPayload(
                answer=safe_msg,
                confidence_score=0.0,
                confidence_label=ConfidenceLabel.INSUFFICIENT,
                domain=domain_enum,
                is_domain_supported=False,
                sources=[],
                caveats=[
                    "The requested domain is not supported by the current City of Chicago business licensing dataset."
                ],
                explanation=f"Query belongs to unsupported domain '{domain_str}'. Cross-domain retrieval was prevented.",
                response_validated=True,
                fabrication_detected=False,
            )
            return self._wrap_result(message, result)

        logger.info(
            "advisory_agent_processing",
            request_id=message.request_id,
            sufficient_evidence=sufficient,
            retrieval_confidence=retrieval_confidence,
            domain=domain_str,
        )

        # ── Language Detection ────────────────────────────────────────────────
        lang = "en"
        if isinstance(nlp_analysis_data, dict):
            lang = nlp_analysis_data.get("language") or "en"
        if not lang or lang == "en":
            from app.nlp.language_detector import resolve_query_language
            lang = resolve_query_language(query)

        # ── Responsible AI: Insufficient evidence check ───────────────────────
        if not sufficient or retrieval_confidence < self._confidence_threshold:
            domain_enum = Domain(domain_str) if domain_str in Domain._value2member_map_ else Domain.BUSINESS_LICENSE
            from app.agents.advisory_agent.intent_formatter import get_insufficient_evidence_response
            insufficient_ans = get_insufficient_evidence_response(lang)
            result = AdvisoryResultPayload(
                answer=insufficient_ans,
                confidence_score=0.0,
                confidence_label=ConfidenceLabel.INSUFFICIENT,
                domain=domain_enum,
                is_domain_supported=True,
                sources=[],
                caveats=[
                    "The available government dataset did not contain a sufficiently relevant service record."
                ],
                explanation="No sufficiently relevant service records were found in the database.",
                response_validated=True,
                fabrication_detected=False,
            )
            return self._wrap_result(message, result)

        # ── Extract Intent ────────────────────────────────────────────────────
        from app.orchestrator.message_schema import Intent
        intent_obj = Intent.GENERAL
        intents_list = []
        if isinstance(nlp_analysis_data, dict):
            raw_intent = nlp_analysis_data.get("intent")
            intents_list = nlp_analysis_data.get("intents", [])
            if isinstance(raw_intent, Intent):
                intent_obj = raw_intent
            elif isinstance(raw_intent, str):
                try:
                    intent_obj = Intent(raw_intent)
                except ValueError:
                    intent_obj = Intent.GENERAL
        else:
            from app.nlp.intent_classifier import classify_intent, classify_intents
            intent_obj = classify_intent(query)
            intents_list = classify_intents(query)

        # ── Build grounded prompt ─────────────────────────────────────────────
        prompt = build_prompt(
            query=query,
            evidence_bundle=evidence_bundle_data,
            nlp_analysis=nlp_analysis_data,
        )

        # ── Call LLM with seamless fallback ──────────────────────────────────
        from app.agents.advisory_agent.intent_formatter import (
            format_intent_response,
            calibrate_confidence_for_intent,
            get_insufficient_evidence_response,
        )

        try:
            raw_answer = await self._llm.generate(prompt)
        except Exception as exc:
            logger.warning("llm_call_exception_fallback", error=str(exc))
            raw_answer = f"[LLM_PROVIDER_ERROR] {str(exc)}"

        is_target_available = True
        synth_explanation = "Response verified and grounded against official evidence."

        # ── Handle LLM provider errors with grounded evidence synthesis ──────
        if self._is_error_output(raw_answer):
            logger.warning("llm_call_fallback_to_evidence_synthesis", raw_output=raw_answer)
            raw_answer, is_target_available, synth_explanation = format_intent_response(
                query, intent_obj, evidence_bundle_data, intents=intents_list, language=lang
            )
        else:
            if "not currently provide a verified fee" in raw_answer.lower() or "cannot provide a fee" in raw_answer.lower():
                is_target_available = False


        # ── Validate response ─────────────────────────────────────────────────
        validation = validate_response(
            answer=raw_answer,
            evidence_bundle=evidence_bundle_data,
        )

        # ── Compute intent-calibrated confidence label ────────────────────────
        final_score, label = calibrate_confidence_for_intent(
            intent=intent_obj,
            retrieval_confidence=retrieval_confidence,
            is_target_available=is_target_available,
            is_validated=validation.passed,
        )
        domain_enum = Domain(domain_str) if domain_str in Domain._value2member_map_ else Domain.BUSINESS_LICENSE

        fallback_ans = get_insufficient_evidence_response(lang)
        result = AdvisoryResultPayload(
            answer=raw_answer if validation.passed else fallback_ans,
            confidence_score=final_score,
            confidence_label=label,
            domain=domain_enum,
            is_domain_supported=True,
            sources=validation.attributed_sources if validation.passed else [],
            caveats=validation.caveats,
            explanation=synth_explanation if is_target_available else "Requested target information was not verified in official records.",
            response_validated=validation.passed,
            fabrication_detected=not validation.passed,
        )

        logger.info(
            "advisory_agent_complete",
            request_id=message.request_id,
            intent=intent_obj.value if hasattr(intent_obj, "value") else str(intent_obj),
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
            "error code: 429",
            "credit_balance_exhausted",
            "insufficient_quota",
        ]
        lower = answer.lower()
        return any(prefix.lower() in lower for prefix in error_prefixes)


    def _synthesize_from_evidence(self, query: str, evidence_bundle: dict, intent: Optional[Any] = None) -> str:
        """
        Synthesizes an intent-driven structured answer directly from retrieved Chicago database evidence
        when the external LLM provider is unavailable, rate-limited, or unconfigured.
        """
        from app.agents.advisory_agent.intent_formatter import format_intent_response
        intent_obj = intent or Intent.GENERAL
        if isinstance(intent_obj, str):
            try:
                intent_obj = Intent(intent_obj)
            except ValueError:
                intent_obj = Intent.GENERAL
        answer, _, _ = format_intent_response(query, intent_obj, evidence_bundle)
        return answer

