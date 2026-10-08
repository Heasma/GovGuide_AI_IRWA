"""
GovGuide AI — Unit Tests: Response / Verification Agent (Agent 3)
"""

import pytest
from app.agents.response_verification_agent.agent import ResponseVerificationAgent
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    ResponseTaskPayload, EvidenceBundle, EvidenceResult, SourceReference,
    ConfidenceLabel,
)
from app.llm.llm_client import BaseLLMClient


class MockLLM(BaseLLMClient):
    def __init__(self, output: str):
        self._output = output

    async def generate(self, prompt: str, **kwargs) -> str:
        return self._output


@pytest.mark.anyio
async def test_response_verification_agent_grounded_answer():
    mock_llm = MockLLM(
        "A Retail Food Establishment License is required in Chicago [Source 1]. "
        "Apply at https://www.chicago.gov/BusinessDirect."
    )
    agent = ResponseVerificationAgent(llm_client=mock_llm)

    bundle = EvidenceBundle(
        query="restaurant license",
        total_retrieved=1,
        confidence=0.85,
        results=[
            EvidenceResult(
                chunk_id="chk-1",
                source_id="src-1",
                source_title="Retail Food Establishment License",
                source_url="https://www.chicago.gov/BusinessDirect",
                content="Retail Food License is required for restaurants in Chicago.",
                relevance_score=0.85,
            )
        ],
        sources=[
            SourceReference(
                source_id="src-1",
                title="Retail Food Establishment License",
                url="https://www.chicago.gov/BusinessDirect",
            )
        ],
    )

    task = AgentMessage(
        sender=AgentId.RETRIEVAL_AGENT,
        recipient=AgentId.RESPONSE_AGENT,
        message_type=MessageType.TASK,
        payload=ResponseTaskPayload(
            user_query="How to get a restaurant license?",
            evidence_bundle=bundle,
            retrieval_confidence=0.85,
            sufficient_evidence=True,
        ).model_dump(),
    )

    response = await agent.process(task)

    assert response.message_type == MessageType.RESULT
    assert response.sender == AgentId.RESPONSE_AGENT
    payload = response.payload
    assert "Retail Food Establishment License" in payload["answer"]
    assert payload["confidence_label"] == ConfidenceLabel.HIGH
    assert payload["response_validated"] is True
    assert len(payload["sources"]) > 0


@pytest.mark.anyio
async def test_response_verification_agent_insufficient_evidence():
    agent = ResponseVerificationAgent()

    bundle = EvidenceBundle(
        query="unsupported query",
        total_retrieved=0,
        confidence=0.0,
        results=[],
    )

    task = AgentMessage(
        sender=AgentId.RETRIEVAL_AGENT,
        recipient=AgentId.RESPONSE_AGENT,
        message_type=MessageType.TASK,
        payload=ResponseTaskPayload(
            user_query="Alien registration",
            evidence_bundle=bundle,
            retrieval_confidence=0.0,
            sufficient_evidence=False,
        ).model_dump(),
    )

    response = await agent.process(task)
    payload = response.payload
    assert payload["confidence_label"] == ConfidenceLabel.INSUFFICIENT
    assert "could not find sufficient" in payload["answer"].lower()
    assert len(payload["sources"]) == 0
