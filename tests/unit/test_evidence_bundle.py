"""
GovGuide AI — Unit Tests: EvidenceBundle Schema

Tests:
- EvidenceBundle schema serialization and validation
- EvidenceResult fields (chunk_id, service_id, service_code, section, text, score, source_url, source_title)
- Backward compatibility with content/relevance_score
- SourceReference model
"""

import pytest
from app.orchestrator.message_schema import (
    EvidenceBundle,
    EvidenceResult,
    SourceReference,
)


def test_evidence_result_creation_and_alias_sync():
    res = EvidenceResult(
        chunk_id="chk-1006-overview",
        service_id="srv-1006",
        service_code="1006",
        service_name="Retail Food Establishment",
        section="overview",
        text="All restaurants need this license.",
        score=0.85,
        source_id="src-1006",
        source_title="City of Chicago Official Guide: Retail Food",
        source_url="https://www.chicago.gov/RetailFood",
    )

    assert res.chunk_id == "chk-1006-overview"
    assert res.service_code == "1006"
    assert res.text == "All restaurants need this license."
    assert res.content == "All restaurants need this license."  # alias synced
    assert res.score == 0.85
    assert res.relevance_score == 0.85  # alias synced
    assert res.source_url == "https://www.chicago.gov/RetailFood"


def test_evidence_bundle_serialization():
    bundle = EvidenceBundle(
        query="restaurant license",
        intent="service_lookup",
        total_retrieved=1,
        confidence=0.85,
        retrieval_method="hybrid",
        results=[
            EvidenceResult(
                chunk_id="chk-1006-overview",
                source_id="src-1006",
                source_title="Retail Food Guide",
                source_url="https://www.chicago.gov/food",
                text="Overview of retail food",
                score=0.9,
            )
        ],
        sources=[
            SourceReference(
                source_id="src-1006",
                title="Retail Food Guide",
                url="https://www.chicago.gov/food",
                excerpt="Overview of retail food",
            )
        ],
    )

    data = bundle.model_dump()
    assert data["query"] == "restaurant license"
    assert data["intent"] == "service_lookup"
    assert data["total_retrieved"] == 1
    assert data["confidence"] == 0.85
    assert len(data["results"]) == 1
    assert data["results"][0]["chunk_id"] == "chk-1006-overview"
    assert len(data["sources"]) == 1
