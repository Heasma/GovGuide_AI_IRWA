"""
GovGuide AI — Conversational Regression Tests

Validates:
- Test A: Entity switching (Restaurant -> Clothing shop context switch without leakage)
- Test B: Intent switching (REQUIRED_DOCUMENTS -> FEES -> ELIGIBILITY -> APPLICATION_PROCEDURE -> RENEWAL)
- Test C: Geographic eligibility (Sri Lanka remote applicant -> No hallucination, explicit gap, low confidence)
- Test D: Pronoun resolution ("it", "for it", "this license" follow-up resolution)
- Test E: New explicit entity overrides old context (Clothing shop overrides previous restaurant context)
"""

import pytest
from app.nlp.intent_classifier import classify_intent
from app.nlp.entity_extractor import (
    extract_primary_service_entity,
    resolve_query_entity,
    resolve_conversation_context,
)
from app.orchestrator.message_schema import Intent, ConfidenceLabel
from app.agents.advisory_agent.intent_formatter import format_intent_response, calibrate_confidence_for_intent


# ── Fixtures & Mock Evidence Bundles ──────────────────────────────────────────

@pytest.fixture
def restaurant_evidence_bundle():
    return {
        "results": [
            {
                "service_code": "1006",
                "service_name": "Retail Food Establishment License",
                "category": "Food & Dining",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "City of Chicago Retail Food Guide",
                "source_confidence": "VERIFIED",
                "text": (
                    "Official Fee Amount: $660\n"
                    "Fee Details: Biennial licensing fee\n"
                    "Required Documentation: Lease or deed; Food Sanitation Manager Certificate; CDPH consultation; Floor plan\n"
                    "Eligibility Criteria: Fixed food service establishments operating within the City of Chicago.\n"
                    "Step-by-step Procedure: 1. Zoning review. 2. Health consultation with CDPH. 3. Submit application online. 4. Complete inspection.\n"
                    "License Term Validity: 2 years\n"
                    "Renewal Cycle: Biennial renewal required prior to expiration"
                ),
            }
        ]
    }


@pytest.fixture
def clothing_shop_evidence_bundle():
    return {
        "results": [
            {
                "service_code": "1010",
                "service_name": "Limited Business License",
                "category": "Retail & General",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "City of Chicago Limited Business License Guide",
                "source_confidence": "VERIFIED",
                "text": (
                    "Official Fee Amount: $500\n"
                    "Fee Details: Standard 2-year general retail license\n"
                    "Required Documentation: Lease or proof of ownership; Business entity documents; Federal EIN; Illinois Department of Revenue account\n"
                    "Eligibility Criteria: General retail stores, clothing shops, and boutique merchandise sales.\n"
                    "Step-by-step Procedure: 1. Verify zoning. 2. Register business entity. 3. Apply via Chicago Business Direct. 4. Pay fee.\n"
                    "License Term Validity: 2 years\n"
                    "Renewal Cycle: Biennial renewal prior to expiration"
                ),
            }
        ]
    }


# ── Test A: Entity Switching ──────────────────────────────────────────────────

def test_regression_a_entity_switching(restaurant_evidence_bundle, clothing_shop_evidence_bundle):
    """
    Test A – Entity switching
    Conversation:
    1. "I want to open a restaurant in Chicago. What license do I need?" -> Retail Food Establishment
    2. "How much does it cost?" -> Restaurant fee ($660)
    3. "What documents do I need?" -> Restaurant documents (Sanitation certificate, etc.)
    4. "I want to open a clothing shop instead. What license do I need?" -> Limited Business License
    5. "What documents do I need for it?" -> Limited Business License documents (EIN, etc.)
    6. "How much does it cost?" -> Limited Business License fee ($500)
    """
    # Turn 1: Restaurant inquiry
    q1 = "I want to open a restaurant in Chicago. What license do I need?"
    entity1, source1, switched1 = resolve_query_entity(q1, context_entity=None)
    intent1 = classify_intent(q1)
    assert entity1 == "Retail Food Establishment License"
    assert intent1 == Intent.SERVICE_LOOKUP
    active_entity = entity1

    # Turn 2: Restaurant fee follow-up
    q2 = "How much does it cost?"
    entity2, source2, switched2 = resolve_query_entity(q2, context_entity=active_entity)
    intent2 = classify_intent(q2)
    assert entity2 == "Retail Food Establishment License"
    assert source2 == "pronoun_resolution"
    assert intent2 == Intent.FEES
    ans2, avail2, _ = format_intent_response(q2, intent2, restaurant_evidence_bundle)
    assert "$660" in ans2
    assert "Retail Food Establishment" in ans2
    assert "Limited Business" not in ans2

    # Turn 3: Restaurant documents follow-up
    q3 = "What documents do I need?"
    entity3, source3, switched3 = resolve_query_entity(q3, context_entity=active_entity)
    intent3 = classify_intent(q3)
    assert entity3 == "Retail Food Establishment License"
    assert intent3 == Intent.REQUIRED_DOCUMENTS
    ans3, avail3, _ = format_intent_response(q3, intent3, restaurant_evidence_bundle)
    assert "Sanitation" in ans3 or "CDPH" in ans3 or "Lease" in ans3
    assert "1006" in ans3

    # Turn 4: Context switch to clothing shop
    q4 = "I want to open a clothing shop instead. What license do I need?"
    entity4, source4, switched4 = resolve_query_entity(q4, context_entity=active_entity)
    intent4 = classify_intent(q4)
    assert entity4 == "Limited Business License"
    assert switched4 is True
    assert intent4 == Intent.SERVICE_LOOKUP
    active_entity = entity4  # Updated active entity

    # Turn 5: Clothing shop documents follow-up
    q5 = "What documents do I need for it?"
    entity5, source5, switched5 = resolve_query_entity(q5, context_entity=active_entity)
    intent5 = classify_intent(q5)
    assert entity5 == "Limited Business License"
    assert source5 == "pronoun_resolution"
    assert intent5 == Intent.REQUIRED_DOCUMENTS
    ans5, avail5, _ = format_intent_response(q5, intent5, clothing_shop_evidence_bundle)
    assert "Limited Business License" in ans5
    assert "1010" in ans5
    assert "Federal EIN" in ans5 or "Department of Revenue" in ans5 or "Lease" in ans5
    # Strict check: NO restaurant pollution
    assert "Food Sanitation" not in ans5
    assert "CDPH" not in ans5

    # Turn 6: Clothing shop fee follow-up
    q6 = "How much does it cost?"
    entity6, source6, switched6 = resolve_query_entity(q6, context_entity=active_entity)
    intent6 = classify_intent(q6)
    assert entity6 == "Limited Business License"
    assert intent6 == Intent.FEES
    ans6, avail6, _ = format_intent_response(q6, intent6, clothing_shop_evidence_bundle)
    assert "$500" in ans6
    assert "1010" in ans6
    assert "$660" not in ans6


# ── Test B: Intent Switching ──────────────────────────────────────────────────

def test_regression_b_intent_switching(clothing_shop_evidence_bundle):
    """
    Test B – Intent switching
    Conversation:
    1. "What documents do I need for a Limited Business License?" -> REQUIRED_DOCUMENTS
    2. "How much does it cost?" -> FEES
    3. "Who is eligible?" -> ELIGIBILITY
    4. "How do I apply?" -> APPLICATION_PROCEDURE
    5. "How often do I renew it?" -> RENEWAL
    """
    # Turn 1: REQUIRED_DOCUMENTS
    q1 = "What documents do I need for a Limited Business License?"
    i1 = classify_intent(q1)
    assert i1 == Intent.REQUIRED_DOCUMENTS
    ans1, _, _ = format_intent_response(q1, i1, clothing_shop_evidence_bundle)
    assert "documents" in ans1.lower() or "required" in ans1.lower()

    # Turn 2: FEES
    q2 = "How much does it cost?"
    i2 = classify_intent(q2)
    assert i2 == Intent.FEES
    ans2, _, _ = format_intent_response(q2, i2, clothing_shop_evidence_bundle)
    assert "$500" in ans2

    # Turn 3: ELIGIBILITY
    q3 = "Who is eligible?"
    i3 = classify_intent(q3)
    assert i3 == Intent.ELIGIBILITY
    ans3, _, _ = format_intent_response(q3, i3, clothing_shop_evidence_bundle)
    assert "intended for" in ans3.lower() or "eligible" in ans3.lower() or "retail" in ans3.lower()

    # Turn 4: APPLICATION_PROCEDURE
    q4 = "How do I apply?"
    i4 = classify_intent(q4)
    assert i4 == Intent.APPLICATION_PROCEDURE
    ans4, _, _ = format_intent_response(q4, i4, clothing_shop_evidence_bundle)
    assert "1." in ans4
    assert "Chicago Business Direct" in ans4

    # Turn 5: RENEWAL
    q5 = "How often do I renew it?"
    i5 = classify_intent(q5)
    assert i5 == Intent.RENEWAL
    ans5, _, _ = format_intent_response(q5, i5, clothing_shop_evidence_bundle)
    assert "valid for" in ans5.lower() or "renewal" in ans5.lower()


# ── Test C: Geographic / Applicant Eligibility ────────────────────────────────

def test_regression_c_geographic_eligibility(restaurant_evidence_bundle):
    """
    Test C – Geographic eligibility
    1. "I want to open a restaurant in Chicago. What license do I need?"
    2. "I am currently in Sri Lanka. Can I apply for this license?"
    Expected:
    - Resolve "this license" to Retail Food Establishment License.
    - Detect geographic/applicant eligibility intent.
    - Do not hallucinate remote application eligibility.
    - State information gap and return Low confidence.
    """
    q1 = "I want to open a restaurant in Chicago. What license do I need?"
    e1, _, _ = resolve_query_entity(q1, context_entity=None)
    assert e1 == "Retail Food Establishment License"

    q2 = "I am currently in Sri Lanka. Can I apply for this license?"
    e2, source2, _ = resolve_query_entity(q2, context_entity=e1)
    assert e2 == "Retail Food Establishment License"
    assert source2 == "pronoun_resolution"

    i2 = classify_intent(q2)
    assert i2 == Intent.GEOGRAPHIC_ELIGIBILITY

    ans2, is_avail, expl = format_intent_response(q2, i2, restaurant_evidence_bundle)
    assert not is_avail
    assert "Sri Lanka" in ans2
    assert "do not specify whether an applicant currently residing in Sri Lanka can apply remotely" in ans2
    assert "BACP" in ans2 or "Chicago Business Direct" in ans2

    # Verify confidence calibration returns LOW / False
    score, label = calibrate_confidence_for_intent(i2, retrieval_confidence=0.85, is_target_available=is_avail, is_validated=True)
    assert label == ConfidenceLabel.LOW
    assert score <= 0.35


# ── Test D: Pronoun Resolution ────────────────────────────────────────────────

def test_regression_d_pronoun_resolution():
    """
    Test D – Pronoun resolution
    All follow-ups must resolve "it" to the correct active license.
    """
    active_entity = "Retail Food Establishment License"

    follow_ups = [
        ("How much does it cost?", Intent.FEES),
        ("What documents do I need for it?", Intent.REQUIRED_DOCUMENTS),
        ("Who is eligible for it?", Intent.ELIGIBILITY),
        ("How do I apply for it?", Intent.APPLICATION_PROCEDURE),
        ("Can I apply for this license?", Intent.ELIGIBILITY),
        ("What about this license?", Intent.GENERAL),
    ]

    for query, expected_intent in follow_ups:
        entity, source, switched = resolve_query_entity(query, context_entity=active_entity)
        assert entity == active_entity
        assert source == "pronoun_resolution"
        assert not switched
        assert classify_intent(query) == expected_intent


# ── Test E: New Explicit Entity Overrides Old Context ─────────────────────────

def test_regression_e_explicit_entity_overrides_old_context(clothing_shop_evidence_bundle):
    """
    Test E – New explicit entity overrides old context
    Previous: "What documents are required for a restaurant license?"
    Current: "What license do I need for a clothing shop?" -> overrides previous context
    Then: "What documents do I need for it?" -> must return Limited Business License documents
    """
    old_context = "Retail Food Establishment License"

    # Turn 2: User explicitly mentions clothing shop
    q2 = "What license do I need for a clothing shop?"
    entity2, source2, switched2 = resolve_query_entity(q2, context_entity=old_context)
    assert entity2 == "Limited Business License"
    assert switched2 is True
    assert source2 in ("explicit_current_query", "inferred_current_query")

    # Turn 3: Follow-up resolves to clothing shop
    q3 = "What documents do I need for it?"
    entity3, source3, switched3 = resolve_query_entity(q3, context_entity=entity2)
    assert entity3 == "Limited Business License"
    assert source3 == "pronoun_resolution"
    assert not switched3

    ans3, avail3, _ = format_intent_response(q3, Intent.REQUIRED_DOCUMENTS, clothing_shop_evidence_bundle)
    assert "Limited Business License" in ans3
    assert "1010" in ans3
    assert "Food Sanitation" not in ans3


# ── Conversational & Non-Informational Regression Tests ────────────────────────

def test_conversational_test_1_thank_you():
    """
    Test 1 – Thank You
    Input: "Thank you for your information"
    Expected:
    - CONVERSATIONAL
    - THANKS
    - retrieval_required = false
    - no sources
    - no confidence
    - no generic disclaimer
    """
    q = "Thank you for your information"
    from app.nlp.intent_classifier import classify_intent, classify_conversation_type, is_conversational_query
    from app.agents.advisory_agent.intent_formatter import get_conversational_response

    intent = classify_intent(q)
    assert intent == Intent.CONVERSATIONAL
    assert is_conversational_query(q) is True
    assert classify_conversation_type(q) == "THANKS"

    ans = get_conversational_response(q, "THANKS")
    assert "welcome" in ans.lower()
    assert "Code 1006" not in ans
    assert "Retail Food" not in ans
    assert "Important Information" not in ans
    assert "Official Sources" not in ans


def test_conversational_test_2_you_are_welcome():
    """
    Test 2 – You're Welcome
    Input: "You're welcome!"
    Expected:
    - CONVERSATIONAL
    - ACKNOWLEDGEMENT
    - retrieval_required = false
    - no retrieval
    - no license information
    """
    q = "You're welcome!"
    from app.nlp.intent_classifier import classify_intent, classify_conversation_type, is_conversational_query
    from app.agents.advisory_agent.intent_formatter import get_conversational_response

    intent = classify_intent(q)
    assert intent == Intent.CONVERSATIONAL
    assert is_conversational_query(q) is True
    assert classify_conversation_type(q) == "ACKNOWLEDGEMENT"

    ans = get_conversational_response(q, "ACKNOWLEDGEMENT")
    assert "help" in ans.lower() or "welcome" in ans.lower() or "questions" in ans.lower()
    assert "License" not in ans
    assert "Retail Food" not in ans


def test_conversational_test_3_context_preservation(restaurant_evidence_bundle):
    """
    Test 3 – Context Preservation
    Conversation:
    1. "I want to open a restaurant in Chicago. What license do I need?" -> Retail Food
    2. "Thank you!" -> CONVERSATIONAL
    3. "You're welcome!" -> CONVERSATIONAL
    4. "How much does it cost?" -> FEES (resolves Retail Food Establishment License fee)
    """
    # Turn 1
    q1 = "I want to open a restaurant in Chicago. What license do I need?"
    e1, _, _ = resolve_query_entity(q1, context_entity=None)
    assert e1 == "Retail Food Establishment License"
    active_entity = e1

    # Turn 2: "Thank you!"
    q2 = "Thank you!"
    intent2 = classify_intent(q2)
    assert intent2 == Intent.CONVERSATIONAL
    e2, _, _ = resolve_query_entity(q2, context_entity=active_entity)
    assert e2 == "Retail Food Establishment License"

    # Turn 3: "You're welcome!"
    q3 = "You're welcome!"
    intent3 = classify_intent(q3)
    assert intent3 == Intent.CONVERSATIONAL
    e3, _, _ = resolve_query_entity(q3, context_entity=active_entity)
    assert e3 == "Retail Food Establishment License"

    # Turn 4: "How much does it cost?"
    q4 = "How much does it cost?"
    intent4 = classify_intent(q4)
    assert intent4 == Intent.FEES
    e4, source4, _ = resolve_query_entity(q4, context_entity=active_entity)
    assert e4 == "Retail Food Establishment License"
    assert source4 == "pronoun_resolution"

    ans4, avail4, _ = format_intent_response(q4, intent4, restaurant_evidence_bundle)
    assert "$660" in ans4
    assert "Retail Food Establishment" in ans4


def test_conversational_test_4_mixed_thanks_and_question():
    """
    Test 4 – Mixed Thanks + Question
    Input: "Thanks, how much does it cost?"
    Expected: Intent = FEES (NOT pure THANKS)
    """
    q = "Thanks, how much does it cost?"
    from app.nlp.intent_classifier import classify_intent, is_conversational_query

    assert is_conversational_query(q) is False
    assert classify_intent(q) == Intent.FEES


def test_conversational_test_5_mixed_acknowledgement_and_question():
    """
    Test 5 – Mixed Acknowledgement + Question
    Input: "Okay, what documents do I need?"
    Expected: Intent = REQUIRED_DOCUMENTS
    """
    q = "Okay, what documents do I need?"
    from app.nlp.intent_classifier import classify_intent, is_conversational_query

    assert is_conversational_query(q) is False
    assert classify_intent(q) == Intent.REQUIRED_DOCUMENTS


def test_conversational_test_6_multiple_conversational_turns():
    """
    Test 6 – Multiple Conversational Turns
    Conversation:
    - "Thanks."
    - "You're welcome!"
    - "That's helpful."
    - "Goodbye."
    All must remain conversational and must never trigger government retrieval.
    """
    from app.nlp.intent_classifier import classify_intent, is_conversational_query, classify_conversation_type

    turns = [
        ("Thanks.", "THANKS"),
        ("You're welcome!", "ACKNOWLEDGEMENT"),
        ("That's helpful.", "ACKNOWLEDGEMENT"),
        ("Goodbye.", "GOODBYE"),
    ]

    for q, expected_type in turns:
        assert is_conversational_query(q) is True
        assert classify_intent(q) == Intent.CONVERSATIONAL
        assert classify_conversation_type(q) == expected_type


