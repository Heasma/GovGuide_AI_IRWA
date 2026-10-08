"""
GovGuide AI — Integration Tests: Multi-Agent Interaction Pipeline
Tests the complete interaction across:
Agent 1 (Query Understanding) → Agent 2 (Retrieval) → Agent 3 (Response Verification)
"""

import pytest
import psycopg2
from app.config import get_settings
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.agent_registry import AgentRegistry
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    QueryUnderstandingTaskPayload, StructuredQueryPayload,
    RetrievalTaskPayload, RetrievalResultPayload,
    ResponseTaskPayload, ResponseResultPayload,
)

DB_URL = get_settings().DATABASE_SYNC_URL


def _is_db_reachable() -> bool:
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=3)
        conn.close()
        return True
    except Exception:
        return False


db_required = pytest.mark.skipif(
    not _is_db_reachable(),
    reason="PostgreSQL database not reachable",
)


@db_required
class TestMultiAgentInteraction:
    """Integration test suite for the 3 interacting agents."""

    @pytest.mark.anyio
    async def test_sequential_agent_message_flow(self):
        """
        Verify that Agent 1 output is consumed by Agent 2,
        whose output is consumed by Agent 3 to generate a valid response.
        """
        registry = AgentRegistry()
        query_agent = registry.get_agent(AgentId.QUERY_AGENT)
        retrieval_agent = registry.get_agent(AgentId.RETRIEVAL_AGENT)
        response_agent = registry.get_agent(AgentId.RESPONSE_AGENT)

        user_query = "What is the fee and procedure for a Retail Food Establishment license in Chicago?"

        # 1. Agent 1: Query Understanding
        msg_1 = AgentMessage(
            sender=AgentId.ORCHESTRATOR,
            recipient=AgentId.QUERY_AGENT,
            message_type=MessageType.TASK,
            payload=QueryUnderstandingTaskPayload(raw_query=user_query).model_dump(),
        )
        res_1 = await query_agent.process(msg_1)
        assert res_1.message_type == MessageType.RESULT
        structured_query = StructuredQueryPayload(**res_1.payload)
        assert len(structured_query.entities) > 0

        # 2. Agent 2: Retrieval Agent
        msg_2 = AgentMessage(
            sender=AgentId.QUERY_AGENT,
            recipient=AgentId.RETRIEVAL_AGENT,
            message_type=MessageType.TASK,
            payload=RetrievalTaskPayload(structured_query=structured_query).model_dump(),
        )
        res_2 = await retrieval_agent.process(msg_2)
        assert res_2.message_type == MessageType.RESULT
        retrieval_res = RetrievalResultPayload(**res_2.payload)
        assert retrieval_res.sufficient_evidence is True
        assert retrieval_res.evidence_bundle.total_retrieved > 0

        # 3. Agent 3: Response / Verification Agent
        msg_3 = AgentMessage(
            sender=AgentId.RETRIEVAL_AGENT,
            recipient=AgentId.RESPONSE_AGENT,
            message_type=MessageType.TASK,
            payload=ResponseTaskPayload(
                user_query=user_query,
                structured_query=structured_query,
                evidence_bundle=retrieval_res.evidence_bundle,
                retrieval_confidence=retrieval_res.retrieval_confidence,
                sufficient_evidence=retrieval_res.sufficient_evidence,
            ).model_dump(),
        )
        res_3 = await response_agent.process(msg_3)
        assert res_3.message_type == MessageType.RESULT
        resp_payload = ResponseResultPayload(**res_3.payload)
        assert len(resp_payload.answer) > 0
        assert resp_payload.response_validated is True
        assert len(resp_payload.sources) > 0
