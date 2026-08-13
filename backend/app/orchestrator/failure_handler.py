"""GovGuide AI — Failure Handler"""

import structlog
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType, ErrorCode, ErrorPayload
)

logger = structlog.get_logger(__name__)


class FailureHandler:
    """
    Wraps agent calls with error handling.
    Returns a structured error AgentMessage on failure so the orchestrator
    can handle it gracefully without crashing the request pipeline.
    """

    async def call_with_fallback(
        self,
        agent_fn,
        message: AgentMessage,
        agent_id: AgentId,
    ) -> AgentMessage:
        """
        Calls agent_fn(message) and catches any exception.
        Returns the agent's result or a structured error message.
        """
        try:
            result = await agent_fn(message)
            return result
        except Exception as exc:
            logger.error(
                "agent_call_failed",
                agent_id=agent_id,
                request_id=message.request_id,
                error=str(exc),
            )
            return AgentMessage(
                request_id=message.request_id,
                correlation_id=message.correlation_id,
                sender=agent_id,
                recipient=AgentId.ORCHESTRATOR,
                message_type=MessageType.ERROR,
                payload=ErrorPayload(
                    error_code=ErrorCode.RETRIEVAL_FAILED
                    if agent_id == AgentId.RESEARCH_AGENT
                    else ErrorCode.LLM_UNAVAILABLE,
                    error_message=str(exc),
                    recoverable=False,
                ).model_dump(),
            )
