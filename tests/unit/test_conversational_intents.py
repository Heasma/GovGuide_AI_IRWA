import pytest
from app.nlp.intent_classifier import classify_intent
from app.nlp.entity_extractor import extract_primary_service_entity, resolve_conversation_context
from app.orchestrator.message_schema import Intent, ConfidenceLabel
from app.agents.advisory_agent.intent_formatter import format_intent_response, calibrate_confidence_for_intent

class DummyMessage:
    def __init__(self, content: str, role: str = "user"):
        self.content = content
        self.role = role


def test_test1_fee_query():
    query = "How much does a Limited Business License cost?"
    intent = classify_intent(query)
    assert intent == Intent.FEES

    evidence = {
        "results": [
            {
                "service_name": "Limited Business License (LBL)",
                "service_code": "1010",
                "section": "fees",
                "text": "License Fee Amount: $500 (2-year term)\nFee Details: Flat fee for two-year license. Non-refundable. Effective January 1, 2026.",
                "source_url": "https://www.chicago.gov/BusinessDirect",
                "source_title": "BACP LBL Guide",
            }
        ]
    }
    answer, available, _ = format_intent_response(query, intent, evidence)
    assert available is True
    assert "$500" in answer
    assert "Limited Business License" in answer
    assert "Required Documentation" not in answer


def test_test2_documents_query_not_repeating_fee():
    query = "What documents do I need for a Limited Business License?"
    intent = classify_intent(query)
    assert intent == Intent.REQUIRED_DOCUMENTS

    evidence = {
        "results": [
            {
                "service_name": "Limited Business License (LBL)",
                "service_code": "1010",
                "section": "required_documents",
                "text": "Required Documentation: Government-issued photo ID | Lease Agreement or Deed | Certificate of Occupancy | Illinois Business Tax (IBT) number.",
                "source_url": "https://www.chicago.gov/BusinessDirect",
                "source_title": "BACP LBL Guide",
            }
        ]
    }
    answer, available, _ = format_intent_response(query, intent, evidence)
    assert available is True
    assert "Limited Business License" in answer
    assert "Government-issued photo ID" in answer
    # Must NOT simply repeat fee text
    assert "costs $500" not in answer


def test_test3_eligibility_query():
    query = "Who is eligible for a Limited Business License?"
    intent = classify_intent(query)
    assert intent == Intent.ELIGIBILITY

    evidence = {
        "results": [
            {
                "service_name": "Limited Business License (LBL)",
                "service_code": "1010",
                "section": "eligibility",
                "text": "Eligibility Criteria: Any individual or business entity operating a general retail or commercial service business within Chicago city limits.",
                "source_url": "https://www.chicago.gov/BusinessDirect",
                "source_title": "BACP LBL Guide",
            }
        ]
    }
    answer, available, _ = format_intent_response(query, intent, evidence)
    assert available is True
    assert "Limited Business License" in answer
    assert "operating a general retail" in answer
    assert "Step-by-Step" not in answer


def test_test4_application_procedure_query():
    query = "How do I apply for a Limited Business License?"
    intent = classify_intent(query)
    assert intent in (Intent.APPLICATION_PROCEDURE, Intent.PROCEDURE)

    evidence = {
        "results": [
            {
                "service_name": "Limited Business License (LBL)",
                "service_code": "1010",
                "section": "application_steps",
                "text": "Step-by-Step Procedure: 1. Confirm license applicability. 2. Complete zoning review. 3. Submit application online. 4. Pay fee.",
                "source_url": "https://www.chicago.gov/BusinessDirect",
                "source_title": "BACP LBL Guide",
            }
        ]
    }
    answer, available, _ = format_intent_response(query, intent, evidence)
    assert available is True
    assert "1. Confirm license applicability" in answer
    assert "Chicago Business Direct" in answer
    assert "Unable to connect" not in answer


def test_test5_renewal_query():
    query = "How do I renew my Limited Business License?"
    intent = classify_intent(query)
    assert intent == Intent.RENEWAL

    evidence = {
        "results": [
            {
                "service_name": "Limited Business License (LBL)",
                "service_code": "1010",
                "section": "renewal",
                "text": "License Term Validity: 2 years\nRenewal Period: Every 2 years\nRenewal Required: Yes",
                "source_url": "https://www.chicago.gov/BusinessDirect",
                "source_title": "BACP LBL Guide",
            }
        ]
    }
    answer, available, _ = format_intent_response(query, intent, evidence)
    assert available is True
    assert "2 years" in answer
    assert "Renewal Steps:" in answer


def test_test6_context_followup_fee():
    # Turn 1: "I want to open a restaurant in Chicago. What license do I need?"
    history = [
        DummyMessage("I want to open a restaurant in Chicago. What license do I need?", role="user"),
        DummyMessage("For your business inquiry, you will need a Retail Food Establishment License (Code 1006).", role="assistant"),
    ]
    # Turn 2: "How much does it cost?"
    q2 = "How much does it cost?"
    intent2 = classify_intent(q2)
    assert intent2 == Intent.FEES

    resolved_entity = resolve_conversation_context(q2, history)
    assert "Retail Food" in resolved_entity or "1006" in resolved_entity

    evidence = {
        "results": [
            {
                "service_name": resolved_entity,
                "service_code": "1006",
                "section": "fees",
                "text": "License Fee Amount: $660.00\nFee Details: Tiered by square footage. Two-year license term.",
                "source_url": "https://www.chicago.gov/BusinessDirect",
                "source_title": "BACP Retail Food Guide",
            }
        ]
    }
    answer2, available2, _ = format_intent_response(q2, intent2, evidence)
    assert available2 is True
    assert "$660.00" in answer2


def test_test7_context_followup_documents():
    # Turn 1: "I want to open a restaurant in Chicago. What license do I need?"
    history = [
        DummyMessage("I want to open a restaurant in Chicago. What license do I need?", role="user"),
        DummyMessage("For your business inquiry, you will need a Retail Food Establishment License (Code 1006).", role="assistant"),
    ]
    # Turn 2: "What documents do I need?"
    q2 = "What documents do I need?"
    intent2 = classify_intent(q2)
    assert intent2 == Intent.REQUIRED_DOCUMENTS

    resolved_entity = resolve_conversation_context(q2, history)
    assert "Retail Food" in resolved_entity or "1006" in resolved_entity

    evidence = {
        "results": [
            {
                "service_name": resolved_entity,
                "service_code": "1006",
                "section": "required_documents",
                "text": "Required Documentation: Lease or proof of ownership | Business entity documents | Food Service Manager Certificate.",
                "source_url": "https://www.chicago.gov/BusinessDirect",
                "source_title": "BACP Retail Food Guide",
            }
        ]
    }
    answer2, available2, _ = format_intent_response(q2, intent2, evidence)
    assert available2 is True
    assert "Food Service Manager Certificate" in answer2
    assert "What license do I need" not in answer2


def test_test8_context_switching_fee_to_eligibility():
    # Turn 1: "How much does a Limited Business License cost?"
    history = [
        DummyMessage("How much does a Limited Business License cost?", role="user"),
        DummyMessage("A Limited Business License (Code 1010) costs $500 for a two-year term.", role="assistant"),
    ]
    # Turn 2: "Who is eligible for it?"
    q2 = "Who is eligible for it?"
    intent2 = classify_intent(q2)
    assert intent2 == Intent.ELIGIBILITY

    resolved_entity = resolve_conversation_context(q2, history)
    assert "Limited Business License" in resolved_entity or "1010" in resolved_entity

    evidence = {
        "results": [
            {
                "service_name": resolved_entity,
                "service_code": "1010",
                "section": "eligibility",
                "text": "Eligibility Criteria: General retail or commercial service businesses not requiring specific licensure.",
                "source_url": "https://www.chicago.gov/BusinessDirect",
                "source_title": "BACP LBL Guide",
            }
        ]
    }
    answer2, available2, _ = format_intent_response(q2, intent2, evidence)
    assert available2 is True
    assert "General retail" in answer2
    assert "$500" not in answer2


def test_test9_context_switching_eligibility_to_documents():
    # Turn 1: "How much does a Limited Business License cost?"
    # Turn 2: "Who is eligible for it?"
    history = [
        DummyMessage("How much does a Limited Business License cost?", role="user"),
        DummyMessage("A Limited Business License (Code 1010) costs $500 for a two-year term.", role="assistant"),
        DummyMessage("Who is eligible for it?", role="user"),
        DummyMessage("A Limited Business License is intended for general retail businesses.", role="assistant"),
    ]
    # Turn 3: "What documents do I need?"
    q3 = "What documents do I need?"
    intent3 = classify_intent(q3)
    assert intent3 == Intent.REQUIRED_DOCUMENTS

    resolved_entity = resolve_conversation_context(q3, history)
    assert "Limited Business License" in resolved_entity or "1010" in resolved_entity

    evidence = {
        "results": [
            {
                "service_name": resolved_entity,
                "service_code": "1010",
                "section": "required_documents",
                "text": "Required Documentation: Government-issued photo ID | Lease Agreement | Certificate of Occupancy.",
                "source_url": "https://www.chicago.gov/BusinessDirect",
                "source_title": "BACP LBL Guide",
            }
        ]
    }
    answer3, available3, _ = format_intent_response(q3, intent3, evidence)
    assert available3 is True
    assert "Government-issued photo ID" in answer3
    assert "Certificate of Occupancy" in answer3
