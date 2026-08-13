"""
Unit tests — SessionService
"""

import pytest
import uuid
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.session_service import SessionService
from app.services.exceptions import SessionNotFoundError
from app.models.conversation import QuerySession, ConversationMessage, AuditLog, AgentInteractionLog


@pytest.mark.anyio
async def test_list_sessions_success():
    db = AsyncMock()
    user_id = str(uuid.uuid4())
    
    mock_sessions = [
        QuerySession(id=uuid.uuid4(), user_id=uuid.UUID(user_id), started_at=datetime.now()),
        QuerySession(id=uuid.uuid4(), user_id=uuid.UUID(user_id), started_at=datetime.now()),
    ]
    
    with patch("app.repositories.conversation_repository.ConversationRepository.get_sessions_by_user", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sessions
        
        result = await SessionService.list_sessions(db, user_id)
        
        assert len(result) == 2
        assert result[0]["session_id"] == str(mock_sessions[0].id)
        mock_get.assert_called_once_with(db, uuid.UUID(user_id))


@pytest.mark.anyio
async def test_list_sessions_invalid_uuid():
    db = AsyncMock()
    result = await SessionService.list_sessions(db, "invalid-uuid")
    assert result == []


@pytest.mark.anyio
async def test_get_session_messages_success():
    db = AsyncMock()
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    mock_session = QuerySession(id=uuid.UUID(session_id), user_id=uuid.UUID(user_id))
    mock_messages = [
        ConversationMessage(id=uuid.uuid4(), session_id=uuid.UUID(session_id), role="user", content="hello", created_at=datetime.now()),
        ConversationMessage(id=uuid.uuid4(), session_id=uuid.UUID(session_id), role="assistant", content="hi", created_at=datetime.now()),
    ]
    
    with patch("app.repositories.conversation_repository.ConversationRepository.get_session_by_id_and_user", new_callable=AsyncMock) as mock_get_sess, \
         patch("app.repositories.conversation_repository.ConversationRepository.get_messages_by_session", new_callable=AsyncMock) as mock_get_msgs:
        
        mock_get_sess.return_value = mock_session
        mock_get_msgs.return_value = mock_messages
        
        result = await SessionService.get_session_messages(db, session_id, user_id)
        
        assert len(result) == 2
        assert result[0]["content"] == "hello"
        assert result[1]["role"] == "assistant"
        mock_get_sess.assert_called_once_with(db, uuid.UUID(session_id), uuid.UUID(user_id))
        mock_get_msgs.assert_called_once_with(db, uuid.UUID(session_id))


@pytest.mark.anyio
async def test_get_session_messages_not_found():
    db = AsyncMock()
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    with patch("app.repositories.conversation_repository.ConversationRepository.get_session_by_id_and_user", new_callable=AsyncMock) as mock_get_sess:
        mock_get_sess.return_value = None
        
        with pytest.raises(SessionNotFoundError):
            await SessionService.get_session_messages(db, session_id, user_id)


@pytest.mark.anyio
async def test_delete_session_success():
    db = AsyncMock()
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    mock_session = QuerySession(id=uuid.UUID(session_id), user_id=uuid.UUID(user_id))
    
    with patch("app.repositories.conversation_repository.ConversationRepository.get_session_by_id_and_user", new_callable=AsyncMock) as mock_get_sess, \
         patch("app.repositories.conversation_repository.ConversationRepository.delete_session", new_callable=AsyncMock) as mock_delete:
        
        mock_get_sess.return_value = mock_session
        mock_delete.return_value = None
        
        await SessionService.delete_session(db, session_id, user_id)
        
        mock_get_sess.assert_called_once_with(db, uuid.UUID(session_id), uuid.UUID(user_id))
        mock_delete.assert_called_once_with(db, mock_session)


@pytest.mark.anyio
async def test_delete_session_not_found():
    db = AsyncMock()
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    with patch("app.repositories.conversation_repository.ConversationRepository.get_session_by_id_and_user", new_callable=AsyncMock) as mock_get_sess:
        mock_get_sess.return_value = None
        
        with pytest.raises(SessionNotFoundError):
            await SessionService.delete_session(db, session_id, user_id)


@pytest.mark.anyio
async def test_get_audit_logs():
    db = AsyncMock()
    
    mock_logs = [
        AuditLog(id=uuid.uuid4(), event_type="auth.login", outcome="success", created_at=datetime.now()),
        AuditLog(id=uuid.uuid4(), event_type="query.submitted", outcome="success", created_at=datetime.now()),
    ]
    
    with patch("app.repositories.conversation_repository.ConversationRepository.list_audit_logs", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_logs
        
        result = await SessionService.get_audit_logs(db, skip=0, limit=10, event_type="auth.login")
        
        assert len(result) == 2
        assert result[0]["event_type"] == "auth.login"
        mock_list.assert_called_once_with(db, skip=0, limit=10, event_type="auth.login")


@pytest.mark.anyio
async def test_get_agent_logs():
    db = AsyncMock()
    
    mock_logs = [
        AgentInteractionLog(id=uuid.uuid4(), request_id=uuid.uuid4(), agent_id="research_agent", message_type="task", duration_ms=100, created_at=datetime.now()),
    ]
    
    with patch("app.repositories.conversation_repository.ConversationRepository.list_agent_logs", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_logs
        
        result = await SessionService.get_agent_logs(db, skip=0, limit=10)
        
        assert len(result) == 1
        assert result[0]["agent_id"] == "research_agent"
        mock_list.assert_called_once_with(db, skip=0, limit=10)
