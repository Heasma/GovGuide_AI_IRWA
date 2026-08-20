"""
GovGuide AI — Unit Tests: Advisory Agent

Tests:
- AdvisoryAgent initialization and dependency injection
- Grounded answer processing with mocked LLM
- Insufficient evidence handling when confidence is below threshold
- Insufficient evidence handling when sufficient_evidence is False
- Output message formatting and confidence labeling
"""

import pytest
from unittest.mock import AsyncMock

from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    AdvisoryTaskPayload, ConfidenceLabel,
)
from app.agents.advisory_agent.agent import AdvisoryAgent, INSUFFICIENT_EVIDENCE_RESPONSE
from app.llm.llm_client import BaseLLMClient


class MockLLM(BaseLLMClient):
    def __init__(self, return_text: str = "Mock answer [Source 1]"):
        self.return_text = return_text

    async def generate(self, prompt: str, **kwargs) -> str:
        return self.return_text


@pytest.mark.anyio
async def test_advisory_agent_sufficient_evidence_generates_grounded_answer():
    mock_llm = MockLLM("To open a restaurant you need a Retail Food License [Source 1].")
    agent = AdvisoryAgent(llm_client=mock_llm)

    evidence_bundle = {
        "results": [
            {
                "chunk_id": "chk-1006-overview",
                "source_id": "src-1006",
                "source_title": "Retail Food License Guide",
                "source_url": "https://www.chicago.gov/RetailFood",
                "service_code": "1006",
                "section": "overview",
                "text": "Required for restaurants in Chicago.",
            }
        ]
    }

    task_payload = AdvisoryTaskPayload(
        user_query="What license do I need for a cafe?",
        nlp_analysis={"intent": "service_lookup", "entities": []},
        evidence_bundle=evidence_bundle,
        retrieval_confidence=0.85,
        sufficient_evidence=True,
    )

    msg = AgentMessage(
        sender=AgentId.ORCHESTRATOR,
        recipient=AgentId.ADVISORY_AGENT,
        message_type=MessageType.TASK,
        payload=task_payload.model_dump(),
    )

    response = await agent.process(msg)

    assert response.sender == AgentId.ADVISORY_AGENT
    assert response.recipient == AgentId.ORCHESTRATOR
    assert response.message_type == MessageType.RESULT

    payload = response.payload
    assert payload["response_validated"] is True
    assert "Retail Food License" in payload["answer"]
    assert payload["confidence_label"] == ConfidenceLabel.HIGH.value
    assert len(payload["sources"]) == 1


@pytest.mark.anyio
async def test_advisory_agent_insufficient_evidence_flow():
    agent = AdvisoryAgent(llm_client=MockLLM())

    task_payload = AdvisoryTaskPayload(
        user_query="How do I register a spaceship in Chicago?",
        nlp_analysis={"intent": "unknown", "entities": []},
        evidence_bundle={"results": []},
        retrieval_confidence=0.0,
        sufficient_evidence=False,
    )

    msg = AgentMessage(
        sender=AgentId.ORCHESTRATOR,
        recipient=AgentId.ADVISORY_AGENT,
        message_type=MessageType.TASK,
        payload=task_payload.model_dump(),
    )

    response = await agent.process(msg)
    payload = response.payload

    assert payload["confidence_label"] == ConfidenceLabel.INSUFFICIENT.value
    assert payload["confidence_score"] == 0.0
    assert "sufficient official evidence" in payload["answer"].lower()
    assert len(payload["sources"]) == 0
