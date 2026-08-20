"""
Unit tests — ServiceController
"""

import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.controllers.service_controller import router
from app.schemas.service_schema import (
    ServiceListResponse,
    CategoryListResponse,
    ServiceSearchResponse,
    GovernmentServiceResponse,
    GovernmentOfficeResponse,
)
from app.database import get_db

app = FastAPI()
app.include_router(router)


async def override_db():
    yield AsyncMock()

app.dependency_overrides[get_db] = override_db

client = TestClient(app)

SAMPLE_SERVICE_ID = uuid.uuid4()
SAMPLE_OFFICE_ID = uuid.uuid4()

sample_office_resp = GovernmentOfficeResponse(
    id=SAMPLE_OFFICE_ID,
    name="City of Chicago — BACP",
    department="Business Affairs and Consumer Protection",
)

sample_service_resp = GovernmentServiceResponse(
    id=SAMPLE_SERVICE_ID,
    service_code="1006",
    name="Apply for a Retail Food Establishment License",
    description="Required for restaurants, cafes, and food vendors in Chicago.",
    category="Food & Beverage",
    is_active=True,
    office=sample_office_resp,
)


def test_list_services_success():
    with patch("app.services.service_service.ServiceService.list_services", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = ServiceListResponse(total=1, items=[sample_service_resp])
        
        response = client.get("/services")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["service_code"] == "1006"
        assert data["items"][0]["name"] == "Apply for a Retail Food Establishment License"
        mock_list.assert_called_once()


def test_list_categories_success():
    with patch("app.services.service_service.ServiceService.list_categories", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = CategoryListResponse(total=2, categories=["Food & Beverage", "Retail"])
        
        response = client.get("/services/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert "Food & Beverage" in data["categories"]
        mock_list.assert_called_once()


def test_search_services_success():
    with patch("app.services.service_service.ServiceService.search_services", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = ServiceSearchResponse(query="food", total=1, items=[sample_service_resp])
        
        response = client.get("/services/search?query=food")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "food"
        assert data["total"] == 1
        assert data["items"][0]["service_code"] == "1006"
        mock_search.assert_called_once()


def test_get_service_success():
    with patch("app.services.service_service.ServiceService.get_service", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_service_resp
        
        response = client.get(f"/services/{SAMPLE_SERVICE_ID}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(SAMPLE_SERVICE_ID)
        assert data["service_code"] == "1006"
        mock_get.assert_called_once()
