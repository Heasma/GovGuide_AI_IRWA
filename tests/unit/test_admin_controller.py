"""
Unit tests — AdminController
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.controllers.admin_controller import router
from app.dependencies import require_admin
from app.database import get_db

app = FastAPI()
app.include_router(router)


async def override_db():
    yield AsyncMock()

app.dependency_overrides[get_db] = override_db


def override_require_admin():
    return {"user_id": "admin-id", "role": "admin"}

app.dependency_overrides[require_admin] = override_require_admin

client = TestClient(app)


def test_list_users():
    with patch("app.services.auth_service.AuthService.list_users", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            {"user_id": "u-1", "email": "admin@ex.com", "role": "admin", "is_active": True, "created_at": "2026-08-12T10:00:00"}
        ]
        
        response = client.get("/admin/users")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["email"] == "admin@ex.com"
        mock_list.assert_called_once()


def test_get_audit_logs():
    with patch("app.services.session_service.SessionService.get_audit_logs", new_callable=AsyncMock) as mock_audit:
        mock_audit.return_value = [
            {"id": "a-1", "event_type": "auth.login", "outcome": "success", "user_id": "u-1", "resource": "/api/v1/auth/login", "created_at": "2026-08-12T10:00:00"}
        ]
        
        response = client.get("/admin/audit-logs?event_type=auth.login")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["event_type"] == "auth.login"
        mock_audit.assert_called_once()


def test_get_agent_logs():
    with patch("app.services.session_service.SessionService.get_agent_logs", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = [
            {"id": "ag-1", "request_id": "r-1", "agent_id": "research_agent", "message_type": "task", "duration_ms": 100, "created_at": "2026-08-12T10:00:00"}
        ]
        
        response = client.get("/admin/agent-logs")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["agent_id"] == "research_agent"
        mock_agent.assert_called_once()
