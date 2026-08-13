"""
Unit tests — AuthController
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.controllers.auth_controller import router
from app.services.exceptions import (
    DuplicateUserError,
    InvalidCredentialsError,
    InactiveUserError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.dependencies import get_current_user
from app.database import get_db

app = FastAPI()
app.include_router(router)

# Override database dependency
async def override_db():
    yield AsyncMock()

app.dependency_overrides[get_db] = override_db


def override_current_user():
    return {"user_id": "test-user-id", "role": "citizen"}

app.dependency_overrides[get_current_user] = override_current_user

client = TestClient(app)


def test_register_success():
    with patch("app.services.auth_service.AuthService.register", new_callable=AsyncMock) as mock_register:
        mock_register.return_value = {"message": "Account created successfully.", "user_id": "user-123"}
        
        response = client.post("/auth/register", json={"email": "new@ex.com", "password": "securepassword"})
        
        assert response.status_code == 201
        assert response.json()["user_id"] == "user-123"
        mock_register.assert_called_once()


def test_register_conflict():
    with patch("app.services.auth_service.AuthService.register", new_callable=AsyncMock) as mock_register:
        mock_register.side_effect = DuplicateUserError("An account with this email already exists.")
        
        response = client.post("/auth/register", json={"email": "dup@ex.com", "password": "securepassword"})
        
        assert response.status_code == 409
        assert "exists" in response.json()["detail"]


def test_login_success():
    with patch("app.services.auth_service.AuthService.login", new_callable=AsyncMock) as mock_login:
        mock_login.return_value = {
            "access_token": "acc_tok",
            "refresh_token": "ref_tok",
            "token_type": "bearer",
            "expires_in": 3600,
        }
        
        response = client.post("/auth/login", json={"email": "login@ex.com", "password": "password"})
        
        assert response.status_code == 200
        assert response.json()["access_token"] == "acc_tok"


def test_login_unauthorized():
    with patch("app.services.auth_service.AuthService.login", new_callable=AsyncMock) as mock_login:
        mock_login.side_effect = InvalidCredentialsError("Invalid email or password.")
        
        response = client.post("/auth/login", json={"email": "login@ex.com", "password": "password"})
        
        assert response.status_code == 401


def test_login_deactivated():
    with patch("app.services.auth_service.AuthService.login", new_callable=AsyncMock) as mock_login:
        mock_login.side_effect = InactiveUserError("Account is deactivated.")
        
        response = client.post("/auth/login", json={"email": "login@ex.com", "password": "password"})
        
        assert response.status_code == 403


def test_refresh_token_success():
    with patch("app.services.auth_service.AuthService.refresh_token", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = {
            "access_token": "new_acc",
            "refresh_token": "new_ref",
            "token_type": "bearer",
            "expires_in": 3600,
        }
        
        response = client.post("/auth/refresh", json={"refresh_token": "ref_tok"})
        
        assert response.status_code == 200
        assert response.json()["access_token"] == "new_acc"


def test_refresh_token_invalid():
    with patch("app.services.auth_service.AuthService.refresh_token", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.side_effect = InvalidTokenError("Invalid token.")
        
        response = client.post("/auth/refresh", json={"refresh_token": "ref_tok"})
        
        assert response.status_code == 401


def test_get_me_success():
    with patch("app.services.auth_service.AuthService.get_profile", new_callable=AsyncMock) as mock_profile:
        mock_profile.return_value = {
            "user_id": "test-user-id",
            "email": "me@ex.com",
            "role": "citizen",
            "created_at": "2026-08-12T10:00:00",
        }
        
        response = client.get("/auth/me")
        
        assert response.status_code == 200
        assert response.json()["email"] == "me@ex.com"


def test_get_me_not_found():
    with patch("app.services.auth_service.AuthService.get_profile", new_callable=AsyncMock) as mock_profile:
        mock_profile.side_effect = UserNotFoundError("User not found.")
        
        response = client.get("/auth/me")
        
        assert response.status_code == 404


def test_logout_success():
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert "Logged out" in response.json()["message"]
