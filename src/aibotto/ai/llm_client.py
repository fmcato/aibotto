"""
LLM client for OpenAI-compatible API integration.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, cast

import openai
from openai import RateLimitError

from ..config.settings import Config
from .backoff_handler import ExponentialBackoffHandler

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client.

    All fields have safe defaults that fall back to global Config.
    Use this class to create subagent-specific LLM configurations.

    Attributes:
        api_key: API key for authentication
        base_url: Base URL for the API endpoint
        model: Model identifier to use
        max_tokens: Maximum tokens for responses
        temperature: Temperature for response generation
    """

    api_key: str = field(default_factory=lambda: Config.OPENAI_API_KEY)
    base_url: str = field(default_factory=lambda: Config.OPENAI_BASE_URL)
    model: str = field(default_factory=lambda: Config.OPENAI_MODEL)
    max_tokens: int | None = field(default_factory=lambda: Config.LLM_MAX_TOKENS)
    temperature: float | None = None

    @classmethod
    def from_provider(
        cls,
        provider_config: Any,
        model: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> "LLMConfig":
        """Create LLMConfig from a provider configuration.

        Args:
            provider_config: LLMProviderConfig instance with api_key_env and base_url
            model: Model identifier to use
            max_tokens: Optional max tokens override
            temperature: Optional temperature override

        Returns:
            LLMConfig instance
        """
        return cls(
            api_key=provider_config.get_api_key(),
            base_url=provider_config.base_url,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )


class LLMClient:
    """Client for OpenAI-compatible API."""

    LLM_TIMEOUT = 300.0

    def __init__(self, config: LLMConfig | None = None) -> None:
        """Initialize LLM client with optional configuration.

        Args:
            config: LLMConfig instance. If None, uses global Config defaults.
        """
        self._config = config or LLMConfig()

        self.client = openai.AsyncOpenAI(
            api_key=self._config.api_key,
            base_url=self._config.base_url,
            timeout=self.LLM_TIMEOUT,
        )
        self._rate_limit_reset_time: float | None = None
        self._backoff_handler = ExponentialBackoffHandler()

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],  # Changed from str to Any to match API
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create chat completion with optional tool calling."""
        max_retries = Config.LLM_MAX_RETRIES

        for attempt in range(max_retries):
            # Check if we're in a rate limit cooldown period
            if (
                self._rate_limit_reset_time
                and time.time() < self._rate_limit_reset_time
            ):
                remaining_wait = self._rate_limit_reset_time - time.time()
                logger.info(
                    f"Rate limited, waiting {remaining_wait:.1f}s before retrying"
                )
                await asyncio.sleep(remaining_wait)
                self._rate_limit_reset_time = None  # Reset after waiting

            try:
                # Build request params
                params: dict[str, Any] = {
                    "model": self._config.model,
                    "messages": messages,
                    "tools": tools,
                    "stream": False,
                    **kwargs,
                }

                # Set tool_choice appropriately for GLM compatibility
                if tools:
                    params["tool_choice"] = (
                        tool_choice if tool_choice is not None else "auto"
                    )
                # Note: When tools is None, tool_choice is not set (GLM validation error)

                # Add max_tokens if configured
                if self._config.max_tokens is not None:
                    params["max_tokens"] = self._config.max_tokens

                # Add temperature if configured
                if self._config.temperature is not None:
                    params["temperature"] = self._config.temperature

                response = await self.client.chat.completions.create(**params)

                # Record successful request and reset backoff counter
                self._backoff_handler.record_success()
                return cast(dict[str, Any], response.model_dump())

            except RateLimitError as e:
                # If this was our last retry attempt, raise the error
                if attempt == max_retries - 1:
                    logger.error(f"Max retries ({max_retries}) reached, giving up")
                    raise

                # Parse rate limit headers to determine reset time
                reset_time = self._get_rate_limit_reset_time(e)

                # Increment retry counter for backoff calculation
                self._backoff_handler.record_retry()

                # Wait for the calculated delay
                if reset_time and time.time() < reset_time:
                    # Use server-provided reset time
                    remaining_wait = reset_time - time.time()
                    logger.info(
                        f"Rate limited until {reset_time}, waiting {remaining_wait:.1f}s "
                        f"(retry {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(remaining_wait)
                    self._rate_limit_reset_time = None
                else:
                    # Use backoff handler (1s, 10s, 30s progression)
                    backoff_delay = self._backoff_handler.calculate_backoff()
                    logger.info(
                        f"Rate limited, waiting {backoff_delay:.1f}s "
                        f"(retry {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(backoff_delay)

            except Exception as e:
                logger.error(f"LLM API error: {e}")
                raise

        # Should never reach here, but for type safety
        raise RuntimeError("Unexpected end of retry loop")

    def _get_rate_limit_reset_time(self, error: RateLimitError) -> float | None:
        """Extract rate limit reset time from error headers.

        Args:
            error: RateLimitError from OpenAI API

        Returns:
            Unix timestamp of reset time, or None if not available
        """
        try:
            # Extract headers from the error response
            headers = (
                getattr(error.response, "headers", {})
                if hasattr(error, "response")
                else {}
            )

            # Get reset time from headers if available
            reset_timestamp = headers.get("x-ratelimit-reset")
            if reset_timestamp:
                # Convert to seconds and add a small buffer
                reset_time = float(reset_timestamp) / 1000 + 1.0
                return reset_time

            return None

        except Exception:
            # Return None on any parsing error
            return None

    async def simple_chat(self, messages: list[dict[str, str]]) -> str:
        """Simple chat completion without tool calling."""
        response = await self.chat_completion(messages)
        return cast(str, response["choices"][0]["message"]["content"])
