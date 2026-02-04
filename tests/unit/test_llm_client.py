"""
Unit tests for LLM client module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello there!"
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await llm_client.chat_completion([{"role": "user", "content": "Hello"}])
        
        assert result == mock_response
        llm_client.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_tools(self, llm_client):
        """Test chat completion with tool calling."""
        tools = [{"type": "function", "function": {"name": "test_tool"}}]
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I'll use a tool"
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await llm_client.chat_completion(
            [{"role": "user", "content": "Hello"}],
            tools=tools,
            tool_choice="auto"
        )
        
        assert result == mock_response
        # Verify tools and tool_choice were passed
        call_args = llm_client.client.chat.completions.create.call_args
        assert call_args[1]["tools"] == tools
        assert call_args[1]["tool_choice"] == "auto"
    
    @pytest.mark.asyncio
    async def test_chat_completion_api_error(self, llm_client):
        """Test chat completion with API error."""
        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(Exception) as exc_info:
            await llm_client.chat_completion([{"role": "user", "content": "Hello"}])
        
        assert "API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_simple_chat_success(self, llm_client):
        """Test simple chat completion."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Simple response"
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await llm_client.simple_chat([{"role": "user", "content": "Hello"}])
        
        assert result == "Simple response"
    
    @pytest.mark.asyncio
    async def test_simple_chat_empty_response(self, llm_client):
        """Test simple chat with empty response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await llm_client.simple_chat([{"role": "user", "content": "Hello"}])
        
        assert result is None