"""
GovGuide AI — LLM Client (Abstract Base + Stub)
Adapter pattern for LLM integration. The system is not coupled to any single vendor.

Phase 1: StubLLMClient returns a structured placeholder response.
Phase 2: Use OpenAIAdapter or LocalLLMAdapter based on LLM_PROVIDER config.
"""

from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger(__name__)


class BaseLLMClient(ABC):
    """Abstract base for all LLM adapters."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response from the given prompt."""
        ...


class StubLLMClient(BaseLLMClient):
    """
    Stub LLM client used in Phase 1.
    Returns a transparent placeholder that clearly communicates
    the system is not yet connected to a real LLM.
    """

    async def generate(self, prompt: str) -> str:
        logger.debug("stub_llm_called", prompt_length=len(prompt))
        return (
            "[PHASE 1 STUB] The LLM integration is not yet configured. "
            "Once the LLM_API_KEY and LLM_MODEL environment variables are set "
            "and the government dataset is integrated, this system will generate "
            "evidence-grounded responses to your query."
        )


def get_llm_client() -> BaseLLMClient:
    """
    Factory: returns the appropriate LLM client based on configuration.
    Phase 1: Always returns StubLLMClient.
    Phase 2: Switch on LLM_PROVIDER env var.
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.LLM_API_KEY or not settings.LLM_MODEL:
        logger.info("llm_client_using_stub", reason="LLM_API_KEY or LLM_MODEL not configured")
        return StubLLMClient()

    # Phase 2: instantiate real adapter
    # if settings.LLM_PROVIDER == "openai":
    #     from app.llm.openai_adapter import OpenAIAdapter
    #     return OpenAIAdapter()
    # elif settings.LLM_PROVIDER == "local":
    #     from app.llm.local_llm_adapter import LocalLLMAdapter
    #     return LocalLLMAdapter()

    return StubLLMClient()
