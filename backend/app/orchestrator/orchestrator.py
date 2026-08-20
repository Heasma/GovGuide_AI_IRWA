"""
GovGuide AI — Agent Orchestrator
Coordinates the full query pipeline:
  User Query → Research Agent → Advisory Agent → Validated Response
"""

import uuid
import time
import structlog
from typing import Optional

from app.orchestrator.message_schema import (
    AgentId, MessageType, AgentMessage,
    ResearchTaskPayload, AdvisoryTaskPayload,
    ErrorCode, ErrorPayload,
    ConfidenceLabel,
)
from app.orchestrator.agent_registry import AgentRegistry
from app.orchestrator.failure_handler import FailureHandler
from app.orchestrator.interaction_logger import InteractionLogger
from app.security.prompt_injection_guard import assert_safe
from app.schemas import QueryResponse, SourceReference

logger = structlog.get_logger(__name__)


class Orchestrator:
    """
    Central orchestrator that manages the multi-agent query pipeline.

    Flow:
      1. Validate + sanitize user query
      2. Check for prompt injection
      3. Send ResearchTask to Research Agent
      4. Receive EvidenceBundle
      5. Send AdvisoryTask (with evidence) to Advisory Agent
      6. Receive validated response
      7. Return QueryResponse to API layer
    """

    def __init__(self):
        self.registry = AgentRegistry()
        self.failure_handler = FailureHandler()
        self.interaction_logger = InteractionLogger()

    async def process_query(
        self,
        query: str,
        request_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> QueryResponse:
        """
        Full orchestration pipeline. Returns a QueryResponse for the API layer.
        """
        log = logger.bind(request_id=request_id, user_id=user_id)
        correlation_id = str(uuid.uuid4())

        # ── Step 1: Prompt injection check ───────────────────────────────────
        try:
            assert_safe(query)
        except ValueError as e:
            log.warning("injection_detected", detail=str(e))
            return self._injection_blocked_response(request_id)

        # ── Step 1b: Friendly greeting check ─────────────────────────────────
        import re
        if re.match(r"^(hi|hello|hey|good\s+(morning|afternoon|evening)|greetings|hi\s+there|hello\s+there|howdy)[!.]*$", query.strip(), re.I):
            return QueryResponse(
                request_id=request_id,
                answer=(
                    "Hello! I am GovGuide AI, your City of Chicago government services and business licensing assistant. "
                    "How can I help you today? You can ask me about business licenses (such as Retail Food, Limited Business, or Children's Services), "
                    "application procedures, required documentation, fees, or City department offices."
                ),
                confidence_score=1.0,
                confidence_label=ConfidenceLabel.HIGH,
                sources=[],
                caveats=[],
                explanation="Greeting response provided by assistant.",
                is_demo=False,
            )

        # ── Step 2: Build & send task to Research Agent ───────────────────────
        research_task = AgentMessage(
            request_id=request_id,
            correlation_id=correlation_id,
            sender=AgentId.ORCHESTRATOR,
            recipient=AgentId.RESEARCH_AGENT,
            message_type=MessageType.TASK,
            payload=ResearchTaskPayload(
                user_query=query,
                session_id=session_id,
            ).model_dump(),
        )

        log.info("dispatching_research_task")
        start = time.monotonic()

        research_agent = self.registry.get_agent(AgentId.RESEARCH_AGENT)
        research_result_msg = await self.failure_handler.call_with_fallback(
            agent_fn=research_agent.process,
            message=research_task,
            agent_id=AgentId.RESEARCH_AGENT,
        )
        research_duration_ms = int((time.monotonic() - start) * 1000)

        self.interaction_logger.log(research_task, research_result_msg, research_duration_ms)

        if research_result_msg.message_type == MessageType.ERROR:
            return self._error_response(request_id, research_result_msg)

        research_payload = research_result_msg.payload

        # ── Step 3: Build & send task to Advisory Agent ───────────────────────
        advisory_task = AgentMessage(
            request_id=request_id,
            correlation_id=correlation_id,
            sender=AgentId.ORCHESTRATOR,
            recipient=AgentId.ADVISORY_AGENT,
            message_type=MessageType.TASK,
            payload=AdvisoryTaskPayload(
                user_query=query,
                nlp_analysis=research_payload["nlp_analysis"],
                evidence_bundle=research_payload["evidence_bundle"],
                retrieval_confidence=research_payload["retrieval_confidence"],
                sufficient_evidence=research_payload["sufficient_evidence"],
            ).model_dump(),
        )

        log.info("dispatching_advisory_task")
        adv_start = time.monotonic()

        advisory_agent = self.registry.get_agent(AgentId.ADVISORY_AGENT)
        advisory_result_msg = await self.failure_handler.call_with_fallback(
            agent_fn=advisory_agent.process,
            message=advisory_task,
            agent_id=AgentId.ADVISORY_AGENT,
        )
        advisory_duration_ms = int((time.monotonic() - adv_start) * 1000)

        self.interaction_logger.log(advisory_task, advisory_result_msg, advisory_duration_ms)

        if advisory_result_msg.message_type == MessageType.ERROR:
            return self._error_response(request_id, advisory_result_msg)

        adv_payload = advisory_result_msg.payload
        log.info(
            "pipeline_complete",
            confidence=adv_payload.get("confidence_label"),
            sources=len(adv_payload.get("sources", [])),
        )

        from app.config import get_settings
        has_live_llm = bool(get_settings().LLM_API_KEY and get_settings().LLM_MODEL)

        return QueryResponse(
            request_id=request_id,
            answer=adv_payload.get("answer", ""),
            confidence_score=adv_payload.get("confidence_score", 0.0),
            confidence_label=adv_payload.get("confidence_label", ConfidenceLabel.INSUFFICIENT),
            sources=[
                SourceReference(**s)
                for s in adv_payload.get("sources", [])
            ],
            caveats=adv_payload.get("caveats", []),
            explanation=adv_payload.get("explanation"),
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
