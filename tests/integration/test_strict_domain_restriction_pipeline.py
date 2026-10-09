"""
GovGuide AI — Integration Tests: Strict Domain Restriction Multi-Agent Pipeline

Verifies end-to-end behavior of GovGuide AI Orchestrator, Retrieval Agent, and Response Verification Agent:
1. Returns standard out-of-domain refusal in English & Thanglish for unrelated queries.
2. Never attaches citations, never defaults to Code 1010, and sets confidence INSUFFICIENT (0.0).
3. Never reuses active session context for unrelated questions.
4. Preserves valid licensing discovery, procedures, documents, fees, and follow-ups.
5. Handles license-related queries with missing knowledge base evidence as insufficient evidence (not out-of-domain).
"""

import pytest
import uuid
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.message_schema import ConfidenceLabel


@pytest.fixture
def orchestrator():
    return Orchestrator()


# ── 1. End-to-End Unrelated English Questions ─────────────────────────────────
@pytest.mark.asyncio
async def test_unrelated_english_pipeline(orchestrator):
    unrelated_queries = [
        "Who will win the cricket match?",
        "How do I cook biryani?",
        "Tell me a joke.",
        "Which mobile phone is best?",
        "Explain a mathematics problem.",
    ]

    for q in unrelated_queries:
        req_id = str(uuid.uuid4())
        resp = await orchestrator.process_query(query=q, request_id=req_id)

        # 1. Exact refusal text check
        assert "Sorry, GovGuide AI does not provide information on this topic." in resp.answer, f"Failed for '{q}'"
        assert "business licences" in resp.answer

        # 2. Strict confidence and zero citations
        assert resp.confidence_label == ConfidenceLabel.INSUFFICIENT, f"Expected INSUFFICIENT for '{q}'"
        assert resp.confidence_score == 0.0, f"Expected score 0.0 for '{q}'"
        assert len(resp.sources) == 0, f"Expected 0 sources for '{q}', got {len(resp.sources)}"

        # 3. No default to 1010 or any other license code
        assert "1010" not in resp.answer
        assert "Limited Business License" not in resp.answer
        assert "Retail Food" not in resp.answer


# ── 2. End-to-End Unrelated Thanglish Questions ───────────────────────────────
@pytest.mark.asyncio
async def test_unrelated_thanglish_pipeline(orchestrator):
    thanglish_queries = [
        "Cricket eppidi villadurathu?",
        "Biryani eppidi samaikiradhu?",
        "Mobile phone edhu nalladhu?",
        "Oru joke sollu",
    ]

    for q in thanglish_queries:
        req_id = str(uuid.uuid4())
        resp = await orchestrator.process_query(query=q, request_id=req_id)

        # 1. Exact Thanglish refusal text check
        assert "Mannikkavum, indha topic pathina information GovGuide AI system-la available illa." in resp.answer, f"Failed for '{q}'"
        assert "business licences" in resp.answer

        # 2. Strict confidence and zero citations
        assert resp.confidence_label == ConfidenceLabel.INSUFFICIENT, f"Expected INSUFFICIENT for '{q}'"
        assert resp.confidence_score == 0.0, f"Expected score 0.0 for '{q}'"
        assert len(resp.sources) == 0, f"Expected 0 sources for '{q}'"

        # 3. No default to 1010
        assert "1010" not in resp.answer
        assert "Limited Business License" not in resp.answer


# ── 3. Unrelated Question in an Active Multi-Turn Session ─────────────────────
@pytest.mark.asyncio
async def test_unrelated_question_in_active_session_drops_context(orchestrator):
    """
    User first asks about Retail Food (Code 1006), then asks an unrelated question.
    GovGuide must NOT answer about Retail Food or attach Retail Food citations.
    """
    # Turn 1: Valid Retail Food inquiry
    resp1 = await orchestrator.process_query("How do I apply for a retail food establishment license?")
    assert "1006" in resp1.answer or "Retail Food" in resp1.answer
    assert resp1.confidence_label in (ConfidenceLabel.HIGH, ConfidenceLabel.MEDIUM)
    assert len(resp1.sources) > 0

    # Turn 2: Unrelated English question with context_entity="Retail Food Establishment License"
    resp2 = await orchestrator.process_query(
        "Who will win the cricket match?",
        context_entity="Retail Food Establishment License"
    )
    assert "Sorry, GovGuide AI does not provide information on this topic." in resp2.answer
    assert "1006" not in resp2.answer
    assert "Retail Food" not in resp2.answer
    assert resp2.confidence_label == ConfidenceLabel.INSUFFICIENT
    assert resp2.confidence_score == 0.0
    assert len(resp2.sources) == 0

    # Turn 3: Unrelated Thanglish question with context_entity="1006"
    resp3 = await orchestrator.process_query(
        "Cricket eppidi villadurathu?",
        context_entity="1006"
    )
    assert "Mannikkavum, indha topic pathina information GovGuide AI system-la available illa." in resp3.answer
    assert "1006" not in resp3.answer
    assert "Retail Food" not in resp3.answer
    assert resp3.confidence_label == ConfidenceLabel.INSUFFICIENT
    assert resp3.confidence_score == 0.0
    assert len(resp3.sources) == 0


# ── 4. Genuine Follow-up in an Active Multi-Turn Session ──────────────────────
@pytest.mark.asyncio
async def test_genuine_followup_preserves_licensing_flow(orchestrator):
    """
    User asks a valid follow-up about fees or documents.
    GovGuide must preserve context and return the grounded license answer.
    """
    # Follow-up on fees
    resp_fee = await orchestrator.process_query(
        "What about the fees?",
        context_entity="Retail Food Establishment License"
    )
    assert "1006" in resp_fee.answer or "Retail Food" in resp_fee.answer
    assert "660" in resp_fee.answer or "Fee" in resp_fee.answer or "$" in resp_fee.answer
    assert resp_fee.confidence_label in (ConfidenceLabel.HIGH, ConfidenceLabel.MEDIUM)
    assert len(resp_fee.sources) > 0

    # Follow-up on documents
    resp_docs = await orchestrator.process_query(
        "What documents are required?",
        context_entity="Retail Food Establishment License"
    )
    assert "1006" in resp_docs.answer or "Retail Food" in resp_docs.answer
    assert len(resp_docs.sources) > 0


# ── 5. In-Domain Query with Missing Information ──────────────────────────────
@pytest.mark.asyncio
async def test_indomain_missing_information_not_unrelated(orchestrator):
    """
    When a question is license-related but specific information is missing from the dataset,
    it must return an insufficient evidence notice (referring to BACP), NOT classify as an unrelated topic.
    """
    query = "Does the massage establishment license permit operating a commercial helicopter pad at 3 AM?"
    resp = await orchestrator.process_query(query)

    # Must NOT return the generic out-of-domain response
    assert "Sorry, GovGuide AI does not provide information on this topic." not in resp.answer
    # Must return the verified insufficient evidence guidance
    assert "could not find sufficient verified information" in resp.answer.lower() or "bacp" in resp.answer.lower() or "insufficient" in str(resp.confidence_label).lower()
