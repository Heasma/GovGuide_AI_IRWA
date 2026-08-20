"""
GovGuide AI — Unit Tests: Canonical Document Builder

Tests:
- Canonical document generation from service dict/ORM
- 9 standardized section creation
- NOT_AVAILABLE handling for empty/null fields
- Preservation of complete source attribution
"""

import uuid
import pytest
from app.retrieval.document_builder import (
    CanonicalDocument,
    build_service_document,
    build_documents_from_services,
    NOT_AVAILABLE,
)


def _make_mock_service(**overrides):
    base = {
        "id": str(uuid.uuid4()),
        "service_code": "1006",
        "name": "Apply for a Retail Food Establishment License",
        "category": "Food & Beverage",
        "description": "Required for restaurants, bakeries, cafes, and food handling businesses.",
        "source_url": "https://www.chicago.gov/RetailFood",
        "license_term_years": 2,
        "fee_amount": "$660.00",
        "fee_description": "$660 for a 2-year license term.",
        "application_portal_url": "https://www.chicago.gov/BusinessDirect",
        "eligibility_summary": "Any business preparing or serving food on premises in Chicago.",
        "required_documents": "1. Lease/Deed\n2. Health inspection certificate\n3. Food manager certificate",
        "application_steps": "1. Apply online\n2. Schedule CDPH inspection\n3. Pay fee",
        "inspection_required": True,
        "renewal_required": True,
        "renewal_period": "Every 2 years",
        "legal_reference": "MCC Title 4, Chapter 4-8",
        "source_confidence": "VERIFIED",
    }
    base.update(overrides)
    return base


def test_build_service_document_complete():
    """Verify document builder populates all 9 sections from complete service data."""
    svc = _make_mock_service()
    doc = build_service_document(svc)

    assert doc.service_code == "1006"
    assert doc.service_name == "Apply for a Retail Food Establishment License"
    assert doc.category == "Food & Beverage"
    assert doc.source_url == "https://www.chicago.gov/RetailFood"
    assert doc.source_confidence == "VERIFIED"
    assert "src-1006" in doc.source_id

    # Check 9 sections exist
    expected_sections = [
        "overview",
        "eligibility",
        "required_documents",
        "application_procedure",
        "fees",
        "renewal",
        "responsible_office",
        "contact_information",
        "legal_source_information",
    ]
    for sec in expected_sections:
        assert sec in doc.sections, f"Missing section: {sec}"
        assert len(doc.sections[sec]) > 10

    assert "Retail Food Establishment" in doc.sections["overview"]
    assert "$660.00" in doc.sections["fees"]
    assert "Health inspection certificate" in doc.sections["required_documents"]
    assert "MCC Title 4, Chapter 4-8" in doc.sections["legal_source_information"]


def test_build_service_document_not_available_handling():
    """Missing or null fields must be strictly replaced by NOT_AVAILABLE without hallucination."""
    sparse_svc = {
        "id": str(uuid.uuid4()),
        "service_code": "9999",
        "name": "Custom License",
        "category": None,
        "description": "",
        "source_url": None,
        "license_term_years": None,
        "fee_amount": None,
        "fee_description": "",
        "application_portal_url": None,
        "eligibility_summary": None,
        "required_documents": None,
        "application_steps": None,
        "inspection_required": None,
        "renewal_required": None,
        "renewal_period": None,
        "legal_reference": None,
        "source_confidence": None,
    }
    doc = build_service_document(sparse_svc)

    assert doc.service_code == "9999"
    assert doc.category == NOT_AVAILABLE
    assert NOT_AVAILABLE in doc.sections["fees"]
    assert NOT_AVAILABLE in doc.sections["eligibility"]
    assert NOT_AVAILABLE in doc.sections["required_documents"]


def test_build_documents_from_services_batch():
    """Verify batch canonical document builder."""
    services = [_make_mock_service(service_code=f"100{i}") for i in range(5)]
    docs = build_documents_from_services(services)

    assert len(docs) == 5
    codes = [d.service_code for d in docs]
    assert codes == ["1000", "1001", "1002", "1003", "1004"]
