"""
API end-to-end integration checks
"""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport

from app.main import create_app

app = create_app()


@pytest.fixture(autouse=True)
async def dispose_engine():
    yield
    from app.database import engine
    await engine.dispose()


@pytest.mark.anyio
async def test_services_and_query_apis():
    """
    Verify Query API and Services API with live government business-license dataset.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test registration and login to get auth
        unique_id = uuid.uuid4().hex[:8]
        email = f"api_user_{unique_id}@example.com"
        password = "securePassword123!"

        reg_response = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        assert reg_response.status_code == 201
        
        login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Test Query API (mock/stub processing)
        query_payload = {"query": "What services are available?", "session_id": str(uuid.uuid4())}
        response_query = await client.post("/api/v1/query", json=query_payload, headers=headers)
        assert response_query.status_code == 200
        query_data = response_query.json()
        assert "request_id" in query_data
        assert "answer" in query_data
        assert query_data["is_demo"] is True

        # 3. Test Services API endpoints (returning real ingested government dataset)
        # Services list
        response_services = await client.get("/api/v1/services?limit=10")
        assert response_services.status_code == 200
        services_data = response_services.json()
        assert "total" in services_data
        assert services_data["total"] >= 56
        assert len(services_data["items"]) <= 10
        assert len(services_data["items"]) > 0

        first_service = services_data["items"][0]
        first_service_id = first_service["id"]
        assert "service_code" in first_service
        assert "name" in first_service

        # Categories list
        response_categories = await client.get("/api/v1/services/categories")
        assert response_categories.status_code == 200
        categories_data = response_categories.json()
        assert "total" in categories_data
        assert "categories" in categories_data
        assert len(categories_data["categories"]) > 0

        # Services search
        response_search = await client.get("/api/v1/services/search?query=food")
        assert response_search.status_code == 200
        search_data = response_search.json()
        assert search_data["query"] == "food"
        assert search_data["total"] > 0
        assert any("food" in item["name"].lower() or (item["description"] and "food" in item["description"].lower()) for item in search_data["items"])

        # Service detail
        response_detail = await client.get(f"/api/v1/services/{first_service_id}")
        assert response_detail.status_code == 200
        detail_data = response_detail.json()
        assert detail_data["id"] == first_service_id
        assert detail_data["service_code"] == first_service["service_code"]
        assert detail_data["name"] == first_service["name"]
