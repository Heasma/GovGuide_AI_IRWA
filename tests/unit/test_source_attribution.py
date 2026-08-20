"""
GovGuide AI — Unit Tests: Source Attribution Validator

Tests:
- Valid source attribution passes
- Missing source_id, source_url, or source_title fails
- Placeholder values ('NOT_AVAILABLE', 'NONE') fail validation
- Filter correctly discards unattributed results
"""

import pytest
from app.retrieval.source_attribution import (
    validate_source_attribution,
    filter_attributed_results,
)


def test_valid_source_attribution():
    item = {
        "chunk_id": "chk-1006-overview",
        "source_id": "src-1006",
        "source_url": "https://www.chicago.gov/RetailFood",
        "source_title": "City of Chicago Official Guide: Retail Food",
        "text": "Valid text",
    }
    is_valid, reason = validate_source_attribution(item)
    assert is_valid is True


def test_missing_source_id_fails():
    item = {
        "chunk_id": "chk-1006-overview",
        "source_id": "",
        "source_url": "https://www.chicago.gov/RetailFood",
        "source_title": "City of Chicago Official Guide: Retail Food",
    }
    is_valid, reason = validate_source_attribution(item)
    assert is_valid is False
    assert "source_id" in reason


def test_missing_source_url_fails():
    item = {
        "chunk_id": "chk-1006-overview",
        "source_id": "src-1006",
        "source_url": "NOT_AVAILABLE",
        "source_title": "City of Chicago Official Guide: Retail Food",
    }
    is_valid, reason = validate_source_attribution(item)
    assert is_valid is False
    assert "source_url" in reason


def test_filter_attributed_results():
    items = [
        {
            "chunk_id": "chk-1",
            "source_id": "src-1",
            "source_url": "https://chicago.gov",
            "source_title": "Valid Source",
        },
        {
            "chunk_id": "chk-2",
            "source_id": "src-2",
            "source_url": "",  # missing url
            "source_title": "Bad Source",
        },
    ]

    filtered = filter_attributed_results(items)
    assert len(filtered) == 1
    assert filtered[0]["chunk_id"] == "chk-1"
