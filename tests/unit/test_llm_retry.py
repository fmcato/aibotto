"""Unit tests for LLM rate limit retry logic."""

import pytest

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from openai import RateLimitError

from aibotto.ai.llm_client import LLMClient
from aibotto.config.settings import Config


@pytest.mark.asyncio
async def test_retry_on_429_with_custom_backoff():
    """Test that LLM client retries 429 errors with 1s, 10s, 30s backoff."""
    client = LLMClient()

    # Mock the API to fail 2 times then succeed
    call_count = [0]
    expected_delays = []

    async def mock_create(**kwargs):
        call_count[0] += 1
        if call_count[0] <= 2:
            # Create rate limit error without reset time header
            response = MagicMock()
            response.headers = {}
            error = RateLimitError("Rate limit exceeded", response=response, body=None)
            raise error
        return MagicMock(model_dump=MagicMock(return_value={"choices": [{"message": {"content": "Success"}}]}))

    # Patch sleep to capture delays
    with patch('asyncio.sleep') as mock_sleep:
        mock_sleep.side_effect = lambda x: expected_delays.append(x)

        with patch.object(client.client.chat.completions, 'create', side_effect=mock_create):
            result = await client.chat_completion([{"role": "user", "content": "test"}])

    # Should have 2 delays (1st and 2nd retry attempts)
    assert len(expected_delays) == 2
    assert expected_delays[0] >= 0.8 and expected_delays[0] <= 1.2  # 1s with ±20% jitter
    assert expected_delays[1] >= 8.0 and expected_delays[1] <= 12.0  # 10s with ±20% jitter
    assert result == {"choices": [{"message": {"content": "Success"}}]}


@pytest.mark.asyncio
async def test_uses_server_reset_time_when_provided():
    """Test that server-provided reset time is used when available."""
    client = LLMClient()

    import time

    call_count = [0]
    expected_delays = []

    async def mock_create(**kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            # Create rate limit error with reset time header
            response = MagicMock()
            response.headers = {'x-ratelimit-reset': f"{int((time.time() + 0.5) * 1000)}"}
            error = RateLimitError("Rate limit exceeded", response=response, body=None)
            raise error
        return MagicMock(model_dump=MagicMock(return_value={"choices": [{"message": {"content": "Success"}}]}))

    with patch('asyncio.sleep') as mock_sleep:
        mock_sleep.side_effect = lambda x: expected_delays.append(x)

        with patch.object(client.client.chat.completions, 'create', side_effect=mock_create):
            result = await client.chat_completion([{"role": "user", "content": "test"}])

    # Should use server-provided reset time (~0.5s) not backoff
    assert len(expected_delays) == 1
    assert expected_delays[0] >= 0.5  # Server reset time with buffer


@pytest.mark.asyncio
async def test_max_retries_exceeded():
    """Test that error is raised after max retries."""
    client = LLMClient()

    async def mock_create(**kwargs):
        response = MagicMock()
        response.headers = {}
        error = RateLimitError("Rate limit exceeded", response=response, body=None)
        raise error

    with patch.object(client.client.chat.completions, 'create', side_effect=mock_create):
        with pytest.raises(RateLimitError):
            await client.chat_completion([{"role": "user", "content": "test"}])
