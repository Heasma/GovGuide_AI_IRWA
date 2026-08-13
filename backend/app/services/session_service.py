"""
GovGuide AI — Session Service
"""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_repository import ConversationRepository
from app.services.exceptions import SessionNotFoundError


class SessionService:
    """Coordinates conversation sessions, message history, and logging analytics."""

    @staticmethod
    async def list_sessions(db: AsyncSession, user_id: str) -> list:
        """
        Coordinates listing conversation sessions for a user.
        """
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return []

        sessions = await ConversationRepository.get_sessions_by_user(db, user_uuid)
        return [
            {
                "session_id": str(s.id),
                "started_at": s.started_at,
                "message_count": 0,  # Count query is a Phase 2 requirement
            }
            for s in sessions
        ]

    @staticmethod
    async def get_session_messages(db: AsyncSession, session_id: str, user_id: str) -> list:
        """
        Coordinates retrieving message history for a specific session.
        Validates session ownership.
        """
        try:
            session_uuid = uuid.UUID(session_id)
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise SessionNotFoundError("Session not found.")

        # Validate session ownership
        session = await ConversationRepository.get_session_by_id_and_user(db, session_uuid, user_uuid)
        if not session:
            raise SessionNotFoundError("Session not found.")

        messages = await ConversationRepository.get_messages_by_session(db, session_uuid)
        return [
            {
                "message_id": str(m.id),
                "role": m.role,
                "content": m.content,
                "confidence_score": m.confidence_score,
                "sources": m.sources,
                "created_at": m.created_at,
            }
            for m in messages
        ]

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: str, user_id: str) -> None:
        """
        Coordinates deleting a conversation session.
        Validates session ownership.
        """
        try:
            session_uuid = uuid.UUID(session_id)
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise SessionNotFoundError("Session not found.")

        # Validate session ownership
        session = await ConversationRepository.get_session_by_id_and_user(db, session_uuid, user_uuid)
        if not session:
            raise SessionNotFoundError("Session not found.")

        await ConversationRepository.delete_session(db, session)

    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        event_type: Optional[str] = None,
    ) -> list:
        """
        Coordinates listing security audit logs (Admin only).
        """
        logs = await ConversationRepository.list_audit_logs(db, skip=skip, limit=limit, event_type=event_type)
        return [
            {
                "id": str(l.id),
                "event_type": l.event_type,
                "outcome": l.outcome,
                "user_id": str(l.user_id) if l.user_id else None,
                "resource": l.resource,
                "created_at": l.created_at,
            }
            for l in logs
        ]

    @staticmethod
    async def get_agent_logs(db: AsyncSession, skip: int = 0, limit: int = 100) -> list:
        """
        Coordinates listing agent interaction logs (Admin only).
        """
        logs = await ConversationRepository.list_agent_logs(db, skip=skip, limit=limit)
        return [
            {
                "id": str(l.id),
                "request_id": str(l.request_id),
                "agent_id": l.agent_id,
                "message_type": l.message_type,
                "duration_ms": l.duration_ms,
                "created_at": l.created_at,
            }
            for l in logs
        ]
