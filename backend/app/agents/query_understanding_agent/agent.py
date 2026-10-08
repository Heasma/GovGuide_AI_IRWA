"""
GovGuide AI — Query Understanding Agent (Agent 1)

Responsibilities:
1. Accepts raw user query and executes multilingual, Thanglish, typo-tolerant NLP analysis.
2. Evaluates prompt injection & safety rules strictly on the original query before normalization.
3. Classifies user intent (service_information, eligibility, required_documents, application_procedure, fees, renewal, office_information, etc.).
4. Performs Named Entity Recognition (NER) to extract government services, organizations, locations, license codes, and fee amounts.
5. Applies domain-specific query expansion for hybrid BM25 + semantic retrieval.
6. Detects query ambiguity.
7. Produces a structured query specification (StructuredQueryPayload) for downstream retrieval & advisory agents.
"""

import structlog
from typing import Optional, Dict, Any, List

from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType, TaskType,
    QueryUnderstandingTaskPayload, StructuredQueryPayload,
    EntityExtraction, Intent, Domain, ErrorCode, ErrorPayload,
)
from app.nlp.query_understanding_service import QueryUnderstandingService, QueryUnderstandingResult

logger = structlog.get_logger(__name__)


class QueryUnderstandingAgent:
    """
    Intelligent Agent specialized in multilingual NLP analysis, intent understanding,
    typo normalization, entity extraction, and query structure generation.
    """

    AGENT_ID = AgentId.QUERY_AGENT

    def __init__(self, service: Optional[QueryUnderstandingService] = None):
        self.service = service or QueryUnderstandingService()
        logger.info("query_understanding_agent_initialized")

    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Processes an incoming query task using QueryUnderstandingService and returns a structured query result.
        """
        payload = message.payload if isinstance(message.payload, dict) else message.payload.model_dump()
        raw_query = payload.get("raw_query") or payload.get("user_query") or ""
        session_id = payload.get("session_id")
        context_entity = payload.get("context_entity")

        logger.info(
            "query_understanding_processing",
            request_id=message.request_id,
            query_length=len(raw_query),
        )

        # Empty / whitespace check
        if not raw_query or not raw_query.strip():
            logger.warning("query_validation_failed_empty")
            return AgentMessage(
                request_id=message.request_id,
                correlation_id=message.correlation_id,
                sender=self.AGENT_ID,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                payload=ErrorPayload(
                    error_code=ErrorCode.VALIDATION_FAILED,
                    error_message="Query cannot be empty.",
                    fallback_response="Input validation error: Query must be at least 1 characters.",
                ).model_dump(),
            )

        # ── Execute Query Understanding Pipeline via Service ──────────────────
        result: QueryUnderstandingResult = self.service.understand_query(
            query=raw_query,
            session_id=session_id,
            context_entity=context_entity,
        )

        # ── Handle Security / Validation Failures ──────────────────────────────
        if not result.is_safe:
            is_val_err = result.search_parameters.get("error_type") == "validation_failed"
            err_code = ErrorCode.VALIDATION_FAILED if is_val_err else ErrorCode.INJECTION_DETECTED
            err_reason = result.search_parameters.get("reason") or result.search_parameters.get("error") or "Security check failed."
            safe_resp = result.search_parameters.get("safe_response") or (
                "Your query could not be processed because it contains content "
                "that may attempt to manipulate the AI system. Please rephrase your question."
            )

            logger.warning("query_understanding_rejected", error_code=err_code.value, reason=err_reason)
            return AgentMessage(
                request_id=message.request_id,
                correlation_id=message.correlation_id,
                sender=self.AGENT_ID,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                payload=ErrorPayload(
                    error_code=err_code,
                    error_message=err_reason,
                    fallback_response=safe_resp,
                ).model_dump(),
            )

        # ── Assemble StructuredQueryPayload for Downstream Agents ─────────────
        result_payload = self.service.to_structured_payload(result)

        logger.info(
            "query_understanding_complete",
            request_id=message.request_id,
            original_query=result.original_query,
            normalized_query=result.normalized_query,
            detected_language=result.detected_language,
            intent=result.intent.value if hasattr(result.intent, "value") else str(result.intent),
            intents=[i.value if hasattr(i, "value") else str(i) for i in result.intents],
            domain=result.domain.value if hasattr(result.domain, "value") else str(result.domain),
            is_domain_supported=result.is_domain_supported,
            entities_count=len(result.entities),
            is_ambiguous=result.is_ambiguous,
        )

        return AgentMessage(
            request_id=message.request_id,
            correlation_id=message.correlation_id,
            sender=self.AGENT_ID,
            recipient=message.sender,
            message_type=MessageType.RESULT,
            payload=result_payload.model_dump(),
        )
