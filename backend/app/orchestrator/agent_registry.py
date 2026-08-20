"""GovGuide AI — Agent Registry"""

from app.orchestrator.message_schema import AgentId
import structlog

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """
    Maintains a registry of available agent instances.
    In Phase 1, agents are instantiated in-process.
    In Phase 2, this could be extended to support remote agent endpoints.
    """

    def __init__(self):
        self._agents = {}
        self._register_all()

    def _register_all(self):
        from app.agents.research_agent.agent import ResearchAgent
        from app.agents.advisory_agent.agent import AdvisoryAgent

        self._agents[AgentId.RESEARCH_AGENT] = ResearchAgent()
        self._agents[AgentId.ADVISORY_AGENT] = AdvisoryAgent()
        logger.info("agent_registry_initialized", agents=list(self._agents.keys()))

    def get_agent(self, agent_id: AgentId):
        agent = self._agents.get(agent_id)
        if agent is None:
            raise ValueError(f"Agent '{agent_id}' is not registered.")
        return agent

    def register(self, agent, agent_id: AgentId = None):
        aid = agent_id or getattr(agent, "AGENT_ID", None)
        if aid is None:
            raise ValueError("Cannot determine agent_id for registration.")
        self._agents[aid] = agent

    def list_agents(self) -> list:
        return list(self._agents.keys())
