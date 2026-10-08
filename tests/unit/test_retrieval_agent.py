"""
GovGuide AI — Unit Tests: Retrieval Agent (Agent 2)
"""

import pytest
from app.agents.retrieval_agent.agent import RetrievalAgent
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    RetrievalTaskPayload, StructuredQueryPayload,
    EvidenceBundle, EvidenceResult, SourceReference,
)


class MockRetrievalEngine:
    def __init__(self, should_fail: bool = False, total_retrieved: int = 2):
        self.should_fail = should_fail
        self.total_retrieved = total_retrieved

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict = None,
        intent: str = None,
        target_service: str = None,
        **kwargs,
    ) -> EvidenceBundle:
        if self.should_fail:
            raise RuntimeError("Database connection timeout")
        if self.total_retrieved == 0:
            return EvidenceBundle(query=query, total_retrieved=0, results=[])

        return EvidenceBundle(
            query=query,
            total_retrieved=2,
            confidence=0.88,
            results=[
                EvidenceResult(
                    chunk_id="chk-1",
                    source_id="src-1",
                    source_title="Retail Food Establishment License",
                    content="Retail food license is required for all food serving businesses in Chicago.",
                    relevance_score=0.88,
                    service_code="1006",
                    service_name="Retail Food Establishment",
                    source_url="https://www.chicago.gov/BusinessDirect",
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


@pytest.mark.anyio
async def test_retrieval_agent_success():
    engine = MockRetrievalEngine()
    agent = RetrievalAgent(retrieval_engine=engine)

    structured_query = StructuredQueryPayload(
        original_query="How to get a food license?",
        cleaned_query="How to get a food license?",
        expanded_query="How to get a food license? retail food establishment food",
        intent="procedure",
    )

    task = AgentMessage(
        sender=AgentId.QUERY_AGENT,
        recipient=AgentId.RETRIEVAL_AGENT,
        message_type=MessageType.TASK,
        payload=RetrievalTaskPayload(structured_query=structured_query).model_dump(),
    )

    response = await agent.process(task)

    assert response.message_type == MessageType.RESULT
    assert response.sender == AgentId.RETRIEVAL_AGENT
    assert response.payload["sufficient_evidence"] is True
    assert response.payload["retrieval_confidence"] == 0.88
    assert len(response.payload["evidence_bundle"]["results"]) == 1


@pytest.mark.anyio
async def test_retrieval_agent_failure_handling():
    engine = MockRetrievalEngine(should_fail=True)
    agent = RetrievalAgent(retrieval_engine=engine)

    structured_query = StructuredQueryPayload(
        original_query="Test query",
        cleaned_query="Test query",
        expanded_query="Test query",
        intent="general",
    )

    task = AgentMessage(
        sender=AgentId.QUERY_AGENT,
        recipient=AgentId.RETRIEVAL_AGENT,
        message_type=MessageType.TASK,
        payload=RetrievalTaskPayload(structured_query=structured_query).model_dump(),
    )

    response = await agent.process(task)
    assert response.message_type == MessageType.ERROR
    assert response.payload["error_code"] == "RETRIEVAL_FAILED"
