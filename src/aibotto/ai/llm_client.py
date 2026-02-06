"""
LLM client for OpenAI-compatible API integration.
"""

import logging
from typing import Any, cast

import openai

from ..config.settings import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for OpenAI-compatible API."""

    def __init__(self) -> None:
        self.client = openai.AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL
        )

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],  # Changed from str to Any to match API
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create chat completion with optional tool calling."""
        try:
            response = await self.client.chat.completions.create(  # type: ignore[call-overload]
                model=Config.OPENAI_MODEL,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                stream=False,
                **kwargs,
            )
            return cast(dict[str, Any], response.model_dump())
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise

    async def simple_chat(self, messages: list[dict[str, str]]) -> str:
        """Simple chat completion without tool calling."""
        response = await self.chat_completion(messages)
        return response.choices[0].message.content  # type: ignore
