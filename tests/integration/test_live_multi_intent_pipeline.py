"""
GovGuide AI — Live Multi-Intent Pipeline Integration Tests
Validates multi-intent query handling end-to-end through the live HTTP API endpoint (/api/v1/query).
"""

import pytest
import psycopg2
import uuid
from httpx import AsyncClient, ASGITransport
from app.config import get_settings
from app.main import create_app

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
class TestLiveMultiIntentPipeline:
    """End-to-end integration tests for multi-intent queries using the full HTTP API pipeline."""

    async def _query_api(self, query: str) -> dict:
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            unique_id = uuid.uuid4().hex[:8]
            email = f"multi_intent_{unique_id}@example.com"
            password = "securePassword123!"

            await client.post("/api/v1/auth/register", json={"email": email, "password": password})
            login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
            token = login_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                "/api/v1/query",
                json={"query": query, "session_id": str(uuid.uuid4())},
                headers=headers,
            )
            assert resp.status_code == 200, f"Query failed with status {resp.status_code}: {resp.text}"
            return resp.json()

    @pytest.mark.anyio
    async def test_restaurant_license_fee_documents(self):
        """
        Query: 'I want to open a restaurant. What license do I need, how much does it cost, and what documents are required?'
        Must return:
        1. License (Retail Food Establishment License / Code 1006)
        2. Cost/Fee ($660, $940, etc.)
        3. Required Documents section (grounded documents or explicit unavailability notice)
        Must NOT be fee-only.
        """
        query = "I want to open a restaurant. What license do I need, how much does it cost, and what documents are required?"
        data = await self._query_api(query)
        answer = data["answer"]

        # Assert all 3 parts exist
        assert "Retail Food Establishment License" in answer or "Code 1006" in answer
        assert "660" in answer
        assert "940" in answer
        assert "Required Documents:" in answer or "documents" in answer.lower()

        # Assert not fee-only
        assert "Required Documents" in answer
        assert "Retail Food Establishment" in answer

    @pytest.mark.anyio
    async def test_food_truck_license_fee_renewal(self):
        """
        Query: 'I want to open a food truck. What license do I need, how much does it cost, and does it require renewal?'
        Must return:
        1. Mobile Food License (Code 4405)
        2. Fee amount ($1,000 / $700)
        3. Renewal info (Every 2 years)
        """
        query = "I want to open a food truck. What license do I need, how much does it cost, and does it require renewal?"
        data = await self._query_api(query)
        answer = data["answer"]

        assert "Mobile Food" in answer or "4405" in answer
        assert "1,000" in answer or "700" in answer or "$" in answer
        assert "Renewal" in answer or "renew" in answer.lower() or "2 years" in answer

    @pytest.mark.anyio
    async def test_clothing_shop_license_fee_documents(self):
        """
        Query: 'I want to open a clothing shop. What license do I need, how much does it cost, and what documents are required?'
        Must return:
        1. Limited Business License (Code 1010)
        2. Fee ($500)
        3. Required Documents
        """
        query = "I want to open a clothing shop. What license do I need, how much does it cost, and what documents are required?"
        data = await self._query_api(query)
        answer = data["answer"]

        assert "Limited Business License" in answer or "1010" in answer
        assert "500" in answer
        assert "Required Documents:" in answer or "documents" in answer.lower()

    @pytest.mark.anyio
    async def test_license_and_fee_multi_intent(self):
        """
        Query: 'What license do I need to open a restaurant and how much does it cost?'
        Must return License and Fee, but not claim documents if not asked.
        """
        query = "What license do I need to open a restaurant and how much does it cost?"
        data = await self._query_api(query)
        answer = data["answer"]

        assert "Retail Food Establishment License" in answer or "1006" in answer
        assert "660" in answer

    @pytest.mark.anyio
    async def test_single_intent_fee_only(self):
        """
        Query: 'How much does a Limited Business License cost?'
        Must return fee only, not full multi-intent breakdown with unrequested sections.
        """
        query = "How much does a Limited Business License cost?"
        data = await self._query_api(query)
        answer = data["answer"]

        assert "500" in answer
        assert "Required Documents:" not in answer

    @pytest.mark.anyio
    async def test_single_intent_documents_only(self):
        """
        Query: 'What documents do I need for a Limited Business License?'
        Must return documents only, not fee-first.
        """
        query = "What documents do I need for a Limited Business License?"
        data = await self._query_api(query)
        answer = data["answer"]

        assert "document" in answer.lower()
