"""
GovGuide AI — Multi-Intent Query Handling Regression Tests

Validates:
1. Test 1: "What license do I need, how much does it cost, and what documents are required?"
   -> LICENSE, FEES, REQUIRED_DOCUMENTS all answered or explicitly unavailable.
2. Test 2: "How much does it cost and how often do I need to renew it?"
   -> FEES and RENEWAL answered.
3. Test 3: "What documents do I need and how do I apply?"
   -> REQUIRED_DOCUMENTS and APPLICATION answered.
4. Test 4: "Can I apply for this license and how much does it cost?"
   -> ELIGIBILITY and FEES answered.
5. Test 5: "I want to open a restaurant. What license do I need?"
   -> LICENSE_IDENTIFICATION / SERVICE_LOOKUP only.
6. Test 6: "How much does it cost?"
   -> FEES only.
7. Test 7: Missing evidence isolation rule (no hallucination of documents, explicit unavailability state).
"""

import pytest
from typing import Dict, Any

from app.nlp.intent_classifier import classify_intent, classify_intents
from app.orchestrator.message_schema import Intent
from app.agents.advisory_agent.intent_formatter import (
    format_intent_response,
    format_multi_intent_response,
)


# ── Fixtures & Evidence Bundles ───────────────────────────────────────────────

@pytest.fixture
def restaurant_evidence_bundle() -> Dict[str, Any]:
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
                    "Fee Details: Biennial licensing fee based on square footage\n"
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
def missing_documents_evidence_bundle() -> Dict[str, Any]:
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
                    "Required Documentation: NOT_AVAILABLE\n"
                    "Eligibility Criteria: Fixed food service establishments in Chicago.\n"
                    "Step-by-step Procedure: 1. Zoning. 2. Apply online.\n"
                    "License Term Validity: 2 years\n"
                    "Renewal Cycle: Biennial"
                ),
            }
        ]
    }


# ── Test 1: License + Fees + Required Documents ───────────────────────────────

def test_multi_intent_1_license_fees_documents(restaurant_evidence_bundle):
    """
    Test 1: What license do I need, how much does it cost, and what documents are required?
    Expected:
    - Intent detection: SERVICE_LOOKUP, FEES, REQUIRED_DOCUMENTS
    - Answered:
      - License identification: Retail Food Establishment License (Code 1006)
      - Fee: $660
      - Required documents: Sanitation Certificate / CDPH consultation / Floor plan / Lease
    """
    query = "I want to open a restaurant. What license do I need, how much does it cost, and what documents are required?"
    intents = classify_intents(query)

    assert Intent.SERVICE_LOOKUP in intents
    assert Intent.FEES in intents
    assert Intent.REQUIRED_DOCUMENTS in intents

    answer, is_avail, expl = format_intent_response(
        query=query,
        intent=intents[0],
        evidence_bundle=restaurant_evidence_bundle,
        intents=intents,
    )

    assert is_avail is True
    # Verify License identification is answered
    assert "Retail Food Establishment" in answer
    assert "1006" in answer

    # Verify Fee is answered
    assert "$660" in answer

    # Verify Documents are answered
    assert "Food Sanitation" in answer or "CDPH" in answer or "Floor plan" in answer or "Lease" in answer


# ── Test 2: Fees + Renewal ───────────────────────────────────────────────────

def test_multi_intent_2_fees_and_renewal(restaurant_evidence_bundle):
    """
    Test 2: How much does it cost and how often do I need to renew it?
    Expected:
    - Intent detection: FEES, RENEWAL
    - Answered:
      - Fees: $660
      - Renewal: 2 years / Biennial renewal
    """
    query = "How much does it cost and how often do I need to renew it?"
    intents = classify_intents(query)

    assert Intent.FEES in intents
    assert Intent.RENEWAL in intents
    assert len(intents) == 2

    answer, is_avail, expl = format_intent_response(
        query=query,
        intent=intents[0],
        evidence_bundle=restaurant_evidence_bundle,
        intents=intents,
    )

    assert is_avail is True
    assert "$660" in answer
    assert "2 years" in answer or "biennial" in answer.lower() or "renewal" in answer.lower()


# ── Test 3: Required Documents + Application Procedure ───────────────────────

def test_multi_intent_3_documents_and_application(restaurant_evidence_bundle):
    """
    Test 3: What documents do I need and how do I apply?
    Expected:
    - Intent detection: REQUIRED_DOCUMENTS, APPLICATION_PROCEDURE
    - Answered:
      - Documents: Sanitation / Floor plan / Lease
      - Application: Step-by-step procedure / Chicago Business Direct
    """
    query = "What documents do I need and how do I apply?"
    intents = classify_intents(query)

    assert Intent.REQUIRED_DOCUMENTS in intents
    assert Intent.APPLICATION_PROCEDURE in intents

    answer, is_avail, expl = format_intent_response(
        query=query,
        intent=intents[0],
        evidence_bundle=restaurant_evidence_bundle,
        intents=intents,
    )

    assert is_avail is True
    assert "Required Documents" in answer
    assert "Application" in answer
    assert "Chicago Business Direct" in answer or "1." in answer


# ── Test 4: Eligibility + Fees ───────────────────────────────────────────────

def test_multi_intent_4_eligibility_and_fees(restaurant_evidence_bundle):
    """
    Test 4: Can I apply for this license and how much does it cost?
    Expected:
    - Intent detection: ELIGIBILITY, FEES
    - Answered:
      - Eligibility: Fixed food service establishments
      - Fees: $660
    """
    query = "Can I apply for this license and how much does it cost?"
    intents = classify_intents(query)

    assert Intent.ELIGIBILITY in intents
    assert Intent.FEES in intents

    answer, is_avail, expl = format_intent_response(
        query=query,
        intent=intents[0],
        evidence_bundle=restaurant_evidence_bundle,
        intents=intents,
    )

    assert is_avail is True
    assert "Eligibility" in answer or "intended for" in answer.lower()
    assert "$660" in answer


# ── Test 5: Single-Intent License Identification Only ─────────────────────────

def test_single_intent_5_license_identification_only(restaurant_evidence_bundle):
    """
    Test 5: I want to open a restaurant. What license do I need?
    Expected:
    - Single intent: SERVICE_LOOKUP only
    - Response contains license identification without dumping full unrelated fee tables
    """
    query = "I want to open a restaurant. What license do I need?"
    intents = classify_intents(query)

    assert intents == [Intent.SERVICE_LOOKUP]
    assert classify_intent(query) == Intent.SERVICE_LOOKUP

    answer, is_avail, expl = format_intent_response(
        query=query,
        intent=intents[0],
        evidence_bundle=restaurant_evidence_bundle,
        intents=intents,
    )

    assert is_avail is True
    assert "Retail Food Establishment" in answer
    assert "1006" in answer
    # Single-intent license lookup does not force full step-by-step procedures
    assert "Step-by-step Procedure" not in answer


# ── Test 6: Single-Intent Fees Only ──────────────────────────────────────────

def test_single_intent_6_fees_only(restaurant_evidence_bundle):
    """
    Test 6: How much does it cost?
    Expected:
    - Single intent: FEES only
    - Response contains fee directly without unrelated document lists
    """
    query = "How much does it cost?"
    intents = classify_intents(query)

    assert intents == [Intent.FEES]
    assert classify_intent(query) == Intent.FEES

    answer, is_avail, expl = format_intent_response(
        query=query,
        intent=intents[0],
        evidence_bundle=restaurant_evidence_bundle,
        intents=intents,
    )

    assert is_avail is True
    assert "$660" in answer
    assert "Required Documents" not in answer


# ── Test 7: Missing Evidence Isolation (No Hallucination) ────────────────────

def test_multi_intent_7_missing_evidence_isolation(missing_documents_evidence_bundle):
    """
    Test 7: Missing evidence handling in multi-intent query.
    When documents are NOT_AVAILABLE in official evidence:
    - Fees must be answered ($660)
    - Documents must explicitly state that the available records do not specify required documents checklist
    - Must NOT invent/hallucinate documents
    """
    query = "What license do I need, how much does it cost, and what documents are required?"
    intents = classify_intents(query)

    answer, is_avail, expl = format_intent_response(
        query=query,
        intent=intents[0],
        evidence_bundle=missing_documents_evidence_bundle,
        intents=intents,
    )

    # Fee answered
    assert "$660" in answer
    # Documents missing statement
    assert "do not specify a verified required documents checklist" in answer
    assert "BACP" in answer
    # Completeness validation flags missing element
    assert is_avail is False
