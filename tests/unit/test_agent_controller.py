"""
GovGuide AI — Unit Tests: Agent Communication Protocol Controller
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.dependencies import get_current_user
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType,
    QueryUnderstandingTaskPayload,
)


def override_user():
    return {"user_id": "test-admin-id", "role": "admin"}


@pytest.mark.anyio
async def test_agent_status_endpoint():
    app = create_app()
    app.dependency_overrides[get_current_user] = override_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "query_agent" in data["registered_agents"]
        assert "retrieval_agent" in data["registered_agents"]
        assert "response_agent" in data["registered_agents"]
        assert "configuration" in data


@pytest.mark.anyio
async def test_query_understanding_endpoint():
    app = create_app()
    app.dependency_overrides[get_current_user] = override_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        message = AgentMessage(
            sender=AgentId.ORCHESTRATOR,
            recipient=AgentId.QUERY_AGENT,
            message_type=MessageType.TASK,
            payload=QueryUnderstandingTaskPayload(
                raw_query="How do I get a limited business license in Chicago?",
            ).model_dump(),
        )
        response = await client.post(
            "/api/v1/agents/query-understanding",
            json=message.model_dump(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sender"] == "query_agent"
        assert data["message_type"] == "result"
        assert data["payload"]["is_safe"] is True
        assert len(data["payload"]["entities"]) > 0


@pytest.mark.anyio
async def test_agent_pipeline_endpoint():
    app = create_app()
    app.dependency_overrides[get_current_user] = override_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agents/pipeline",
            params={"query_text": "What is a Retail Food Establishment License?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["trace"]) == 3
        assert data["trace"][0]["agent"] == "query_understanding_agent"
        assert data["trace"][1]["agent"] == "retrieval_agent"
        assert data["trace"][2]["agent"] == "response_verification_agent"
        assert "final_result" in data
