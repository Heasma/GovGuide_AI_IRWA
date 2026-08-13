"""
Unit tests — AuthService
"""

import pytest
import uuid
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.auth_service import AuthService
from app.services.exceptions import (
    DuplicateUserError,
    InvalidCredentialsError,
    InactiveUserError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.models.user import User


@pytest.mark.anyio
async def test_register_success():
    db = AsyncMock()
    email = "test@example.com"
    password = "securepassword"
    
    mock_user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed_pw",
        role="public",
        is_active=True,
    )
    
    with patch("app.repositories.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get, \
         patch("app.repositories.user_repository.UserRepository.create", new_callable=AsyncMock) as mock_create, \
         patch("app.services.auth_service.hash_password", return_value="hashed_pw"):
        
        mock_get.return_value = None
        mock_create.return_value = mock_user
        
        result = await AuthService.register(db, email, password)
        
        assert result["message"] == "Account created successfully."
        assert result["user_id"] == str(mock_user.id)
        mock_get.assert_called_once_with(db, email)
        mock_create.assert_called_once_with(db, email=email, password_hash="hashed_pw", role="public")


@pytest.mark.anyio
async def test_register_duplicate_email():
    db = AsyncMock()
    email = "duplicate@example.com"
    password = "securepassword"
    
    mock_user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed_pw",
        role="public",
        is_active=True,
    )
    
    with patch("app.repositories.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        
        with pytest.raises(DuplicateUserError):
            await AuthService.register(db, email, password)


@pytest.mark.anyio
async def test_login_success():
    db = AsyncMock()
    email = "login@example.com"
    password = "correct_password"
    
    mock_user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed_pw",
        role="citizen",
        is_active=True,
    )
    
    with patch("app.repositories.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get, \
         patch("app.services.auth_service.verify_password", return_value=True), \
         patch("app.services.auth_service.create_access_token", return_value="access_tok") as mock_access, \
         patch("app.services.auth_service.create_refresh_token", return_value="refresh_tok") as mock_refresh, \
         patch("app.services.auth_service.log_login"):
        
        mock_get.return_value = mock_user
        
        result = await AuthService.login(db, email, password, "127.0.0.1")
        
        assert result["access_token"] == "access_tok"
        assert result["refresh_token"] == "refresh_tok"
        mock_get.assert_called_once_with(db, email)
        mock_access.assert_called_once_with(subject=str(mock_user.id), role="citizen")
        mock_refresh.assert_called_once_with(subject=str(mock_user.id))


@pytest.mark.anyio
async def test_login_invalid_password():
    db = AsyncMock()
    email = "login@example.com"
    password = "wrong_password"
    
    mock_user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed_pw",
        role="citizen",
        is_active=True,
    )
    
    with patch("app.repositories.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get, \
         patch("app.services.auth_service.verify_password", return_value=False), \
         patch("app.services.auth_service.log_login"):
        
        mock_get.return_value = mock_user
        
        with pytest.raises(InvalidCredentialsError):
            await AuthService.login(db, email, password, "127.0.0.1")


@pytest.mark.anyio
async def test_login_deactivated_user():
    db = AsyncMock()
    email = "login@example.com"
    password = "correct_password"
    
    mock_user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed_pw",
        role="citizen",
        is_active=False,
    )
    
    with patch("app.repositories.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get, \
         patch("app.services.auth_service.verify_password", return_value=True), \
         patch("app.services.auth_service.log_login"):
        
        mock_get.return_value = mock_user
        
        with pytest.raises(InactiveUserError):
            await AuthService.login(db, email, password, "127.0.0.1")


@pytest.mark.anyio
async def test_refresh_token_success():
    db = AsyncMock()
    refresh_token = "valid_refresh_token"
    user_id = str(uuid.uuid4())
    
    mock_user = User(
        id=uuid.UUID(user_id),
        email="test@example.com",
        password_hash="hashed_pw",
        role="citizen",
        is_active=True,
    )
    
    with patch("app.services.auth_service.decode_token") as mock_decode, \
         patch("app.repositories.user_repository.UserRepository.get_by_id", new_callable=AsyncMock) as mock_get_id, \
         patch("app.services.auth_service.create_access_token", return_value="new_access_tok"), \
         patch("app.services.auth_service.create_refresh_token", return_value="new_refresh_tok"):
        
        mock_decode.return_value = {"type": "refresh", "sub": user_id}
        mock_get_id.return_value = mock_user
        
        result = await AuthService.refresh_token(db, refresh_token)
        
        assert result["access_token"] == "new_access_tok"
        assert result["refresh_token"] == "new_refresh_tok"


@pytest.mark.anyio
async def test_refresh_token_invalid_type():
    db = AsyncMock()
    refresh_token = "invalid_token"
    
    with patch("app.services.auth_service.decode_token") as mock_decode:
        mock_decode.return_value = {"type": "access", "sub": str(uuid.uuid4())}
        
        with pytest.raises(InvalidTokenError):
            await AuthService.refresh_token(db, refresh_token)


@pytest.mark.anyio
async def test_get_profile_success():
    db = AsyncMock()
    user_id = str(uuid.uuid4())
    created_at = datetime.now()
    
    mock_user = User(
        id=uuid.UUID(user_id),
        email="test@example.com",
        password_hash="hashed_pw",
        role="admin",
        is_active=True,
        created_at=created_at,
    )
    
    with patch("app.repositories.user_repository.UserRepository.get_by_id", new_callable=AsyncMock) as mock_get_id:
        mock_get_id.return_value = mock_user
        
        profile = await AuthService.get_profile(db, user_id)
        
        assert profile["user_id"] == user_id
        assert profile["email"] == "test@example.com"
        assert profile["role"] == "admin"
        assert profile["created_at"] == created_at


@pytest.mark.anyio
async def test_get_profile_not_found():
    db = AsyncMock()
    user_id = str(uuid.uuid4())
    
    with patch("app.repositories.user_repository.UserRepository.get_by_id", new_callable=AsyncMock) as mock_get_id:
        mock_get_id.return_value = None
        
        with pytest.raises(UserNotFoundError):
            await AuthService.get_profile(db, user_id)


@pytest.mark.anyio
async def test_list_users():
    db = AsyncMock()
    
    user1 = User(id=uuid.uuid4(), email="u1@ex.com", role="public", is_active=True)
    user2 = User(id=uuid.uuid4(), email="u2@ex.com", role="admin", is_active=False)
    
    with patch("app.repositories.user_repository.UserRepository.list_all", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [user1, user2]
        
        result = await AuthService.list_users(db, 0, 50)
        
        assert len(result) == 2
        assert result[0]["email"] == "u1@ex.com"
        assert result[1]["role"] == "admin"
        assert result[1]["is_active"] is False
