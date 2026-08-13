"""
GovGuide AI — Conversation, Audit, and Agent Interaction ORM Models

STABLE TABLES: Core conversation tracking and audit trail.
"""

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID, INET
from sqlalchemy.orm import relationship

from app.models.base import Base, uuid_pk, now


class QuerySession(Base):
    """Tracks a user's conversation session. user_id is nullable for anonymous use."""
    __tablename__ = "query_sessions"

    id = uuid_pk()
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_token = Column(String(255), nullable=True, index=True)
    started_at = now()
    ended_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)

    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "ConversationMessage",
        back_populates="session",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ConversationMessage(Base):
    """Individual message within a query session."""
    __tablename__ = "conversation_messages"

    id = uuid_pk()
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("query_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(
        Enum("user", "assistant", "system", name="message_role_enum"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)
    sources = Column(JSONB, default=list)     # list of source references
    caveats = Column(JSONB, default=list)     # list of caveat strings
    created_at = now()

    session = relationship("QuerySession", back_populates="messages")


class AuditLog(Base):
    """
    Immutable audit trail for security-relevant events.
    Payload is stored as a hash — never log raw sensitive data.
    """
    __tablename__ = "audit_logs"

    id = uuid_pk()
    user_id = Column(UUID(as_uuid=True), nullable=True)   # nullable = anonymous/system
    event_type = Column(String(100), nullable=False, index=True)
    resource = Column(String(200), nullable=True)
    ip_address = Column(INET, nullable=True)
    request_id = Column(UUID(as_uuid=True), nullable=True)
    payload_hash = Column(String(64), nullable=True)       # SHA-256 of request
    outcome = Column(
        Enum("success", "failure", "blocked", name="audit_outcome_enum"),
        nullable=True,
    )
    created_at = now()


class AgentInteractionLog(Base):
    """Records every message exchanged between the orchestrator and agents."""
    __tablename__ = "agent_interaction_logs"

    id = uuid_pk()
    request_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("query_sessions.id"),
        nullable=True,
    )
    agent_id = Column(String(100), nullable=False)
    message_type = Column(String(50), nullable=False)
    sender = Column(String(100), nullable=False)
    recipient = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    created_at = now()


__all__ = ["QuerySession", "ConversationMessage", "AuditLog", "AgentInteractionLog"]
