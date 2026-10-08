"""
GovGuide AI — Named Entity Recognition & Entity Extractor

Extracts domain-specific entities from citizen and business queries:
- SERVICES: Government service names & license categories
- LOCATIONS: Municipalities, addresses, city facilities
- ORGANIZATIONS: Municipal departments, agencies, divisions
- LICENSE_CODES: Numerical and code identifiers (e.g., 1006, 1010, 1011)
- FEE_AMOUNTS: Monetary fee expressions (e.g., $660, $250)
- DATES_PERIODS: Timeframes, renewal intervals (e.g., 2 years, biennial)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class ExtractedEntity(BaseModel):
    """Structured representation of an extracted entity."""
    text: str
    label: str  # SERVICE, LOCATION, ORGANIZATION, LICENSE_CODE, FEE_AMOUNT, DATE_PERIOD
    confidence: float = 1.0
    start_char: Optional[int] = None
    end_char: Optional[int] = None


# ── Domain Dictionaries & Pattern Definitions ────────────────────────────────

_ORGANIZATION_PATTERNS = [
    (r"\b(department\s+of\s+business\s+affairs\s+and\s+consumer\s+protection|bacp)\b", "BACP"),
    (r"\b(chicago\s+department\s+of\s+public\s+health|cdph|health\s+department)\b", "CDPH"),
    (r"\b(department\s+of\s+buildings|dob|building\s+department)\b", "DOB"),
    (r"\b(chicago\s+fire\s+department|cfd|fire\s+prevention\s+bureau)\b", "CFD"),
    (r"\b(chicago\s+police\s+department|cpd)\b", "CPD"),
    (r"\b(department\s+of\s+finance|city\s+clerk|clerk's\s+office)\b", "City Clerk / Finance"),
    (r"\b(small\s+business\s+center|sbc)\b", "Small Business Center"),
    (r"\b(zoning\s+administrator|zoning\s+board|zoning\s+department)\b", "Zoning Department"),
    (r"\b(city\s+of\s+chicago)\b", "City of Chicago"),
]

_LOCATION_PATTERNS = [
    (r"\b(chicago|city\s+of\s+chicago|cook\s+county|illinois|il)\b", "LOCATION"),
    (r"\b(city\s+hall|121\s+n(\.|\s+)?lasalle(\s+st)?(\.|\b)|room\s+800)\b", "LOCATION"),
    (r"\b(downtown|loop|river\s+north|west\s+loop|south\s+side|north\s+side)\b", "LOCATION"),
]

_SERVICE_PATTERNS = [
    (r"\b(retail\s+food\s+establishment|retail\s+food|restaurant\s+license|food\s+license|food\s+business(?:\s+license)?|food\s+establishment|food\s+service|food\s+store)\b", "Retail Food Establishment License"),
    (r"\b(limited\s+business\s+license|lbl|general\s+business\s+license|general\s+business)\b", "Limited Business License"),
    (r"\b(children('s|\s+)?services(\s+facility)?|daycare\s+license|childcare\s+facility)\b", "Children's Services Facility License"),
    (r"\b(public\s+place\s+of\s+amusement|ppa|entertainment\s+license|music\s+venue\s+license)\b", "Public Place of Amusement License"),
    (r"\b(consumption\s+on\s+premises|liquor\s+license|tavern\s+license|bar\s+license|liquor)\b", "Tavern / Consumption on Premises"),
    (r"\b(retail\s+tobacco|tobacco\s+license|vape\s+shop\s+license|smoke\s+shop)\b", "Retail Tobacco"),
    (r"\b(motor\s+vehicle\s+repair|auto\s+repair\s+license|garage\s+license|body\s+shop)\b", "Motor Vehicle Repair"),
    (r"\b(massage\s+establishment|spa\s+license|massage\s+therapy\s+license)\b", "Massage Establishment"),
    (r"\b(mobile\s+food\s+(vendor|dispenser|preparer)|food\s+truck\s+license)\b", "Mobile Food Vendor"),
    (r"\b(shared\s+kitchen(\s+user|\s+supplemental)?|commissary\s+license)\b", "Shared Kitchen"),
    (r"\b(valet\s+parking\s+operator|parking\s+garage\s+license)\b", "Valet Parking Operator"),
    (r"\b(home\s+occupation\s+license|home-based\s+business)\b", "Home Occupation"),
    (r"\b(animal\s+care\s+facility|pet\s+shop\s+license|veterinary\s+hospital)\b", "Animal Care Facility"),
    (r"\b(hotel\s+license|bed\s+and\s+breakfast|vacation\s+rental)\b", "Hotel / Shared Housing"),
    (r"\b(business\s+license|license\s+application|city\s+license)\b", "Business License"),
]

_LICENSE_CODE_PATTERN = re.compile(r"\b(1006|1010|1011|1002|1004|1005|1012|1014|1016|1020|1030|1050|1470|1471|1472|1473|1524|1575|1600|1601|1781|1782|1783|1784|42-5)\b", re.I)

_FEE_PATTERN = re.compile(r"(\$\s*\d{1,4}(?:,\d{3})*(?:\.\d{2})?|\b\d{2,4}\s+dollars?\b|\bfee\b|\bcost\b)", re.I)

_DATE_PERIOD_PATTERN = re.compile(r"\b(\d+\s+(?:years?|months?|days?|weeks?)|biennial|annually|annual|renewal\s+period|expiration\s+date)\b", re.I)


def extract_entities(query: str) -> List[ExtractedEntity]:
    """
    Extracts named domain entities from a natural-language query string.

    Args:
        query: Raw or normalized user query string.

    Returns:
        List of ExtractedEntity instances.
    """
    if not query:
        return []

    entities: List[ExtractedEntity] = []
    seen_spans = set()

    # 1. Extract Services
    for pattern, canonical_name in _SERVICE_PATTERNS:
        for match in re.finditer(pattern, query, re.I):
            span = (match.start(), match.end())
            if span not in seen_spans:
                seen_spans.add(span)
                entities.append(
                    ExtractedEntity(
                        text=match.group(0),
                        label="SERVICE",
                        confidence=0.95,
                        start_char=match.start(),
                        end_char=match.end(),
                    )
                )

    # 2. Extract Organizations / Departments
    for pattern, canonical_name in _ORGANIZATION_PATTERNS:
        for match in re.finditer(pattern, query, re.I):
            span = (match.start(), match.end())
            if span not in seen_spans:
                seen_spans.add(span)
                entities.append(
                    ExtractedEntity(
                        text=match.group(0),
                        label="ORGANIZATION",
                        confidence=0.92,
                        start_char=match.start(),
                        end_char=match.end(),
                    )
                )

    # 3. Extract Locations
    for pattern, _ in _LOCATION_PATTERNS:
        for match in re.finditer(pattern, query, re.I):
            span = (match.start(), match.end())
            if span not in seen_spans:
                seen_spans.add(span)
                entities.append(
                    ExtractedEntity(
                        text=match.group(0),
                        label="LOCATION",
                        confidence=0.90,
                        start_char=match.start(),
                        end_char=match.end(),
                    )
                )

    # 4. Extract License Codes
    for match in _LICENSE_CODE_PATTERN.finditer(query):
        span = (match.start(), match.end())
        if span not in seen_spans:
            seen_spans.add(span)
            entities.append(
                ExtractedEntity(
                    text=match.group(0),
                    label="LICENSE_CODE",
                    confidence=0.98,
                    start_char=match.start(),
                    end_char=match.end(),
                )
            )

    # 5. Extract Fee Amounts
    for match in _FEE_PATTERN.finditer(query):
        span = (match.start(), match.end())
        if span not in seen_spans:
            seen_spans.add(span)
            entities.append(
                ExtractedEntity(
                    text=match.group(0),
                    label="FEE_AMOUNT",
                    confidence=0.88,
                    start_char=match.start(),
                    end_char=match.end(),
                )
            )

    # 6. Extract Dates / Periods
    for match in _DATE_PERIOD_PATTERN.finditer(query):
        span = (match.start(), match.end())
        if span not in seen_spans:
            seen_spans.add(span)
            entities.append(
                ExtractedEntity(
                    text=match.group(0),
                    label="DATE_PERIOD",
                    confidence=0.85,
                    start_char=match.start(),
                    end_char=match.end(),
                )
            )

    # Sort entities by start_char position
    entities.sort(key=lambda e: e.start_char if e.start_char is not None else 0)
    return entities


_PRONOUN_PATTERN = re.compile(
    r"\b(it|this|that|these|those|this license|that license|this business|the license|for it|for this|about it|to apply|apply for it|apply for this|renew it|renew this)\b",
    re.I
)


def extract_primary_service_entity(text: str) -> Tuple[Optional[str], str]:
    """
    Extracts the most prominent service or license identifier from text.
    Returns Tuple of (canonical_entity_name, source_type).
    """
    if not text:
        return None, "none"

    from app.nlp.activity_extractor import extract_business_activity, BusinessActivityType

    # Check license code patterns
    code_match = _LICENSE_CODE_PATTERN.search(text)
    if code_match:
        code = code_match.group(0)
        code_to_name = {
            "1006": "Retail Food Establishment License",
            "1010": "Limited Business License",
            "1011": "Children's Services Facility License",
            "1023": "Children's Services Facility License",
            "1004": "Public Place of Amusement License",
            "1050": "Public Place of Amusement License",
            "1005": "Tavern License",
            "1470": "Tavern License",
            "1002": "Package Goods Liquor License",
            "1474": "Package Goods Liquor License",
            "1625": "Raffles License",
            "4405": "Mobile Food License",
            "1781": "Tobacco License",
        }
        return code_to_name.get(code, f"License Code {code}"), "explicit_current_query"

    # Check explicit service patterns
    for pattern, canonical_name in _SERVICE_PATTERNS:
        if pattern != r"\b(business\s+license|license\s+application|city\s+license)\b":
            if re.search(pattern, text, re.I):
                return canonical_name, "explicit_current_query"

    # Check business activity extraction (structured & domain-aware)
    activity = extract_business_activity(text)
    if activity.suggested_candidate_service:
        return activity.suggested_candidate_service, "inferred_current_query"

    return None, "none"


def resolve_conversation_context(current_query: str, recent_messages: List[Any], is_chronological: bool = False) -> Optional[str]:
    """
    Scans recent conversation history (latest to oldest) to find the primary target license/service entity.
    """
    if not recent_messages:
        return None

    # Scan messages from newest to oldest
    msgs = list(reversed(recent_messages)) if is_chronological else list(recent_messages)
    for msg in msgs:
        content = msg.content if hasattr(msg, "content") else (msg.get("content") if isinstance(msg, dict) else str(msg))
        entity, _ = extract_primary_service_entity(content)
        if entity:
            return entity
    return None


_TOPIC_SWITCH_PATTERN = re.compile(
    r"\b(?:what\s+about|how\s+about|instead\s+of|switch\s+to|what\s+if\s+i\s+start|what\s+if\s+i\s+open|what\s+if\s+i\s+have|for\s+a|for\s+an)\s+(?:a\s+|an\s+)?([a-z0-9_\-\s]+?)(?:\?|$)",
    re.I
)

_DISTINCT_BUSINESS_PATTERN = re.compile(
    r"\b([a-z0-9_\-]+(?:\s+[a-z0-9_\-]+)?)\s+(?:company|business|shop|store|firm|contractor|facility|center|industry)\b",
    re.I
)


def resolve_query_entity(
    current_query: str,
    context_entity: Optional[str] = None,
) -> Tuple[Optional[str], str, bool]:
    """
    Determines the active entity for the current query based on strict priority:
    1. Explicit entity in current query (overrides previous context)
    2. Inferred entity in current query (overrides previous context)
    3. Topic switch / new business subject detection (drops old context)
    4. Pronoun resolution using conversation context
    5. Conversation context follow-up

    Returns:
        Tuple of (resolved_entity, entity_source, context_switched)
    """
    # Priority 1 & 2: Check current query first for known entities
    current_entity, source = extract_primary_service_entity(current_query)
    if current_entity:
        context_switched = bool(context_entity and current_entity != context_entity)
        return current_entity, source, context_switched

    # Priority 3: Check for explicit topic switch or new distinct business activity
    switch_match = _TOPIC_SWITCH_PATTERN.search(current_query)
    if switch_match:
        switched_subject = switch_match.group(1).strip()
        # Clean up filler words
        switched_subject = re.sub(r"\b(instead|now|please)\b", "", switched_subject, flags=re.I).strip()
        pronoun_words = {"it", "this", "that", "these", "those", "this license", "that license", "the license", "this one", "that one", "license", "the business", "this business"}
        if switched_subject and switched_subject.lower() not in pronoun_words:
            return switched_subject, "topic_switch", True

    # Check if a specific business activity was mentioned in the current query that overrides previous context
    from app.nlp.activity_extractor import extract_business_activity, BusinessActivityType
    act = extract_business_activity(current_query)
    if act.activity_type != BusinessActivityType.NONE and act.activity_type != BusinessActivityType.GENERIC_BUSINESS:
        if context_entity:
            is_food_context = any(w in context_entity.lower() for w in ("food", "restaurant", "1006", "tavern", "bar"))
            if act.is_food_related != is_food_context or act.activity_type in (
                BusinessActivityType.SERVICE_TAILORING,
                BusinessActivityType.RETAIL_CLOTHING,
                BusinessActivityType.RETAIL_ELECTRONICS_MOBILE,
                BusinessActivityType.GENERIC_RETAIL,
            ):
                return act.suggested_candidate_service or act.extracted_text, "new_business_subject", True
        elif act.suggested_candidate_service:
            return act.suggested_candidate_service, "inferred_current_query", False

    # Check if a new distinct business type is mentioned (e.g. "construction company")
    biz_match = _DISTINCT_BUSINESS_PATTERN.search(current_query)
    if biz_match:
        new_biz = biz_match.group(0).strip()
        if context_entity and new_biz.lower() not in context_entity.lower():
            return new_biz, "new_business_subject", True

    # Check if query contains an unknown token like "XYZABC123"
    unknown_token_match = re.search(r"\b([a-zA-Z0-9_-]*[0-9]+[a-zA-Z0-9_-]*)\b", current_query)
    if unknown_token_match and unknown_token_match.group(1) not in ("1006", "1010", "1011", "1004", "1005", "1002", "1470", "1781", "4405", "800", "121", "60602", "744", "6060", "2", "1", "3", "4", "5"):
        return unknown_token_match.group(1), "unrecognized_token", True

    # Priority 4 & 5: Check if previous context exists for genuine follow-ups
    if context_entity:
        has_pronoun = bool(_PRONOUN_PATTERN.search(current_query))
        source = "pronoun_resolution" if has_pronoun else "conversation_context"
        return context_entity, source, False

    return None, "none", False




