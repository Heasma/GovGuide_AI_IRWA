"""
GovGuide AI — Multi-Agent Orchestrator

Coordinates the full 3-agent query workflow:
  User Query
      │
      ▼
  [ Agent 1: Query Understanding Agent ] (NLP, NER, Intent, Safety)
      │  (AgentMessage: StructuredQueryPayload)
      ▼
  [ Agent 2: Retrieval Agent ] (Hybrid BM25 + Semantic + RRF)
      │  (AgentMessage: EvidenceBundle)
      ▼
  [ Agent 3: Response / Verification Agent ] (Grounded Generation, Verification, Citations)
      │
      ▼
  Validated QueryResponse
"""

import uuid
import time
import re
import structlog
from typing import Optional, Dict, Any, List

from app.orchestrator.message_schema import (
    AgentId, MessageType, TaskType, AgentMessage,
    QueryUnderstandingTaskPayload, StructuredQueryPayload,
    RetrievalTaskPayload, RetrievalResultPayload,
    ResponseTaskPayload, ResponseResultPayload,
    ResearchTaskPayload, ResearchResultPayload,
    AdvisoryTaskPayload, AdvisoryResultPayload,
    ErrorCode, ErrorPayload,
    ConfidenceLabel, NLPAnalysis, Intent,
)
from app.orchestrator.agent_registry import AgentRegistry
from app.orchestrator.failure_handler import FailureHandler
from app.orchestrator.interaction_logger import InteractionLogger
from app.security.prompt_injection_guard import assert_safe
from app.schemas import QueryResponse, SourceReference
from app.config import get_settings
from app.agents.advisory_agent.intent_formatter import get_conversational_response, get_clarification_response

logger = structlog.get_logger(__name__)


class Orchestrator:
    """
    Central orchestrator coordinating message exchanges between the 3 interacting intelligent agents:
    - Agent 1: QueryUnderstandingAgent
    - Agent 2: RetrievalAgent
    - Agent 3: ResponseVerificationAgent
    """

    def __init__(self):
        self.registry = AgentRegistry()
        self.failure_handler = FailureHandler()
        self.interaction_logger = InteractionLogger()

    async def process_query(
        self,
        query: str,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context_entity: Optional[str] = None,
    ) -> QueryResponse:
        """
        Executes the full 3-agent pipeline and returns a QueryResponse for the API / UI layer.
        """
        request_id = request_id or str(uuid.uuid4())
        log = logger.bind(request_id=request_id, user_id=user_id)
        correlation_id = str(uuid.uuid4())

        # ── Step 1: Prompt Injection Pre-check ───────────────────────────────
        try:
            assert_safe(query)
        except ValueError as e:
            log.warning("injection_detected_precheck", detail=str(e))
            return self._injection_blocked_response(request_id)

        # ── Step 2: Agent 1 — Query Understanding Agent ───────────────────────
        query_task = AgentMessage(
            request_id=request_id,
            correlation_id=correlation_id,
            sender=AgentId.ORCHESTRATOR,
            recipient=AgentId.QUERY_AGENT,
            message_type=MessageType.TASK,
            payload=QueryUnderstandingTaskPayload(
                raw_query=query,
                session_id=session_id,
                context_entity=context_entity,
            ).model_dump(),
        )


        log.info("dispatching_to_query_understanding_agent")
        q_start = time.monotonic()
        query_agent = self.registry.get_agent(AgentId.QUERY_AGENT)
        query_result_msg = await self.failure_handler.call_with_fallback(
            agent_fn=query_agent.process,
            message=query_task,
            agent_id=AgentId.QUERY_AGENT,
        )
        q_dur = int((time.monotonic() - q_start) * 1000)
        self.interaction_logger.log(query_task, query_result_msg, q_dur)

        if query_result_msg.message_type == MessageType.ERROR:
            return self._error_response(request_id, query_result_msg)

        structured_query_dict = query_result_msg.payload
        structured_query = StructuredQueryPayload(**structured_query_dict)

        log.info(
            "query_understanding_stage_done",
            detected_domain=structured_query.domain.value if hasattr(structured_query.domain, "value") else str(structured_query.domain),
            detected_intent=structured_query.intent.value if hasattr(structured_query.intent, "value") else str(structured_query.intent),
            knowledge_base_domain_supported=structured_query.is_domain_supported,
        )

        # ── Step 2a: Conversational / Non-informational Fast-path ─────────────
        is_conversational_intent = (
            structured_query.intent in (
                Intent.CONVERSATIONAL, Intent.THANKS, Intent.ACKNOWLEDGEMENT,
                Intent.GOODBYE, Intent.GREETING,
            )
            or structured_query.search_parameters.get("conversation_type") is not None
        )

        if is_conversational_intent:
            conv_type = structured_query.search_parameters.get("conversation_type")
            conv_answer = get_conversational_response(query, conv_type)
            log.info(
                "conversational_response_dispatched",
                conversation_type=conv_type,
                active_entity_preserved=structured_query.search_parameters.get("active_entity_preserved", False),
                retrieval_bypassed=True,
            )
            return QueryResponse(
                request_id=request_id,
                answer=conv_answer,
                confidence_score=0.0,
                confidence_label=None,
                sources=[],
                caveats=[],
                explanation=None,
                is_demo=False,
                is_conversational=True,
            )

        # ── Step 2b: Strict Out-of-Domain Refusal Fast-path ───────────────────
        if not structured_query.is_domain_supported:
            from app.nlp.language_detector import resolve_query_language
            from app.agents.advisory_agent.intent_formatter import get_unsupported_domain_response
            resolved_lang = resolve_query_language(query)
            domain_val_str = structured_query.domain.value if hasattr(structured_query.domain, "value") else str(structured_query.domain)
            out_of_domain_answer = get_unsupported_domain_response(domain_val_str, resolved_lang)
            log.info(
                "out_of_domain_response_dispatched",
                detected_domain=domain_val_str,
                language=str(resolved_lang),
            )
            return QueryResponse(
                request_id=request_id,
                answer=out_of_domain_answer,
                confidence_score=0.0,
                confidence_label=ConfidenceLabel.INSUFFICIENT,
                sources=[],
                caveats=["Topic outside GovGuide AI government service and business licensing domain."],
                explanation=f"Query belongs to unsupported domain '{domain_val_str}'. Cross-domain retrieval was prevented.",
                is_demo=False,
                is_conversational=False,
            )

        # ── Step 2c: Unknown Service Fast-path ───────────────────────────────
        if structured_query.search_parameters.get("is_unknown_service", False):
            unknown_name = structured_query.search_parameters.get("unknown_service_name") or "the requested service"
            unknown_answer = f"I couldn't find a matching verified government service for '{unknown_name}' in the current knowledge base. Please provide the service name or license code."
            log.info("unknown_service_response_dispatched", unknown_service_name=unknown_name)
            return QueryResponse(
                request_id=request_id,
                answer=unknown_answer,
                confidence_score=0.0,
                confidence_label=ConfidenceLabel.INSUFFICIENT,
                sources=[],
                caveats=["Unknown government service requested."],
                explanation=f"No matching canonical GovernmentService record found for '{unknown_name}'.",
                is_demo=False,
                is_conversational=False,
            )

        # ── Step 2d: Ambiguous Query Clarification Fast-path ───────────────────
        if structured_query.search_parameters.get("needs_clarification", False):
            detected_lang = structured_query.search_parameters.get("detected_language", "en")
            clar_type = structured_query.search_parameters.get("clarification_type")
            clarification_answer = get_clarification_response(detected_lang, clarification_type=clar_type)
            log.info(
                "ambiguous_clarification_dispatched",
                detected_language=detected_lang,
                clarification_type=clar_type,
            )
            return QueryResponse(
                request_id=request_id,
                answer=clarification_answer,
                confidence_score=0.5,
                confidence_label=ConfidenceLabel.MEDIUM,
                sources=[],
                caveats=["Query is ambiguous. Clarification requested."],
                explanation="The query requests a license or service without specifying the business type or specific service required.",
                is_demo=False,
                is_conversational=False,
            )

        # ── Step 3: Agent 2 — Retrieval Agent ─────────────────────────────────
        retrieval_task = AgentMessage(
            request_id=request_id,
            correlation_id=correlation_id,
            sender=AgentId.QUERY_AGENT,
            recipient=AgentId.RETRIEVAL_AGENT,
            message_type=MessageType.TASK,
            payload=RetrievalTaskPayload(
                structured_query=structured_query,
            ).model_dump(),
        )

        log.info(
            "dispatching_to_retrieval_agent",
            intent=structured_query.intent.value if hasattr(structured_query.intent, "value") else str(structured_query.intent),
            domain=structured_query.domain.value if hasattr(structured_query.domain, "value") else str(structured_query.domain),
        )
        r_start = time.monotonic()
        retrieval_agent = self.registry.get_agent(AgentId.RETRIEVAL_AGENT)
        retrieval_result_msg = await self.failure_handler.call_with_fallback(
            agent_fn=retrieval_agent.process,
            message=retrieval_task,
            agent_id=AgentId.RETRIEVAL_AGENT,
        )
        r_dur = int((time.monotonic() - r_start) * 1000)
        self.interaction_logger.log(retrieval_task, retrieval_result_msg, r_dur)

        if retrieval_result_msg.message_type == MessageType.ERROR:
            return self._error_response(request_id, retrieval_result_msg)

        retrieval_payload = retrieval_result_msg.payload
        evidence_bundle_dict = retrieval_payload.get("evidence_bundle", {})
        retrieval_confidence = retrieval_payload.get("retrieval_confidence", 0.0)
        sufficient_evidence = retrieval_payload.get("sufficient_evidence", False)

        log.info(
            "retrieval_stage_done",
            detected_domain=structured_query.domain.value if hasattr(structured_query.domain, "value") else str(structured_query.domain),
            knowledge_base_domain_supported=structured_query.is_domain_supported,
            retrieval_executed=structured_query.is_domain_supported,
            evidence_sufficient=sufficient_evidence,
            retrieval_confidence=retrieval_confidence,
        )

        detected_lang = structured_query.search_parameters.get("detected_language", "en")
        is_multilingual = structured_query.search_parameters.get("is_multilingual", False)

        # Also log for backward compatibility with existing tests
        research_compat_msg = AgentMessage(
            request_id=request_id,
            correlation_id=correlation_id,
            sender=AgentId.RESEARCH_AGENT,
            recipient=AgentId.ORCHESTRATOR,
            message_type=MessageType.RESULT,
            payload=ResearchResultPayload(
                nlp_analysis=NLPAnalysis(
                    intent=structured_query.intent,
                    intents=structured_query.intents,
                    domain=structured_query.domain,
                    is_domain_supported=structured_query.is_domain_supported,
                    entities=structured_query.entities,
                    expanded_query=structured_query.expanded_query,
                    keywords=structured_query.keywords,
                    language=detected_lang,
                    is_multilingual=is_multilingual,
                ),
                evidence_bundle=evidence_bundle_dict,
                retrieval_confidence=retrieval_confidence,
                sufficient_evidence=sufficient_evidence,
            ).model_dump(),
        )
        self.interaction_logger.log(query_task, research_compat_msg, q_dur + r_dur)

        # ── Step 4: Agent 3 — Response / Verification Agent ───────────────────
        nlp_analysis_obj = NLPAnalysis(
            intent=structured_query.intent,
            intents=structured_query.intents,
            domain=structured_query.domain,
            is_domain_supported=structured_query.is_domain_supported,
            entities=structured_query.entities,
            expanded_query=structured_query.expanded_query,
            keywords=structured_query.keywords,
            language=detected_lang,
            is_multilingual=is_multilingual,
        )

        response_task = AgentMessage(
            request_id=request_id,
            correlation_id=correlation_id,
            sender=AgentId.RETRIEVAL_AGENT,
            recipient=AgentId.RESPONSE_AGENT,
            message_type=MessageType.TASK,
            payload=AdvisoryTaskPayload(
                user_query=query,
                nlp_analysis=nlp_analysis_obj,
                evidence_bundle=evidence_bundle_dict,
                retrieval_confidence=retrieval_confidence,
                sufficient_evidence=sufficient_evidence,
                domain=structured_query.domain,
                is_domain_supported=structured_query.is_domain_supported,
            ).model_dump(),
        )

        log.info("dispatching_to_response_verification_agent")
        res_start = time.monotonic()
        response_agent = self.registry.get_agent(AgentId.RESPONSE_AGENT)
        response_result_msg = await self.failure_handler.call_with_fallback(
            agent_fn=response_agent.process,
            message=response_task,
            agent_id=AgentId.RESPONSE_AGENT,
        )
        res_dur = int((time.monotonic() - res_start) * 1000)
        self.interaction_logger.log(response_task, response_result_msg, res_dur)

        if response_result_msg.message_type == MessageType.ERROR:
            return self._error_response(request_id, response_result_msg)

        resp_payload = response_result_msg.payload

        if not structured_query.is_domain_supported:
            final_type = "unsupported_domain"
        elif not sufficient_evidence:
            final_type = "insufficient_evidence"
        else:
            final_type = "grounded_response"

        log.info(
            "multi_agent_pipeline_complete",
            detected_domain=structured_query.domain.value if hasattr(structured_query.domain, "value") else str(structured_query.domain),
            detected_intent=structured_query.intent.value if hasattr(structured_query.intent, "value") else str(structured_query.intent),
            knowledge_base_domain_supported=structured_query.is_domain_supported,
            retrieval_executed=structured_query.is_domain_supported,
            evidence_sufficient=sufficient_evidence,
            final_response_type=final_type,
            confidence=resp_payload.get("confidence_label"),
            sources=len(resp_payload.get("sources", [])),
            total_duration_ms=q_dur + r_dur + res_dur,
        )

        has_live_llm = bool(get_settings().LLM_API_KEY and get_settings().LLM_MODEL)

        return QueryResponse(
            request_id=request_id,
            answer=resp_payload.get("answer", ""),
            confidence_score=resp_payload.get("confidence_score", 0.0),
            confidence_label=resp_payload.get("confidence_label", ConfidenceLabel.INSUFFICIENT),
            sources=[
                SourceReference(**s) if isinstance(s, dict) else s
                for s in resp_payload.get("sources", [])
            ],
            caveats=resp_payload.get("caveats", []),
            explanation=resp_payload.get("explanation"),
            is_demo=not has_live_llm,
        )

    def _injection_blocked_response(self, request_id: str) -> QueryResponse:
        return QueryResponse(
            request_id=request_id,
            answer=(
                "Your query could not be processed because it contains content "
                "that may attempt to manipulate the AI system. "
                "Please rephrase your question."
            ),
            confidence_score=0.0,
            confidence_label=ConfidenceLabel.INSUFFICIENT,
            caveats=["Query blocked by security filter."],
        )

    def _error_response(self, request_id: str, error_msg: AgentMessage) -> QueryResponse:
        payload = error_msg.payload or {}
        fallback = payload.get(
            "fallback_response",
            "I could not find sufficient official evidence to provide a reliable answer.",
        )
        return QueryResponse(
            request_id=request_id,
            answer=fallback,
            confidence_score=0.0,
            confidence_label=ConfidenceLabel.INSUFFICIENT,
            caveats=["An agent error occurred. Please try again."],
        )
