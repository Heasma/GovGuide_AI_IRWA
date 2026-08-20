"""
GovGuide AI — Unit Tests: Responsible AI Grounding & Validation

Tests:
- Detection of unverified / hallucinated URLs
- Valid source extraction from EvidenceBundle
- Recognition of insufficient-evidence refusal responses
- Caveat generation
"""

import pytest
from app.responsible_ai.grounding_checker import check_grounding_and_citations
from app.agents.advisory_agent.response_validator import validate_response


def test_grounding_checker_valid_citations():
    evidence = {
        "results": [
            {
                "source_id": "src-1006",
                "source_title": "Retail Food License Guide",
                "source_url": "https://www.chicago.gov/RetailFood",
                "text": "Fee is $660 for two years.",
            }
        ]
    }
    answer = (
        "According to [Source 1], a Retail Food License is required in Chicago. "
        "More details can be found at https://www.chicago.gov/RetailFood."
    )
    result = check_grounding_and_citations(answer, evidence)

    assert result.is_grounded is True
    assert len(result.reasons) == 0
    assert len(result.attributed_sources) == 1
    assert result.attributed_sources[0]["source_id"] == "src-1006"


def test_grounding_checker_catches_hallucinated_external_url():
    evidence = {
        "results": [
            {
                "source_id": "src-1006",
                "source_title": "Retail Food License Guide",
                "source_url": "https://www.chicago.gov/RetailFood",
                "text": "Fee is $660.",
            }
        ]
    }
    answer = "Apply at https://www.fake-chicago-license-scam.com/pay for fast approval."
    result = check_grounding_and_citations(answer, evidence)

    assert result.is_grounded is False
    assert any("fake-chicago-license-scam" in r for r in result.reasons)


def test_response_validator_with_empty_answer():
    res = validate_response("", {"results": [{"source_id": "src-1"}]})
    assert res.passed is False
    assert "empty" in res.explanation.lower()


def test_response_validator_with_empty_evidence():
    res = validate_response("Some answer", {"results": []})
    assert res.passed is False
    assert "No evidence" in res.caveats[0]
