"""
Unit tests — QueryController
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.controllers.query_controller import router
from app.models.responses import QueryResponse
from app.dependencies import get_current_user
from app.database import get_db

app = FastAPI()
app.include_router(router)


async def override_db():
    yield AsyncMock()

app.dependency_overrides[get_db] = override_db


def override_current_user():
    return {"user_id": "test-user-id", "role": "citizen"}

app.dependency_overrides[get_current_user] = override_current_user

client = TestClient(app)


def test_submit_query_success():
    with patch("app.services.query_service.QueryService.process_query", new_callable=AsyncMock) as mock_process:
        mock_response = QueryResponse(
            request_id="req-123",
            answer="Test answer",
            confidence_score=0.9,
            confidence_label="high",
            sources=[],
            caveats=[],
            is_demo=True,
        )
        mock_process.return_value = mock_response
        
        response = client.post("/query", json={"query": "hello", "session_id": "sess-123"})
        
        assert response.status_code == 200
        assert response.json()["answer"] == "Test answer"
        mock_process.assert_called_once()


def test_submit_query_error():
    with patch("app.services.query_service.QueryService.process_query", new_callable=AsyncMock) as mock_process:
        mock_process.side_effect = Exception("System crash")
        
        response = client.post("/query", json={"query": "hello", "session_id": "sess-123"})
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"]


def test_submit_feedback_success():
    response = client.post("/query/req-123/feedback", json={"rating": 1, "comment": "Good"})
    assert response.status_code == 200
    assert "Feedback recorded" in response.json()["message"]
