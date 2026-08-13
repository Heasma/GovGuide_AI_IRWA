"""
Unit tests — HealthController
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.controllers.health_controller import router
from app.database import get_db

app = FastAPI()
app.include_router(router)


async def override_db():
    yield AsyncMock()

app.dependency_overrides[get_db] = override_db

client = TestClient(app)


def test_health_check_success():
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    mock_db.execute.return_value = None
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"
    mock_db.execute.assert_called_once()


def test_health_check_degraded():
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    mock_db.execute.side_effect = Exception("Connection lost")
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "unavailable"
    mock_db.execute.assert_called_once()
