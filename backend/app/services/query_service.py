"""
GovGuide AI — Query Service
"""

import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestrator.orchestrator import Orchestrator
from app.security.audit_logger import log_query
from app.schemas import QueryResponse

logger = structlog.get_logger(__name__)


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
        - Calls the Agent Orchestrator.
        - Returns a structured QueryResponse.
        """
        request_id = str(uuid.uuid4())

        # Audit log the query
        log_query(user_id=user_id, request_id=request_id, ip=ip_address)
        logger.info("query_received", request_id=request_id, user_id=user_id)

        # AI Orchestration
        orchestrator = Orchestrator()
        result = await orchestrator.process_query(
            query=query,
            request_id=request_id,
            session_id=session_id,
            user_id=user_id,
        )

        return result
