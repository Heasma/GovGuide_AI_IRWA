"""
GovGuide AI — Integration Tests: Retrieval Pipeline & ResearchAgent

Tests the end-to-end Information Retrieval pipeline against actual
PostgreSQL GovernmentService records.

Pipeline Flow:
    Query → NLP Preprocessor → BM25 + Semantic → Hybrid RRF → Source Attribution → EvidenceBundle → ResearchAgent
"""

import pytest
import psycopg2
from app.config import get_settings
from app.retrieval.retrieval_service import RetrievalService
from app.agents.research_agent.agent import ResearchAgent
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType, ResearchTaskPayload,
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


@pytest.fixture(scope="module")
def live_retrieval_service():
    """Create a RetrievalService loaded with real PostgreSQL data."""
    service = RetrievalService()
    assert service.is_indexed, "RetrievalService failed to index database chunks."
    assert service.total_chunks > 0, "No chunks loaded from database."
    return service


@db_required
class TestRetrievalPipelineIntegration:
    """Integration tests for the retrieval layer with real PostgreSQL data."""

    def test_corpus_loaded_all_56_services(self, live_retrieval_service):
        """Ensure all 56 services are loaded and chunked (504 section chunks)."""
        assert live_retrieval_service.total_chunks >= 56 * 8

    def test_food_query_retrieval(self, live_retrieval_service):
        """Query for restaurant license must retrieve Retail Food (1006)."""
        bundle = live_retrieval_service.search(
            "What license do I need to open a restaurant or cafe in Chicago?",
            top_k=5,
        )
        assert bundle.total_retrieved > 0
        assert bundle.confidence > 0.0

        top_codes = [r.service_code for r in bundle.results[:3]]
        assert "1006" in top_codes

        # Check source attribution
        for res in bundle.results:
            assert res.source_id != ""
            assert res.source_url.startswith("http")
            assert res.source_title != ""

    def test_lbl_query_retrieval(self, live_retrieval_service):
        """Query for general store license must retrieve Limited Business License (1010)."""
        bundle = live_retrieval_service.search(
            "How do I apply for a Limited Business License LBL?",
            top_k=5,
        )
        assert bundle.total_retrieved > 0
        top_codes = [r.service_code for r in bundle.results[:3]]
        assert "1010" in top_codes

    def test_tobacco_query_retrieval(self, live_retrieval_service):
        """Query for tobacco sales must retrieve Tobacco License (1781)."""
        bundle = live_retrieval_service.search(
            "Where can I apply for a retail tobacco license in Chicago?",
            top_k=5,
        )
        assert bundle.total_retrieved > 0
        top_codes = [r.service_code for r in bundle.results[:3]]
        assert "1781" in top_codes

    def test_exact_license_code_lookup(self, live_retrieval_service):
        """Searching by exact license code '4404' returns Regulated Business."""
        bundle = live_retrieval_service.search("license code 4404", top_k=3)
        assert bundle.total_retrieved > 0
        assert bundle.results[0].service_code == "4404"

    def test_empty_query_returns_empty_bundle(self, live_retrieval_service):
        """Empty query returns 0 results and 0.0 confidence."""
        bundle = live_retrieval_service.search("")
        assert bundle.total_retrieved == 0
        assert bundle.confidence == 0.0
        assert bundle.results == []


@db_required
class TestResearchAgentIntegration:
    """Integration tests for ResearchAgent receiving messages and generating EvidenceBundles."""

    @pytest.mark.anyio
    async def test_research_agent_process_valid_query(self, live_retrieval_service):
        """ResearchAgent must process query, return result message with EvidenceBundle."""
        agent = ResearchAgent()

        task_payload = ResearchTaskPayload(
            user_query="What documents are needed for a Retail Food Establishment License?",
            retrieval_config={"top_k": 5},
        )
        msg = AgentMessage(
            sender=AgentId.ORCHESTRATOR,
            recipient=AgentId.RESEARCH_AGENT,
            message_type=MessageType.TASK,
            payload=task_payload.model_dump(),
        )

        response = await agent.process(msg)

        assert response.sender == AgentId.RESEARCH_AGENT
        assert response.recipient == AgentId.ORCHESTRATOR
        assert response.message_type == MessageType.RESULT

        payload = response.payload
        assert payload["sufficient_evidence"] is True
        assert payload["retrieval_confidence"] >= 0.15
        assert payload["evidence_bundle"]["total_retrieved"] > 0

        # Check evidence results contains 1006
        results = payload["evidence_bundle"]["results"]
        codes = [r["service_code"] for r in results]
        assert "1006" in codes

    @pytest.mark.anyio
    async def test_research_agent_insufficient_evidence_for_gibberish(self):
        """ResearchAgent returns sufficient_evidence=False for empty or out-of-domain queries."""
        agent = ResearchAgent()

        task_payload = ResearchTaskPayload(
            user_query="",
            retrieval_config={"top_k": 5},
        )
        msg = AgentMessage(
            sender=AgentId.ORCHESTRATOR,
            recipient=AgentId.RESEARCH_AGENT,
            message_type=MessageType.TASK,
            payload=task_payload.model_dump(),
        )

        response = await agent.process(msg)
        payload = response.payload
        assert payload["sufficient_evidence"] is False
        assert payload["retrieval_confidence"] == 0.0
