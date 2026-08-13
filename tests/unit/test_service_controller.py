"""
Unit tests — ServiceController
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.controllers.service_controller import router
from app.schemas import DatasetPendingResponse
from app.database import get_db

app = FastAPI()
app.include_router(router)


async def override_db():
    yield AsyncMock()

app.dependency_overrides[get_db] = override_db

client = TestClient(app)


def test_list_services_success():
    with patch("app.services.service_service.ServiceService.list_services", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = DatasetPendingResponse(endpoint="http://test/services")
        
        response = client.get("/services")
        
        assert response.status_code == 200
        assert response.json()["status"] == "dataset_pending"
        mock_list.assert_called_once()


def test_list_categories_success():
    with patch("app.services.service_service.ServiceService.list_categories", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = DatasetPendingResponse(endpoint="http://test/services/categories")
        
        response = client.get("/services/categories")
        
        assert response.status_code == 200
        assert response.json()["status"] == "dataset_pending"
        mock_list.assert_called_once()


def test_search_services_success():
    with patch("app.services.service_service.ServiceService.search_services", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = DatasetPendingResponse(endpoint="http://test/services/search")
        
        response = client.get("/services/search?query=test")
        
        assert response.status_code == 200
        assert response.json()["status"] == "dataset_pending"
        mock_search.assert_called_once()


def test_get_service_success():
    with patch("app.services.service_service.ServiceService.get_service", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = DatasetPendingResponse(endpoint="http://test/services/123")
        
        response = client.get("/services/123")
        
        assert response.status_code == 200
        assert response.json()["status"] == "dataset_pending"
        mock_get.assert_called_once()
