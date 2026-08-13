"""
Unit tests — SessionController
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.controllers.session_controller import router
from app.services.exceptions import SessionNotFoundError
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


def test_list_sessions_success():
    with patch("app.services.session_service.SessionService.list_sessions", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            {"session_id": "sess-1", "started_at": "2026-08-12T10:00:00", "message_count": 0}
        ]
        
        response = client.get("/sessions")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["session_id"] == "sess-1"
        mock_list.assert_called_once()


def test_get_session_messages_success():
    with patch("app.services.session_service.SessionService.get_session_messages", new_callable=AsyncMock) as mock_msgs:
        mock_msgs.return_value = [
            {"message_id": "msg-1", "role": "user", "content": "hello", "created_at": "2026-08-12T10:00:00"}
        ]
        
        response = client.get("/sessions/sess-1/messages")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["content"] == "hello"
        mock_msgs.assert_called_once()


def test_get_session_messages_not_found():
    with patch("app.services.session_service.SessionService.get_session_messages", new_callable=AsyncMock) as mock_msgs:
        mock_msgs.side_effect = SessionNotFoundError("Session not found.")
        
        response = client.get("/sessions/sess-1/messages")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_delete_session_success():
    with patch("app.services.session_service.SessionService.delete_session", new_callable=AsyncMock) as mock_del:
        mock_del.return_value = None
        
        response = client.delete("/sessions/sess-1")
        
        assert response.status_code == 200
        assert "deleted" in response.json()["message"]
        mock_del.assert_called_once()


def test_delete_session_not_found():
    with patch("app.services.session_service.SessionService.delete_session", new_callable=AsyncMock) as mock_del:
        mock_del.side_effect = SessionNotFoundError("Session not found.")
        
        response = client.delete("/sessions/sess-1")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
