"""
GovGuide AI — Query Understanding Service

Central modular service providing multilingual, Thanglish, typo-tolerant,
and spelling-mistake-tolerant natural language query understanding.

Pipeline Architecture:
1. Input Validation & Original Query Preservation
2. Security & Prompt Injection Pre-check (Original Query)
3. Language & Script Detection (English, Tamil, Sinhala, Thanglish, Singlish, Code-mixed)
4. Multilingual / Thanglish Normalization
5. Domain-Aware Typo & Spelling Correction
6. Abbreviation & Informal Expression Expansion
7. Conservative Intent Extraction & Classification
8. Named Entity Recognition (NER) & Context Entity Resolution
9. Domain Classification & Gating
10. Query Expansion for Hybrid Information Retrieval (BM25 + Semantic)
11. Ambiguity Detection
12. Defense-in-Depth Security Verification (Normalized Representation)
"""

import re
import structlog
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.orchestrator.message_schema import (
    Intent,
    Domain,
    EntityExtraction,
    StructuredQueryPayload,
)
from app.nlp.language_detector import detect_language, LanguageInfo, LanguageCode
from app.nlp.thanglish_normalizer import normalize_thanglish_and_multilingual
from app.nlp.spelling_corrector import correct_spelling
from app.nlp.abbreviation_expander import expand_abbreviations
from app.nlp.intent_classifier import (
    classify_intents,
    classify_intent,
    classify_conversation_type,
    is_conversational_query,
)
from app.nlp.domain_detector import classify_domain, SUPPORTED_DOMAINS
from app.nlp.entity_extractor import extract_entities, resolve_query_entity, ExtractedEntity
from app.nlp.preprocessor import expand_query, tokenize_query, preprocess
from app.security.prompt_injection_guard import classify_security_query, SecurityClassification
from app.security.input_validator import sanitize_query

logger = structlog.get_logger(__name__)


class QueryUnderstandingResult(BaseModel):
    """Rich structured output from the QueryUnderstandingService."""
    original_query: str
    cleaned_query: str
    normalized_query: str
    expanded_query: str
    language_info: LanguageInfo
    detected_language: str
    is_multilingual: bool
    intent: Intent
    intents: List[Intent]
    domain: Domain
    is_domain_supported: bool
    entities: List[EntityExtraction]
    keywords: List[str]
    is_safe: bool = True
    is_ambiguous: bool = False
    corrections_applied: List[str] = Field(default_factory=list)
    expansions_applied: List[str] = Field(default_factory=list)
    search_parameters: Dict[str, Any] = Field(default_factory=dict)
    conversation_type: Optional[str] = None
    is_conversational: bool = False


class QueryUnderstandingService:
    """
    Modular, deterministic service coordinating language detection,
    typo normalization, Thanglish understanding, and intent extraction.
    """

    def __init__(self):
        logger.info("query_understanding_service_initialized")

    def normalize_text(self, text: str) -> Tuple[str, LanguageInfo, List[str], List[str]]:
        """
        Executes the normalization steps on a text query:
        1. Language detection
        2. Thanglish / Multilingual rewrite
        3. Abbreviation expansion
        4. Spelling & typo correction
        5. Whitespace and punctuation formatting
        """
        if not text:
            return "", LanguageInfo(language=LanguageCode.UNKNOWN), [], []

        # 1. Detect language on original text
        lang_info = detect_language(text)

        # 2. Multilingual / Thanglish Normalization
        thanglish_normalized, was_thanglish = normalize_thanglish_and_multilingual(text)

        # 3. Abbreviation & Informal Expression Expansion
        fully_expanded, expansions = expand_abbreviations(thanglish_normalized)

        # 4. Spelling & Typo Correction
        spelling_corrected, corrections = correct_spelling(fully_expanded)

        # 5. Final whitespace normalization
        clean_normalized = preprocess(spelling_corrected)

        return clean_normalized, lang_info, corrections, expansions

    def understand_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        context_entity: Optional[str] = None,
    ) -> QueryUnderstandingResult:
        """
        Main entry point for processing and understanding citizen queries.
        Follows the strict security-first workflow.
        """
        raw_query = query if query is not None else ""

        # ── Step 1: Input Validation & Sanitization ───────────────────────────
        if not raw_query or not raw_query.strip():
            logger.warning("query_validation_failed_empty")
            return QueryUnderstandingResult(
                original_query=raw_query,
                cleaned_query=raw_query,
                normalized_query=raw_query,
                expanded_query=raw_query,
                language_info=LanguageInfo(language=LanguageCode.UNKNOWN),
                detected_language="unknown",
                is_multilingual=False,
                intent=Intent.UNKNOWN,
                intents=[Intent.UNKNOWN],
                domain=Domain.UNKNOWN,
                is_domain_supported=False,
                entities=[],
                keywords=[],
                is_safe=False,
                is_ambiguous=True,
                search_parameters={"error": "Query must be at least 1 characters.", "error_type": "validation_failed"},
            )

        try:
            sanitized = sanitize_query(raw_query)
        except ValueError as exc:
            logger.warning("query_sanitization_failed", error=str(exc))
            # Return validation-failed structured result
            return QueryUnderstandingResult(
                original_query=raw_query,
                cleaned_query=raw_query,
                normalized_query=raw_query,
                expanded_query=raw_query,
                language_info=LanguageInfo(language=LanguageCode.UNKNOWN),
                detected_language="unknown",
                is_multilingual=False,
                intent=Intent.UNKNOWN,
                intents=[Intent.UNKNOWN],
                domain=Domain.UNKNOWN,
                is_domain_supported=False,
                entities=[],
                keywords=[],
                is_safe=False,
                is_ambiguous=True,
                search_parameters={"error": str(exc), "error_type": "validation_failed"},
            )

        # ── Step 2: Prompt Injection Check on ORIGINAL Query (Mandatory Security)
        sec_check_original = classify_security_query(raw_query)
        if not sec_check_original.is_safe:
            logger.warning(
                "query_security_check_failed_on_original",
                classification=sec_check_original.classification.value,
                matched_pattern=sec_check_original.matched_pattern,
            )
            return QueryUnderstandingResult(
                original_query=raw_query,
                cleaned_query=sanitized,
                normalized_query=sanitized,
                expanded_query=sanitized,
                language_info=LanguageInfo(language=LanguageCode.ENGLISH),
                detected_language="english",
                is_multilingual=False,
                intent=Intent.UNKNOWN,
                intents=[Intent.UNKNOWN],
                domain=Domain.UNKNOWN,
                is_domain_supported=False,
                entities=[],
                keywords=[],
                is_safe=False,
                is_ambiguous=False,
                search_parameters={
                    "security_blocked": True,
                    "classification": sec_check_original.classification.value,
                    "reason": sec_check_original.reason,
                    "safe_response": sec_check_original.safe_response,
                },
            )

        # ── Step 3: Multilingual, Thanglish & Typo Normalization ──────────────
        normalized_query, lang_info, corrections, expansions = self.normalize_text(sanitized)

        # ── Step 4: Defense-in-Depth Security Verification on Normalized Query ─
        sec_check_norm = classify_security_query(normalized_query)
        if not sec_check_norm.is_safe:
            logger.warning(
                "query_security_check_failed_on_normalized",
                classification=sec_check_norm.classification.value,
            )
            return QueryUnderstandingResult(
                original_query=raw_query,
                cleaned_query=sanitized,
                normalized_query=normalized_query,
                expanded_query=normalized_query,
                language_info=lang_info,
                detected_language=lang_info.language.value,
                is_multilingual=lang_info.is_multilingual,
                intent=Intent.UNKNOWN,
                intents=[Intent.UNKNOWN],
                domain=Domain.UNKNOWN,
                is_domain_supported=False,
                entities=[],
                keywords=[],
                is_safe=False,
                is_ambiguous=False,
                search_parameters={
                    "security_blocked": True,
                    "classification": sec_check_norm.classification.value,
                    "reason": sec_check_norm.reason,
                    "safe_response": sec_check_norm.safe_response,
                },
            )

        # ── Step 5: Business Activity & Entity Extraction ─────────────────────
        from app.nlp.activity_extractor import extract_business_activity, BusinessActivityType
        business_activity = extract_business_activity(normalized_query)

        # ── Step 6: Intent Classification (Conservative & Robust) ─────────────
        intents = classify_intents(normalized_query)
        intent = intents[0] if intents else Intent.GENERAL

        conv_type = classify_conversation_type(normalized_query)
        is_conversational = is_conversational_query(normalized_query) or intent in (
            Intent.CONVERSATIONAL, Intent.THANKS, Intent.ACKNOWLEDGEMENT,
            Intent.GOODBYE, Intent.GREETING
        )
        retrieval_required = not is_conversational

        # ── Step 7: Domain Classification ─────────────────────────────────────
        domain = classify_domain(normalized_query)
        is_supported = domain in SUPPORTED_DOMAINS

        # ── Step 8: Named Entity Recognition & Context Resolution ─────────────
        resolved_entity, entity_source, context_switched = resolve_query_entity(
            normalized_query, context_entity
        )

        extracted_raw = extract_entities(normalized_query)
        entities = [
            EntityExtraction(
                text=e.text,
                label=e.label,
                confidence=e.confidence,
                start_char=e.start_char,
                end_char=e.end_char,
            )
            for e in extracted_raw
        ]

        has_service_or_code = any(e.label in ("SERVICE", "LICENSE_CODE") for e in entities)

        if not is_conversational:
            if resolved_entity and not has_service_or_code:
                entities.append(
                    EntityExtraction(
                        text=resolved_entity,
                        label="SERVICE",
                        confidence=0.95,
                    )
                )
                domain = Domain.BUSINESS_LICENSE
                is_supported = True
            elif resolved_entity and has_service_or_code:
                domain = Domain.BUSINESS_LICENSE
                is_supported = True

        # ── Step 9: Domain Query Expansion for Retrieval ──────────────────────
        expanded_query_str = expand_query(normalized_query)
        if resolved_entity and not is_conversational and resolved_entity not in expanded_query_str:
            expanded_query_str = f"{resolved_entity} {expanded_query_str}"

        tokens = tokenize_query(normalized_query, remove_stopwords=True)

        # ── Step 10: Ambiguity, Follow-Up & Clarification Detection ───────────
        has_specific_service = any(
            e.label in ("SERVICE", "LICENSE_CODE")
            and e.text.lower() not in ("business license", "license", "licenses", "city license")
            for e in entities
        ) or (
            resolved_entity
            and resolved_entity.lower() not in ("business license", "license", "licenses", "city license")
            and entity_source not in ("none",)
        )

        specific_action_intents = {
            Intent.FEES,
            Intent.REQUIRED_DOCUMENTS,
            Intent.OFFICE_INFORMATION,
            Intent.PROCEDURE,
            Intent.APPLICATION_PROCEDURE,
            Intent.RENEWAL,
        }
        has_action_intent = any(it in specific_action_intents for it in intents) or intent in specific_action_intents

        # Detect short context-dependent follow-up questions
        is_short_followup_pattern = bool(re.search(
            r"^\s*(?:for\s+me\s+|can\s+you\s+|please\s+|could\s+you\s+|tell\s+me\s+|what\s+about\s+)?(?:documents\??|document\??|fees\??|fee\??|cost\??|pricing\??|where\??|where\s+to\s+go\??|enga\??|enga\s+poganum\??|epdi\??|how\??|how\s+to\s+apply\??|eligibility\??|explain\??|explain\s+pannu\??|enna\s+meaning\??|more\s+details\??)\s*$",
            normalized_query,
            re.I,
        )) or bool(re.search(
            r"^\s*(?:ennaku|enakku|please|ungalluku)?\s*(?:explain|explain\s+pannu|vilakkam\s+sollunga|details\s+kudunga)\s*\??\s*$",
            raw_query,
            re.I,
        ))

        needs_clarification = False
        clarification_type = None

        if not is_supported:
            needs_clarification = False

        elif is_short_followup_pattern:
            if not context_entity:
                needs_clarification = True
                if any(w in (raw_query + " " + normalized_query).lower() for w in ("explain", "meaning", "details", "vilakkam")):
                    clarification_type = "explain_topic"
                else:
                    clarification_type = "missing_context"
                retrieval_required = False

        elif not is_conversational and not has_specific_service and not context_entity and not has_action_intent:
            # 1. Tailoring inquiry
            if business_activity.activity_type == BusinessActivityType.SERVICE_TAILORING:
                needs_clarification = True
                clarification_type = "tailoring_setup"
                retrieval_required = False

            # 2. Generic Retail with unspecified goods
            elif business_activity.activity_type == BusinessActivityType.GENERIC_RETAIL:
                needs_clarification = True
                clarification_type = "retail_goods"
                retrieval_required = False

            # 3. Generic Business / Ambiguous License request
            elif business_activity.activity_type == BusinessActivityType.GENERIC_BUSINESS or bool(re.search(
                r"\b(which\s+license|what\s+license|need\s+(?:to\s+get\s+|to\s+obtain\s+|a\s+)?license|want\s+(?:to\s+get\s+|to\s+obtain\s+|a\s+)?license|obtain\s+a\s+license|get\s+a\s+license|licen[cs]e\s+(?:venum|edukanum|vanganum)|not\s+specified\s+business|enna\s+business\s+nu\s+sollala|business\s+licen[cs]e\s+theva|licen[cs]e\s+edukanum|licen[cs]e\s+venum)\b",
                raw_query + " " + normalized_query,
                re.I,
            )) or bool(re.search(
                r"^\s*(?:i\s+need|i\s+want|need|want|get|obtain|how\s+can\s+i\s+get)?\s*(?:a\s+)?(?:business\s+)?licen[cs]e\s*\??\s*$",
                normalized_query,
                re.I,
            )):
                needs_clarification = True
                clarification_type = "business_type"
                retrieval_required = False

        is_ambiguous = needs_clarification or (
            len(tokens) <= 1 and intent == Intent.GENERAL and not entities and not is_conversational and is_supported
        )

        search_params = {
            "intent": intent.value if hasattr(intent, "value") else str(intent),
            "intents": [i.value if hasattr(i, "value") else str(i) for i in intents],
            "conversation_type": conv_type,
            "domain": domain.value if hasattr(domain, "value") else str(domain),
            "is_domain_supported": is_supported,
            "retrieval_required": retrieval_required,
            "business_activity": business_activity.activity_type.value,
            "is_food_related": business_activity.is_food_related,
            "active_entity_preserved": bool(context_entity or resolved_entity),
            "entity_count": len(entities),
            "target_services": [e.text for e in entities if e.label == "SERVICE"] or ([resolved_entity] if resolved_entity and retrieval_required else []),
            "target_codes": [e.text for e in entities if e.label == "LICENSE_CODE"],
            "target_orgs": [e.text for e in entities if e.label == "ORGANIZATION"],
            "target_locations": [e.text for e in entities if e.label == "LOCATION"],
            "resolved_context_entity": resolved_entity if retrieval_required else context_entity,
            "entity_source": entity_source,
            "context_switched": context_switched,
            "detected_language": lang_info.language.value,
            "is_multilingual": lang_info.is_multilingual,
            "needs_clarification": needs_clarification,
            "clarification_type": clarification_type,
            "corrections_applied": corrections,
            "expansions_applied": expansions,
        }

        logger.info(
            "query_understanding_service_processed",
            original_query=raw_query,
            normalized_query=normalized_query,
            detected_language=lang_info.language.value,
            is_multilingual=lang_info.is_multilingual,
            intent=intent.value if hasattr(intent, "value") else str(intent),
            domain=domain.value if hasattr(domain, "value") else str(domain),
            corrections=len(corrections),
            expansions=len(expansions),
        )

        return QueryUnderstandingResult(
            original_query=raw_query,
            cleaned_query=sanitized,
            normalized_query=normalized_query,
            expanded_query=expanded_query_str,
            language_info=lang_info,
            detected_language=lang_info.language.value,
            is_multilingual=lang_info.is_multilingual,
            intent=intent,
            intents=intents,
            domain=domain,
            is_domain_supported=is_supported,
            entities=entities,
            keywords=tokens[:10],
            is_safe=True,
            is_ambiguous=is_ambiguous,
            corrections_applied=corrections,
            expansions_applied=expansions,
            search_parameters=search_params,
            conversation_type=conv_type,
            is_conversational=is_conversational,
        )

    def to_structured_payload(self, result: QueryUnderstandingResult) -> StructuredQueryPayload:
        """Converts QueryUnderstandingResult into inter-agent StructuredQueryPayload."""
        return StructuredQueryPayload(
            original_query=result.original_query,
            cleaned_query=result.normalized_query,
            expanded_query=result.expanded_query,
            intent=result.intent,
            intents=result.intents,
            domain=result.domain,
            is_domain_supported=result.is_domain_supported,
            entities=result.entities,
            keywords=result.keywords,
            is_safe=result.is_safe,
            is_ambiguous=result.is_ambiguous,
            search_parameters=result.search_parameters,
        )
