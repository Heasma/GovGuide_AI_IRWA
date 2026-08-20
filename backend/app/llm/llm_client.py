"""
GovGuide AI — LLM Client (Abstract Base + Stub + Factory)
Adapter pattern for LLM integration. The system is not coupled to any single vendor.
"""

from abc import ABC, abstractmethod
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class BaseLLMClient(ABC):
    """Abstract base for all LLM adapters."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the given prompt."""
        ...


class StubLLMClient(BaseLLMClient):
    """
    Stub LLM client used when no live LLM API is configured.
    Returns a transparent message communicating that LLM is not configured.
    """

    async def generate(self, prompt: str, **kwargs) -> str:
        logger.debug("stub_llm_called", prompt_length=len(prompt))
        return (
            "[LLM_NOT_CONFIGURED] The LLM integration is not yet configured with an active API key. "
            "Evidence retrieval completed successfully."
        )


def get_llm_client() -> BaseLLMClient:
    """
    Factory: returns the appropriate LLM client based on configuration.
    If LLM_API_KEY and LLM_MODEL are configured and LLM_PROVIDER is openai,
    returns OpenAIAdapter. Otherwise, returns StubLLMClient.
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.LLM_API_KEY or not settings.LLM_MODEL:
        logger.info("llm_client_using_stub", reason="LLM_API_KEY or LLM_MODEL not configured")
        return StubLLMClient()

    if settings.LLM_PROVIDER.lower() == "openai":
        try:
            from app.llm.openai_adapter import OpenAIAdapter
            return OpenAIAdapter()
        except Exception as exc:
            logger.error("failed_to_initialize_openai_adapter", error=str(exc))
            return StubLLMClient()

    return StubLLMClient()
