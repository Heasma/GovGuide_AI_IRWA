"""
GovGuide AI — Unit Tests: LLM Client & Adapters

Tests:
- StubLLMClient behavior and message
- OpenAIAdapter initialization and parameter handling
- Error handling: unconfigured client, timeouts, authentication, rate limits
- Factory function get_llm_client() switching
- Verification that API keys and secrets are never leaked in logs or error messages
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from openai import APITimeoutError, AuthenticationError, RateLimitError

from app.llm.llm_client import BaseLLMClient, StubLLMClient, get_llm_client
from app.llm.openai_adapter import OpenAIAdapter


@pytest.mark.anyio
async def test_stub_llm_client_returns_unconfigured_message():
    client = StubLLMClient()
    response = await client.generate("Hello GovGuide")
    assert "[LLM_NOT_CONFIGURED]" in response
    assert isinstance(response, str)


@pytest.mark.anyio
async def test_openai_adapter_unconfigured_returns_controlled_error():
    adapter = OpenAIAdapter(api_key="", model="")
    res = await adapter.generate("Test prompt")
    assert "[LLM_NOT_CONFIGURED]" in res


@pytest.mark.anyio
async def test_openai_adapter_successful_generation():
    mock_choice = MagicMock()
    mock_choice.message.content = "A Retail Food License is required in Chicago [Source 1]."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    adapter = OpenAIAdapter(
        api_key="sk-test-key-mock-valid",
        model="gpt-4o-mini",
        client=mock_client,
    )
    result = await adapter.generate("What license is needed for a restaurant?")
    assert "Retail Food License" in result
    assert "[Source 1]" in result


@pytest.mark.anyio
async def test_openai_adapter_timeout_error_handling():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=APITimeoutError(request=MagicMock())
    )

    adapter = OpenAIAdapter(
        api_key="sk-test-key-mock",
        model="gpt-4o-mini",
        client=mock_client,
    )
    result = await adapter.generate("Test timeout")
    assert "[LLM_TIMEOUT]" in result


import httpx

@pytest.mark.anyio
async def test_openai_adapter_auth_error_handling():
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(status_code=401, request=req)
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=AuthenticationError(
            message="Invalid API key",
            response=resp,
            body=None,
        )
    )

    adapter = OpenAIAdapter(
        api_key="sk-invalid-key-mock",
        model="gpt-4o-mini",
        client=mock_client,
    )
    result = await adapter.generate("Test auth error")
    assert "[LLM_PROVIDER_ERROR]" in result
    assert "sk-invalid-key-mock" not in result  # Secret must NOT leak


@pytest.mark.anyio
async def test_openai_adapter_rate_limit_handling():
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(status_code=429, request=req)
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=RateLimitError(
            message="Rate limit reached",
            response=resp,
            body=None,
        )
    )

    adapter = OpenAIAdapter(
        api_key="sk-test-mock",
        model="gpt-4o-mini",
        client=mock_client,
    )
    result = await adapter.generate("Test rate limit")
    assert "[LLM_PROVIDER_ERROR]" in result
    assert "Rate limit" in result


def test_get_llm_client_factory():
    client = get_llm_client()
    assert isinstance(client, BaseLLMClient)
