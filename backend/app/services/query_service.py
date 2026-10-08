"""
GovGuide AI — Query Service

Coordinates the AI query processing pipeline, session context tracking,
database-grounded orchestration, and conversation history persistence.
"""

import uuid
import re
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import QuerySession, ConversationMessage
from app.orchestrator.orchestrator import Orchestrator
from app.security.audit_logger import log_query
from app.schemas import QueryResponse

logger = structlog.get_logger(__name__)

# Pronoun / follow-up reference indicators
_FOLLOW_UP_PATTERN = re.compile(
    r"\b(it|this|that|these|those|the fee|how much|cost|price|documents|requirements|where to apply|apply online)\b",
    re.I
)


class QueryService:
    """Coordinates the AI query processing pipeline and orchestrator invocation."""

    @staticmethod
    async def process_query(
        db: AsyncSession,
        query: str,
        session_id: str = None,
        user_id: str = None,
        ip_address: str = "unknown",
    ) -> QueryResponse:
        """
        Coordinates the query workflow:
        - Logs the query event (security audit).
        - Resolves session history for follow-up pronoun/context enrichment.
        - Calls the Agent Orchestrator for database retrieval & grounded generation.
        - Persists user and assistant messages in PostgreSQL.
        - Returns a structured QueryResponse.
        """
        request_id = str(uuid.uuid4())

        # Audit log the query
        log_query(user_id=user_id, request_id=request_id, ip=ip_address)
        logger.info("query_received", request_id=request_id, user_id=user_id, session_id=session_id)

        # ── Step 1: Session & Follow-up Context Resolution ────────────────────
        context_entity = None
        session_uuid = None
        user_uuid = None

        if session_id:
            try:
                session_uuid = uuid.UUID(session_id)
            except (ValueError, TypeError):
                session_uuid = None

        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
            except (ValueError, TypeError):
                user_uuid = None

        # Check for prior session messages to resolve follow-up entity context
        from app.security.prompt_injection_guard import classify_security_query
        from app.orchestrator.message_schema import SecurityClassification

        sec_check = classify_security_query(query)
        if sec_check.classification == SecurityClassification.NORMAL and db and session_uuid:
            try:
                sess_query = await db.execute(select(QuerySession).where(QuerySession.id == session_uuid))
                if hasattr(sess_query, "scalar_one_or_none"):
                    db_session = sess_query.scalar_one_or_none()
                    if not db_session:
                        db_session = QuerySession(
                            id=session_uuid,
                            user_id=user_uuid,
                        )
                        db.add(db_session)
                        if hasattr(db, "flush"):
                            await db.flush()
                    else:
                        msg_query = await db.execute(
                            select(ConversationMessage)
                            .where(ConversationMessage.session_id == session_uuid)
                            .order_by(ConversationMessage.created_at.desc())
                            .limit(6)
                        )
                        if hasattr(msg_query, "scalars"):
                            recent_msgs = list(msg_query.scalars().all())
                            if recent_msgs:
                                from app.nlp.entity_extractor import resolve_conversation_context
                                context_entity = resolve_conversation_context(query, recent_msgs)
                                if context_entity:
                                    logger.info(
                                        "conversation_entity_context_resolved",
                                        query=query,
                                        resolved_entity=context_entity,
                                    )
            except Exception as exc:
                logger.warning("session_context_resolution_failed", error=str(exc))

        # ── Step 2: Orchestration (Database Retrieval + Grounded Answer) ──────
        orchestrator = Orchestrator()
        result = await orchestrator.process_query(
            query=query,
            request_id=request_id,
            session_id=session_id,
            user_id=user_id,
            context_entity=context_entity,
        )


        # ── Step 3: Persist Conversation Messages in Database ────────────────
        if db and session_uuid:
            try:
                user_msg = ConversationMessage(
                    session_id=session_uuid,
                    role="user",
                    content=query,
                )
                assistant_msg = ConversationMessage(
                    session_id=session_uuid,
                    role="assistant",
                    content=result.answer,
                    confidence_score=result.confidence_score,
                    sources=[s.model_dump() for s in result.sources] if result.sources else [],
                    caveats=result.caveats if result.caveats else [],
                )
                if hasattr(db, "add_all"):
                    db.add_all([user_msg, assistant_msg])
                    if hasattr(db, "commit"):
                        await db.commit()
                        logger.info("conversation_messages_persisted", session_id=str(session_uuid))
            except Exception as exc:
                logger.error("failed_to_persist_conversation_messages", error=str(exc))
                if hasattr(db, "rollback"):
                    await db.rollback()

        return result
