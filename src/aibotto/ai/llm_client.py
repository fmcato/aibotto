"""
LLM client for OpenAI-compatible API integration.
"""

import asyncio
import logging
import time
from typing import Any, cast

import openai
from openai import RateLimitError

from ..config.settings import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for OpenAI-compatible API."""

    # Timeout for LLM API calls (seconds)
    LLM_TIMEOUT = 120.0

    def __init__(self) -> None:
        self.client = openai.AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            timeout=self.LLM_TIMEOUT,
        )
        # Track rate limit reset time to avoid unnecessary retries
        self._rate_limit_reset_time: float | None = None

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],  # Changed from str to Any to match API
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create chat completion with optional tool calling."""
        
        # Check if we're in a rate limit cooldown period
        if self._rate_limit_reset_time and time.time() < self._rate_limit_reset_time:
            remaining_wait = self._rate_limit_reset_time - time.time()
            logger.info(f"Rate limited, waiting {remaining_wait:.1f}s before retrying")
            await asyncio.sleep(remaining_wait)
            self._rate_limit_reset_time = None  # Reset after waiting

        try:
            # Build request params
            params: dict[str, Any] = {
                "model": Config.OPENAI_MODEL,
                "messages": messages,
                "tools": tools,
                "tool_choice": tool_choice,
                "stream": False,
                **kwargs,
            }

            # Add max_tokens if configured (can speed up reasoning models)
            if Config.LLM_MAX_TOKENS is not None:
                params["max_tokens"] = Config.LLM_MAX_TOKENS

            response = await self.client.chat.completions.create(**params)
            return cast(dict[str, Any], response.model_dump())
            
        except RateLimitError as e:
            # Parse rate limit headers to determine reset time
            self._handle_rate_limit_error(e)
            
            # Wait for the calculated delay
            if self._rate_limit_reset_time and time.time() < self._rate_limit_reset_time:
                remaining_wait = self._rate_limit_reset_time - time.time()
                logger.info(f"Waiting {remaining_wait:.1f}s for rate limit to reset")
                await asyncio.sleep(remaining_wait)
                self._rate_limit_reset_time = None
            
            raise
            
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise

    def _handle_rate_limit_error(self, error: RateLimitError) -> None:
        """Handle rate limit error by parsing headers and setting reset time."""
        try:
            # Extract headers from the error response
            headers = getattr(error.response, 'headers', {}) if hasattr(error, 'response') else {}
            
            # Get reset time from headers, default to exponential backoff
            reset_timestamp = headers.get('x-ratelimit-reset')
            if reset_timestamp:
                # Convert to seconds and add a small buffer
                reset_time = float(reset_timestamp) / 1000 + 1.0  # Convert ms to seconds
                current_time = time.time()
                
                if reset_time > current_time:
                    wait_time = reset_time - current_time
                    logger.info(f"Rate limited until {reset_time}, waiting {wait_time:.1f}s")
                    self._rate_limit_reset_time = reset_time
                else:
                    # Reset time is in the past, use exponential backoff
                    wait_time = Config.LLM_RETRY_DELAY
                    logger.info(f"Rate limit reset time in past, using exponential backoff: {wait_time:.1f}s")
                    self._rate_limit_reset_time = current_time + wait_time
            else:
                # No headers, use exponential backoff
                wait_time = Config.LLM_RETRY_DELAY
                logger.info(f"No rate limit headers found, using exponential backoff: {wait_time:.1f}s")
                self._rate_limit_reset_time = time.time() + wait_time
                
        except Exception as e:
            # Fallback to exponential backoff if header parsing fails
            wait_time = Config.LLM_RETRY_DELAY
            logger.warning(f"Error parsing rate limit headers: {e}, using exponential backoff: {wait_time:.1f}s")
            self._rate_limit_reset_time = time.time() + wait_time

    async def simple_chat(self, messages: list[dict[str, str]]) -> str:
        """Simple chat completion without tool calling."""
        response = await self.chat_completion(messages)
        return cast(str, response["choices"][0]["message"]["content"])