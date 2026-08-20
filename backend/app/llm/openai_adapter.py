"""
GovGuide AI — OpenAI LLM Adapter

Implements the BaseLLMClient interface using the official OpenAI Async SDK.

Rules:
- Reads configuration from Settings.
- Never hardcodes or logs API keys, headers, or secrets.
- Encapsulates provider-specific exceptions into standard error codes.
"""

from typing import Any, Dict, Optional
import structlog
from openai import AsyncOpenAI, OpenAIError, APITimeoutError, RateLimitError, AuthenticationError

from app.config import get_settings
from app.llm.llm_client import BaseLLMClient

logger = structlog.get_logger(__name__)


class OpenAIAdapter(BaseLLMClient):
    """
    Asynchronous OpenAI adapter implementing grounded text generation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        client: Optional[AsyncOpenAI] = None,
    ):
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self._model = model if model is not None else settings.LLM_MODEL
        self._max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS
        self._temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE

        self._custom_client = client
        if not self._api_key or not self._model:
            logger.warning(
                "openai_adapter_unconfigured",
                has_api_key=bool(self._api_key),
                has_model=bool(self._model),
            )
        logger.info(
            "openai_adapter_initialized",
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text response from OpenAI model.
        """
        if not self._api_key or not self._model:
            logger.warning("openai_call_skipped_not_configured")
            return (
                "[LLM_NOT_CONFIGURED] The LLM integration is not configured with an active API key or model. "
                "The system operated in retrieval-only mode."
            )

        model = kwargs.get("model", self._model)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        temperature = kwargs.get("temperature", self._temperature)

        client = self._custom_client
        should_close = False
        if not client:
            client = AsyncOpenAI(api_key=self._api_key)
            should_close = True

        try:
            logger.debug(
                "openai_request_dispatch",
                model=model,
                prompt_length=len(prompt),
            )
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            if not response.choices:
                logger.error("openai_response_empty_choices")
                return "[LLM_INVALID_RESPONSE] OpenAI returned no completion choices."

            content = response.choices[0].message.content
            return content.strip() if content else ""

        except AuthenticationError as exc:
            logger.error("openai_auth_error", error=str(exc))
            return "[LLM_PROVIDER_ERROR] Authentication failure with the configured LLM provider."

        except APITimeoutError as exc:
            logger.error("openai_timeout_error", error=str(exc))
            return "[LLM_TIMEOUT] Request to the LLM provider timed out."

        except RateLimitError as exc:
            logger.error("openai_rate_limit_error", error=str(exc))
            return "[LLM_PROVIDER_ERROR] Rate limit exceeded on LLM provider."

        except OpenAIError as exc:
            logger.error("openai_general_error", error=str(exc))
            return f"[LLM_PROVIDER_ERROR] LLM provider error: {str(exc)}"

        except Exception as exc:
            logger.error("openai_unexpected_error", error=str(exc))
            return f"[LLM_PROVIDER_ERROR] Unexpected error during LLM generation: {str(exc)}"

        finally:
            if should_close:
                await client.close()
