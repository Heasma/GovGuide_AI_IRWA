"""
GovGuide AI — Query Understanding Agent (Agent 1)

Responsibilities:
1. Accepts raw user query and performs NLP preprocessing.
2. Checks for safety, manipulation, and prompt injection patterns.
3. Classifies user intent (service_information, eligibility, required_documents, application_procedure, fees, renewal, office_information, etc.).
4. Performs Named Entity Recognition (NER) to extract government services, organizations, locations, license codes, and fee amounts.
5. Applies domain-specific query expansion.
6. Detects query ambiguity.
7. Produces a structured query specification (StructuredQueryPayload) for the Retrieval Agent.
"""

import structlog
from typing import Optional, Dict, Any, List

from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType, TaskType,
    QueryUnderstandingTaskPayload, StructuredQueryPayload,
    EntityExtraction, Intent, Domain, ErrorCode, ErrorPayload,
)
from app.nlp.preprocessor import preprocess, expand_query, tokenize_query
from app.nlp.intent_classifier import classify_intent, classify_intents, classify_conversation_type, is_conversational_query
from app.nlp.domain_detector import classify_domain, SUPPORTED_DOMAINS
from app.nlp.entity_extractor import extract_entities, resolve_query_entity
from app.security.prompt_injection_guard import check_for_injection
from app.security.input_validator import sanitize_query

logger = structlog.get_logger(__name__)


class QueryUnderstandingAgent:
    """
    Intelligent Agent specialized in NLP analysis, intent understanding,
    entity extraction, and query structure generation.
    """

    AGENT_ID = AgentId.QUERY_AGENT

    def __init__(self):
        logger.info("query_understanding_agent_initialized")

    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Processes an incoming query task and returns a structured query result.
        """
        payload = message.payload if isinstance(message.payload, dict) else message.payload.model_dump()
        raw_query = payload.get("raw_query") or payload.get("user_query") or ""

        logger.info(
            "query_understanding_processing",
            request_id=message.request_id,
            query_length=len(raw_query),
        )

        # ── Step 1: Input Validation & Sanitization ───────────────────────────
        try:
            clean_query = sanitize_query(raw_query) if raw_query else ""
        except ValueError as exc:
            logger.warning("query_validation_failed", error=str(exc))
            return AgentMessage(
                request_id=message.request_id,
                correlation_id=message.correlation_id,
                sender=self.AGENT_ID,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                payload=ErrorPayload(
                    error_code=ErrorCode.VALIDATION_FAILED,
                    error_message=str(exc),
                    fallback_response=f"Input validation error: {str(exc)}",
                ).model_dump(),
            )

        # ── Step 2: Prompt Injection & Safety Check ───────────────────────────
        injection_check = check_for_injection(clean_query)
        if not injection_check.is_safe:
            logger.warning("query_injection_detected", pattern=injection_check.matched_pattern)
            return AgentMessage(
                request_id=message.request_id,
                correlation_id=message.correlation_id,
                sender=self.AGENT_ID,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                payload=ErrorPayload(
                    error_code=ErrorCode.INJECTION_DETECTED,
                    error_message=injection_check.reason,
                    fallback_response=(
                        "Your query could not be processed because it contains content "
                        "that may attempt to manipulate the AI system. Please rephrase your question."
                    ),
                ).model_dump(),
            )

        # ── Step 3: NLP Preprocessing & Expansion ─────────────────────────────
        normalized_query = preprocess(clean_query)
        expanded = expand_query(normalized_query)
        tokens = tokenize_query(normalized_query, remove_stopwords=True)

        # ── Step 4: Multi-Intent & Domain Classification ──────────────────────
        intents = classify_intents(normalized_query)
        intent = intents[0]
        domain = classify_domain(normalized_query)
        is_supported = domain in SUPPORTED_DOMAINS
        conv_type = classify_conversation_type(normalized_query)
        is_conversational = is_conversational_query(normalized_query) or intent in (
            Intent.CONVERSATIONAL, Intent.THANKS, Intent.ACKNOWLEDGEMENT,
            Intent.GOODBYE, Intent.GREETING
        )
        retrieval_required = not is_conversational

        # ── Step 5: Named Entity Recognition & Context Resolution ─────────────
        context_entity = payload.get("context_entity")
        resolved_entity, entity_source, context_switched = resolve_query_entity(normalized_query, context_entity)

        extracted = extract_entities(normalized_query)
        entities = [
            EntityExtraction(
                text=e.text,
                label=e.label,
                confidence=e.confidence,
                start_char=e.start_char,
                end_char=e.end_char,
            )
            for e in extracted
        ]

        has_service_or_code = any(e.label in ("SERVICE", "LICENSE_CODE") for e in entities)

        if not is_conversational:
            if resolved_entity and not has_service_or_code:
                # Bind context entity from conversation history or pronoun resolution
                entities.append(
                    EntityExtraction(
                        text=resolved_entity,
                        label="SERVICE",
                        confidence=0.95,
                    )
                )
                expanded = f"{resolved_entity} {expanded}"
                domain = Domain.BUSINESS_LICENSE
                is_supported = True
            elif resolved_entity and has_service_or_code:
                domain = Domain.BUSINESS_LICENSE
                is_supported = True

        if is_conversational:
            logger.info(
                "query_context_resolved",
                query=raw_query,
                intent="CONVERSATIONAL",
                conversation_type=conv_type or "CASUAL_CONVERSATION",
                retrieval_required=False,
                active_entity_preserved=bool(context_entity or resolved_entity),
            )
        else:
            logger.info(
                "query_context_resolved",
                query=raw_query,
                intent=intent.value if hasattr(intent, "value") else str(intent),
                resolved_entity=resolved_entity,
                entity_source=entity_source,
                retrieval_required=True,
                context_switched=context_switched,
            )

        # ── Step 6: Ambiguity & Search Parameter Formulation ──────────────────
        is_ambiguous = len(tokens) <= 1 and intent == Intent.GENERAL and not entities and not is_conversational

        search_params = {
            "intent": intent.value if hasattr(intent, "value") else str(intent),
            "intents": [i.value if hasattr(i, "value") else str(i) for i in intents],
            "conversation_type": conv_type,
            "domain": domain.value if hasattr(domain, "value") else str(domain),
            "is_domain_supported": is_supported,
            "retrieval_required": retrieval_required,
            "active_entity_preserved": bool(context_entity or resolved_entity),
            "entity_count": len(entities),
            "target_services": [e.text for e in entities if e.label == "SERVICE"] or ([resolved_entity] if resolved_entity and retrieval_required else []),
            "target_codes": [e.text for e in entities if e.label == "LICENSE_CODE"],
            "target_orgs": [e.text for e in entities if e.label == "ORGANIZATION"],
            "target_locations": [e.text for e in entities if e.label == "LOCATION"],
            "resolved_context_entity": resolved_entity if retrieval_required else context_entity,
            "entity_source": entity_source,
            "context_switched": context_switched,
        }

        result_payload = StructuredQueryPayload(
            original_query=raw_query,
            cleaned_query=normalized_query,
            expanded_query=expanded,
            intent=intent,
            intents=intents,
            domain=domain,
            is_domain_supported=is_supported,
            entities=entities,
            keywords=tokens[:10],
            is_safe=True,
            is_ambiguous=is_ambiguous,
            search_parameters=search_params,
        )

        logger.info(
            "query_understanding_complete",
            request_id=message.request_id,
            intent=intent.value if hasattr(intent, "value") else str(intent),
            intents=[i.value if hasattr(i, "value") else str(i) for i in intents],
            domain=domain.value if hasattr(domain, "value") else str(domain),
            is_domain_supported=is_supported,
            entities_count=len(entities),
            is_ambiguous=is_ambiguous,
        )

        return AgentMessage(
            request_id=message.request_id,
            correlation_id=message.correlation_id,
            sender=self.AGENT_ID,
            recipient=message.sender,
            message_type=MessageType.RESULT,
            payload=result_payload.model_dump(),
        )
