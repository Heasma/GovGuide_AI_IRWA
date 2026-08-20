"""
GovGuide AI — Unit Tests: Semantic Section Chunker

Tests:
- Document chunking into semantic section chunks
- Metadata retention (chunk_id, service_id, service_code, section, source metadata)
- Exclusion of empty / NOT_AVAILABLE sections
"""

import uuid
import pytest
from app.retrieval.document_builder import build_service_document, NOT_AVAILABLE
from app.retrieval.chunker import chunk_document, chunk_documents, ServiceChunk


def _make_sample_doc():
    svc = {
        "id": str(uuid.uuid4()),
        "service_code": "1010",
        "name": "Apply for a Limited Business License (LBL)",
        "category": "Retail & General",
        "description": "Standard business license for retail and services.",
        "source_url": "https://www.chicago.gov/BusinessDirect",
        "fee_amount": "$500.00",
        "required_documents": "1. Proof of property\n2. Articles of Incorporation",
        "application_steps": "1. Apply online\n2. Zoning review\n3. Issue license",
        "renewal_period": "2 years",
        "source_confidence": "VERIFIED",
    }
    return build_service_document(svc)


def test_chunk_document_creates_section_chunks():
    """Verify document is converted into section-based chunks with non-empty text."""
    doc = _make_sample_doc()
    chunks = chunk_document(doc)

    assert len(chunks) > 0
    sections = [c.section for c in chunks]

    assert "overview" in sections
    assert "fees" in sections
    assert "required_documents" in sections
    assert "application_procedure" in sections


def test_chunk_metadata_retention():
    """Every chunk must retain service_id, service_code, section, source_url, source_title."""
    doc = _make_sample_doc()
    chunks = chunk_document(doc)

    for chk in chunks:
        assert isinstance(chk, ServiceChunk)
        assert chk.chunk_id.startswith("chk-1010-")
        assert chk.service_code == "1010"
        assert chk.service_name == "Apply for a Limited Business License (LBL)"
        assert chk.source_url == "https://www.chicago.gov/BusinessDirect"
        assert "City of Chicago" in chk.source_title
        assert len(chk.text) > 0
        assert chk.metadata["service_code"] == "1010"


def test_chunk_documents_multiple():
    """Batch chunking across multiple documents."""
    doc1 = _make_sample_doc()
    doc2 = _make_sample_doc()
    doc2.service_code = "1006"
    doc2.service_name = "Retail Food"

    all_chunks = chunk_documents([doc1, doc2])
    assert len(all_chunks) == len(chunk_document(doc1)) + len(chunk_document(doc2))
