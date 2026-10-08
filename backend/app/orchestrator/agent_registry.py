"""
GovGuide AI — Agent Registry
Maintains registry of all intelligent agent instances within the GovGuide AI ecosystem.
"""

import structlog
from app.orchestrator.message_schema import AgentId

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """
    Maintains a registry of available agent instances for dispatching and orchestration.
    """

    def __init__(self):
        self._agents = {}
        self._register_all()

    def _register_all(self):
        from app.agents.query_understanding_agent.agent import QueryUnderstandingAgent
        from app.agents.retrieval_agent.agent import RetrievalAgent
        from app.agents.response_verification_agent.agent import ResponseVerificationAgent
        from app.agents.research_agent.agent import ResearchAgent
        from app.agents.advisory_agent.agent import AdvisoryAgent

        q_agent = QueryUnderstandingAgent()
        r_agent = RetrievalAgent()
        res_agent = ResponseVerificationAgent()
        research_agent = ResearchAgent()
        advisory_agent = AdvisoryAgent()

        # 3 Primary Agents
        self._agents[AgentId.QUERY_AGENT] = q_agent
        self._agents[AgentId.QUERY_UNDERSTANDING_AGENT] = q_agent
        self._agents[AgentId.RETRIEVAL_AGENT] = r_agent
        self._agents[AgentId.RESPONSE_AGENT] = res_agent
        self._agents[AgentId.RESPONSE_VERIFICATION_AGENT] = res_agent

        # Backward compatibility aliases
        self._agents[AgentId.RESEARCH_AGENT] = research_agent
        self._agents[AgentId.ADVISORY_AGENT] = advisory_agent

        logger.info(
            "agent_registry_initialized",
            agents=[a.value if hasattr(a, "value") else str(a) for a in self._agents.keys()],
        )

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

        # Maintain aliases when custom agents (e.g. mocks in tests) are registered
        if aid in (AgentId.ADVISORY_AGENT, AgentId.RESPONSE_AGENT, AgentId.RESPONSE_VERIFICATION_AGENT):
            self._agents[AgentId.ADVISORY_AGENT] = agent
            self._agents[AgentId.RESPONSE_AGENT] = agent
            self._agents[AgentId.RESPONSE_VERIFICATION_AGENT] = agent
        elif aid in (AgentId.QUERY_AGENT, AgentId.QUERY_UNDERSTANDING_AGENT):
            self._agents[AgentId.QUERY_AGENT] = agent
            self._agents[AgentId.QUERY_UNDERSTANDING_AGENT] = agent
        elif aid in (AgentId.RETRIEVAL_AGENT, AgentId.RESEARCH_AGENT):
            self._agents[AgentId.RETRIEVAL_AGENT] = agent
            self._agents[AgentId.RESEARCH_AGENT] = agent

    def list_agents(self) -> list:
        return list(self._agents.keys())
