"""GovGuide AI — Agent Interaction Logger"""

import structlog
from app.orchestrator.message_schema import AgentMessage

logger = structlog.get_logger(__name__)


class InteractionLogger:
    """
    Logs every message exchanged between the orchestrator and agents.
    Phase 1: Writes to structured logs.
    Phase 2: Also persists to agent_interaction_logs table.
    """

    def log(
        self,
        outgoing: AgentMessage,
        incoming: AgentMessage,
        duration_ms: int,
    ) -> None:
        logger.info(
            "agent_interaction",
            request_id=outgoing.request_id,
            correlation_id=outgoing.correlation_id,
            sender=outgoing.sender,
            recipient=outgoing.recipient,
            message_type=outgoing.message_type,
            response_type=incoming.message_type,
            duration_ms=duration_ms,
        )
