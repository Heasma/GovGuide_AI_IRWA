"""Unit tests — Agent message schema (Pydantic models)"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    ResearchTaskPayload, ResearchResultPayload,
    AdvisoryTaskPayload, AdvisoryResultPayload,
    ErrorPayload, ErrorCode,
    EvidenceBundle, NLPAnalysis, Intent, ConfidenceLabel,
)


def test_agent_message_has_auto_generated_ids():
    msg = AgentMessage(
        sender=AgentId.ORCHESTRATOR,
        recipient=AgentId.RESEARCH_AGENT,
        message_type=MessageType.TASK,
        payload={},
    )
    assert msg.request_id != ""
    assert msg.correlation_id != ""
    assert msg.timestamp != ""


def test_research_task_payload_defaults():
    payload = ResearchTaskPayload(user_query="test query")
    assert payload.user_query == "test query"
    assert payload.retrieval_config.mode == "hybrid"
    assert payload.retrieval_config.top_k == 10


def test_evidence_bundle_default_empty():
    bundle = EvidenceBundle()
    assert bundle.total_retrieved == 0
    assert bundle.results == []


def test_advisory_result_insufficient_evidence():
    result = AdvisoryResultPayload(
        answer="Cannot confirm",
        confidence_score=0.0,
        confidence_label=ConfidenceLabel.INSUFFICIENT,
    )
    assert result.confidence_label == ConfidenceLabel.INSUFFICIENT
    assert result.sources == []


def test_error_payload_has_fallback_response():
    error = ErrorPayload(
        error_code=ErrorCode.RETRIEVAL_FAILED,
        error_message="Index not available",
    )
    assert "sufficient official evidence" in error.fallback_response


def test_nlp_analysis_defaults_to_unknown_intent():
    analysis = NLPAnalysis()
    assert analysis.intent == Intent.UNKNOWN
    assert analysis.entities == []


def test_agent_message_serialization():
    msg = AgentMessage(
        sender=AgentId.ORCHESTRATOR,
        recipient=AgentId.RESEARCH_AGENT,
        message_type=MessageType.TASK,
        payload=ResearchTaskPayload(user_query="test").model_dump(),
    )
    data = msg.model_dump()
    assert data["sender"] == "orchestrator"
    assert data["recipient"] == "research_agent"
    assert data["schema_version"] == "1.0"
