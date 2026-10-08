import pytest
from app.nlp.intent_classifier import classify_intent, IntentClassifier
from app.orchestrator.message_schema import Intent, ConfidenceLabel
from app.agents.advisory_agent.intent_formatter import (
    format_intent_response,
    calibrate_confidence_for_intent,
    is_valid_field,
    extract_service_profiles,
)

def test_intent_classification_all_intents():
    classifier = IntentClassifier()

    # 1. Fee queries
    assert classifier.classify("Fees for opening a restaurant in Chicago") == Intent.FEES
    assert classify_intent("How much does a restaurant license cost?") == Intent.FEES
    assert classify_intent("How much do I need to pay?") == Intent.FEES
    assert classify_intent("What are the fees?") == Intent.FEES

    # 2. Document queries
    assert classifier.classify("What documents do I need for a liquor license?") == Intent.REQUIRED_DOCUMENTS
    assert classify_intent("What paperwork is required?") == Intent.REQUIRED_DOCUMENTS
    assert classify_intent("What do I need to bring?") == Intent.REQUIRED_DOCUMENTS

    # 3. Eligibility queries
    assert classifier.classify("Who is eligible for this permit?") == Intent.ELIGIBILITY
    assert classify_intent("Do I qualify for this license?") == Intent.ELIGIBILITY
    assert classify_intent("Who can apply for a business license?") == Intent.ELIGIBILITY

    # 4. Application / Procedure queries
    assert classifier.classify("How do I apply for a retail food license?") == Intent.APPLICATION_PROCEDURE
    assert classify_intent("What are the steps to get licensed?") == Intent.APPLICATION_PROCEDURE
    assert classify_intent("How to get a license in Chicago?") == Intent.APPLICATION_PROCEDURE

    # 5. License Identification queries
    assert classifier.classify("What license do I need for a restaurant?") == Intent.SERVICE_LOOKUP
    assert classify_intent("Which license is required for a clothing shop?") == Intent.SERVICE_LOOKUP

    # 6. Comparison queries
    assert classifier.classify("What is the difference between LBL and Retail Food Establishment License?") == Intent.COMPARISON
    assert classify_intent("Compare Retail Food code 1006 vs code 1005") == Intent.COMPARISON

    # 7. Source / Evidence queries
    assert classifier.classify("What official source supports this?") == Intent.SOURCE_EVIDENCE
    assert classify_intent("Where did this information come from?") == Intent.SOURCE_EVIDENCE


def test_format_fee_response_with_verified_fee():
    evidence = {
        "results": [
            {
                "service_name": "Retail Food Establishment License",
                "service_code": "1006",
                "section": "fees",
                "text": "License Fee Amount: $660.00\nFee Details: $660.00 for two-year license period payable upon application.",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "BACP Retail Food License Guide",
                "source_confidence": "VERIFIED"
            }
        ]
    }
    answer, available, explanation = format_intent_response(
        query="Fees for opening a restaurant in Chicago",
        intent=Intent.FEES,
        evidence_bundle=evidence
    )

    assert available is True
    assert "Retail Food Establishment License" in answer
    assert "1006" in answer
    assert "$660.00" in answer
    assert "Key Application Steps" not in answer
    assert "Eligibility Requirements" not in answer

    score, label = calibrate_confidence_for_intent(Intent.FEES, 0.90, available, True)
    assert label == ConfidenceLabel.HIGH
    assert score >= 0.80


def test_format_fee_response_without_verified_fee():
    evidence = {
        "results": [
            {
                "service_name": "Special Events License",
                "service_code": "7034",
                "section": "overview",
                "text": "Special Events License. Application requires zoning approval. Process takes 2 weeks.\nLicense Fee Amount: NOT_AVAILABLE",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "Special Events Guide",
                "source_confidence": "VERIFIED"
            }
        ]
    }
    answer, available, explanation = format_intent_response(
        query="What is the fee for Special Events License?",
        intent=Intent.FEES,
        evidence_bundle=evidence
    )

    assert available is False
    assert "Special Events License" in answer
    assert "7034" in answer
    assert "available government records do not currently provide a verified fee amount" in answer
    assert "Department of Business Affairs and Consumer Protection (BACP)" in answer

    score, label = calibrate_confidence_for_intent(Intent.FEES, 0.90, available, True)
    assert label == ConfidenceLabel.LOW
    assert score <= 0.35


def test_format_documents_response():
    evidence = {
        "results": [
            {
                "service_name": "Limited Business License",
                "service_code": "1010",
                "section": "required_documents",
                "text": "Required Documentation: Government-issued photo ID | Lease Agreement or Deed | Certificate of Occupancy | Illinois Business Tax (IBT) number.",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "BACP Limited Business License Guide"
            }
        ]
    }
    answer, available, explanation = format_intent_response(
        query="What documents do I need for a Limited Business License?",
        intent=Intent.REQUIRED_DOCUMENTS,
        evidence_bundle=evidence
    )

    assert available is True
    assert "Limited Business License" in answer
    assert "1010" in answer
    assert "Government-issued photo ID" in answer
    assert "Lease Agreement or Deed" in answer
    assert "Key Application Steps" not in answer


def test_format_eligibility_response():
    evidence = {
        "results": [
            {
                "service_name": "Retail Food License",
                "service_code": "1006",
                "section": "eligibility",
                "text": "Eligibility Criteria: Any individual aged 18 or older, or registered Illinois business entity operating within Chicago city limits.",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "BACP Retail Food License Guide"
            }
        ]
    }
    answer, available, explanation = format_intent_response(
        query="Who is eligible for a Retail Food License?",
        intent=Intent.ELIGIBILITY,
        evidence_bundle=evidence
    )

    assert available is True
    assert "Retail Food License" in answer
    assert "aged 18 or older" in answer


def test_format_procedure_response():
    evidence = {
        "results": [
            {
                "service_name": "Retail Food License",
                "service_code": "1006",
                "section": "application_steps",
                "text": "Step-by-Step Procedure: 1. Register with Chicago Business Direct. 2. Submit zoning application. 3. Pass Department of Public Health food inspection.",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "BACP Retail Food License Guide"
            }
        ]
    }
    answer, available, explanation = format_intent_response(
        query="How do I apply for a Retail Food License?",
        intent=Intent.APPLICATION_PROCEDURE,
        evidence_bundle=evidence
    )

    assert available is True
    assert "Retail Food License" in answer
    assert "Chicago Business Direct" in answer
    assert "Pass Department of Public Health food inspection" in answer


def test_format_renewal_response():
    evidence = {
        "results": [
            {
                "service_name": "Retail Food License",
                "service_code": "1006",
                "section": "renewal",
                "text": "License Term Validity: 2 years\nRenewal Period: Biennial (every 2 years)\nRenewal Required: Yes",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "BACP Retail Food Guide"
            }
        ]
    }
    answer, available, explanation = format_intent_response(
        query="How do I renew my business license?",
        intent=Intent.RENEWAL,
        evidence_bundle=evidence
    )

    assert available is True
    assert "2 years" in answer
    assert "Chicago Business Direct" in answer

    # When asking for specific missing deadline
    answer_dl, avail_dl, _ = format_intent_response(
        query="What is the renewal deadline?",
        intent=Intent.RENEWAL,
        evidence_bundle=evidence
    )
    assert avail_dl is False
    assert "do not provide a verified renewal deadline" in answer_dl


def test_format_comparison_response():
    evidence = {
        "results": [
            {
                "service_name": "Limited Business License",
                "service_code": "1010",
                "section": "overview",
                "text": "Overview: Covers general retail and sales of non-food merchandise.\nLicense Fee Amount: $250.00",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "BACP LBL Guide"
            },
            {
                "service_name": "Retail Food Establishment License",
                "service_code": "1006",
                "section": "overview",
                "text": "Overview: Required for selling, preparing, or serving food products to consumers.\nLicense Fee Amount: $660.00",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "BACP Retail Food Guide"
            }
        ]
    }
    answer, available, explanation = format_intent_response(
        query="What is the difference between LBL and Retail Food License?",
        intent=Intent.COMPARISON,
        evidence_bundle=evidence
    )

    assert available is True
    assert "comparison" in answer.lower()
    assert "Limited Business License" in answer
    assert "Retail Food Establishment License" in answer
    assert "|" in answer


def test_format_source_evidence_response():
    evidence = {
        "results": [
            {
                "service_name": "Retail Food Establishment License",
                "service_code": "1006",
                "section": "legal_reference",
                "text": "Legal Reference: Municipal Code of Chicago Title 4, Chapter 4-60.\nResponsible Authority: City of Chicago Department of Business Affairs and Consumer Protection (BACP)",
                "source_url": "https://www.chicago.gov/bacp",
                "source_title": "City of Chicago Municipal Code"
            }
        ]
    }
    answer, available, explanation = format_intent_response(
        query="Where did this information come from?",
        intent=Intent.SOURCE_EVIDENCE,
        evidence_bundle=evidence
    )

    assert available is True
    assert "Department of Business Affairs and Consumer Protection" in answer
    assert "Municipal Code of Chicago" in answer
