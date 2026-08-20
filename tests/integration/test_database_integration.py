"""
Integration tests — PostgreSQL Database & MVC Flow
"""

import pytest
import uuid
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure environment variables are loaded
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://govguide:changeme@localhost:5432/govguide_db")
os.environ.setdefault("DATABASE_SYNC_URL", "postgresql://govguide:changeme@localhost:5432/govguide_db")
os.environ.setdefault("JWT_SECRET_KEY", "dev-secret-key-do-not-use-in-production-replace-with-secure-random")

from app.main import create_app
from app.database import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import QuerySession, ConversationMessage

app = create_app()


@pytest.mark.anyio
async def test_database_connection():
    """
    Step 4: Verify connection to the PostgreSQL database.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.anyio
async def test_authentication_and_mvc_flow():
    """
    Step 5 & 6: Verify registration, password hashing, duplicate registration,
    login, JWT generation, and accessing protected endpoints.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_id = uuid.uuid4().hex[:8]
        email = f"user_{unique_id}@example.com"
        password = "securePassword123!"

        # 1. Register user
        reg_payload = {"email": email, "password": password}
        response = await client.post("/api/v1/auth/register", json=reg_payload)
        assert response.status_code == 201
        assert "user_id" in response.json()
        user_id = response.json()["user_id"]

        # Verify user exists in DB and password is not plaintext
        async with AsyncSessionLocal() as session:
            db_user = await UserRepository.get_by_id(session, uuid.UUID(user_id))
            assert db_user is not None
            assert db_user.email == email
            assert db_user.password_hash != password

        # 2. Test duplicate registration
        response_dup = await client.post("/api/v1/auth/register", json=reg_payload)
        assert response_dup.status_code == 409

        # 3. Test invalid credentials login
        login_payload_invalid = {"email": email, "password": "wrongpassword"}
        response_invalid = await client.post("/api/v1/auth/login", json=login_payload_invalid)
        assert response_invalid.status_code == 401

        # 4. Test login and JWT generation
        login_payload = {"email": email, "password": password}
        response_login = await client.post("/api/v1/auth/login", json=login_payload)
        assert response_login.status_code == 200
        token_data = response_login.json()
        assert "access_token" in token_data
        access_token = token_data["access_token"]

        # 5. Access profile (authenticated)
        headers = {"Authorization": f"Bearer {access_token}"}
        response_me = await client.get("/api/v1/auth/me", headers=headers)
        assert response_me.status_code == 200
        assert response_me.json()["email"] == email

        # 6. Access profile (unauthenticated)
        response_unauth = await client.get("/api/v1/auth/me")
        assert response_unauth.status_code == 401


@pytest.mark.anyio
async def test_session_and_logging_flows():
    """
    Step 7 & 9: Verify complete session CRUD flow and logs via PostgreSQL.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_id = uuid.uuid4().hex[:8]
        email = f"session_user_{unique_id}@example.com"
        password = "securePassword123!"

        # Register and login to get auth headers
        reg_response = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        user_id = uuid.UUID(reg_response.json()["user_id"])
        
        login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Seed a session directly in PostgreSQL
        session_id = uuid.uuid4()
        async with AsyncSessionLocal() as session:
            db_session = QuerySession(
                id=session_id,
                user_id=user_id,
                session_token=f"token-{unique_id}",
            )
            session.add(db_session)
            
            # Seed message
            db_msg = ConversationMessage(
                id=uuid.uuid4(),
                session_id=session_id,
                role="user",
                content="Hello assistant",
            )
            session.add(db_msg)
            await session.commit()

        # 1. List user sessions
        response_list = await client.get("/api/v1/sessions", headers=headers)
        assert response_list.status_code == 200
        sessions_list = response_list.json()
        assert len(sessions_list) >= 1
        assert any(s["session_id"] == str(session_id) for s in sessions_list)

        # 2. Retrieve messages
        response_msgs = await client.get(f"/api/v1/sessions/{session_id}/messages", headers=headers)
        assert response_msgs.status_code == 200
        msgs = response_msgs.json()
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Hello assistant"

        # 3. Test unauthorized user access to this session
        # Create another user and login to get their headers
        other_email = f"other_{unique_id}@example.com"
        await client.post("/api/v1/auth/register", json={"email": other_email, "password": password})
        other_login = await client.post("/api/v1/auth/login", json={"email": other_email, "password": password})
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

        response_unauth_msgs = await client.get(f"/api/v1/sessions/{session_id}/messages", headers=other_headers)
        assert response_unauth_msgs.status_code == 404  # Preserves ownership and returns 404

        # 4. Delete session (authorized)
        response_del = await client.delete(f"/api/v1/sessions/{session_id}", headers=headers)
        assert response_del.status_code == 200

        # Verify session is deleted from PostgreSQL
        async with AsyncSessionLocal() as session:
            deleted_session = await ConversationRepository.get_session_by_id_and_user(session, session_id, user_id)
            assert deleted_session is None
