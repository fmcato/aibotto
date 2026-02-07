"""
Unit tests for LLM client module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aibotto.ai.llm_client import LLMClient


class TestLLMClient:
    """Test cases for LLMClient class."""

    @pytest.fixture
    def llm_client(self):
        """Create an LLMClient instance for testing."""
        with patch('src.aibotto.ai.llm_client.openai.AsyncOpenAI') as mock_openai:
            client = LLMClient()
            client.client = MagicMock()
            return client

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, llm_client):
        """Test successful chat completion."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"content": "Hello there!"}}]
        }
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await llm_client.chat_completion([{"role": "user", "content": "Hello"}])

        # Verify the response structure
        assert result is not None
        assert isinstance(result, dict)
        assert "choices" in result
        assert len(result["choices"]) > 0
        assert "message" in result["choices"][0]
        assert result["choices"][0]["message"]["content"] == "Hello there!"
        llm_client.client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_completion_with_tools(self, llm_client):
        """Test chat completion with tool calling."""
        tools = [{"type": "function", "function": {"name": "test_tool"}}]

        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"content": "I'll use a tool"}}]
        }
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await llm_client.chat_completion(
            [{"role": "user", "content": "Hello"}],
            tools=tools,
            tool_choice="auto"
        )

        # Verify the response structure
        assert result is not None
        assert isinstance(result, dict)
        assert "choices" in result
        assert len(result["choices"]) > 0
        assert "message" in result["choices"][0]
        assert result["choices"][0]["message"]["content"] == "I'll use a tool"
        llm_client.client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_simple_chat_success(self, llm_client):
        """Test simple chat completion with direct response."""
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"content": "Simple response"}}]
        }
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await llm_client.simple_chat([{"role": "user", "content": "Hi"}])

        assert result == "Simple response"

    @pytest.mark.asyncio
    async def test_simple_chat_empty_response(self, llm_client):
        """Test chat completion with empty response."""
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"content": None}}]
        }
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await llm_client.simple_chat([{"role": "user", "content": "Hello"}])

        assert result is None

    @pytest.mark.asyncio
    async def test_chat_completion_error(self, llm_client):
        """Test chat completion with error."""
        llm_client.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        with pytest.raises(Exception) as exc_info:
            await llm_client.chat_completion([{"role": "user", "content": "Hello"}])

        assert str(exc_info.value) == "API Error"