"""Test cases for GLM model tool calling fix."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.aibotto.ai.llm_client import LLMClient
from src.aibotto.config.settings import Config


class TestGLMToolCalling:
    """Test GLM model tool calling behavior."""

    @pytest.fixture
    def mock_response_with_tools(self):
        """Mock response with tool calls."""
        response = MagicMock()
        response.model_dump.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "I'll check what day it is today.",
                        "tool_calls": [
                            {
                                "id": "test-tool-call-1",
                                "type": "function",
                                "function": {
                                    "name": "execute_cli_command",
                                    "arguments": '{"command": "date"}'
                                }
                            }
                        ]
                    }
                }
            ]
        }
        return response

    @pytest.fixture
    def mock_response_no_tools(self):
        """Mock response without tool calls."""
        response = MagicMock()
        response.model_dump.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "2 + 2 equals 4.",
                        "tool_calls": []
                    }
                }
            ]
        }
        return response

    @pytest.mark.asyncio
    async def test_tool_choice_auto_when_tools_provided(self, mock_response_with_tools):
        """Test that tool_choice is set to 'auto' when tools are provided and tool_choice is None."""
        client = LLMClient()
        
        # Mock the OpenAI client
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response_with_tools
            
            tools = [{
                'type': 'function',
                'function': {
                    'name': 'execute_cli_command',
                    'description': 'Execute CLI commands',
                    'parameters': {'type': 'object', 'properties': {'command': {'type': 'string'}}}
                }
            }]
            
            await client.chat_completion(
                messages=[{'role': 'user', 'content': 'what day is today?'}],
                tools=tools
            )
            
            # Verify the call was made with correct parameters
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            
            assert call_kwargs['tools'] == tools
            assert call_kwargs['tool_choice'] == 'auto'
            assert call_kwargs['model'] == Config.OPENAI_MODEL

    @pytest.mark.asyncio
    async def test_tool_choice_preserved_when_provided(self, mock_response_with_tools):
        """Test that provided tool_choice is preserved when passed explicitly."""
        client = LLMClient()
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response_with_tools
            
            tools = [{
                'type': 'function',
                'function': {
                    'name': 'execute_cli_command',
                    'description': 'Execute CLI commands',
                    'parameters': {'type': 'object', 'properties': {}}
                }
            }]
            
            await client.chat_completion(
                messages=[{'role': 'user', 'content': 'test'}],
                tools=tools,
                tool_choice='required'
            )
            
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs['tool_choice'] == 'required'

    @pytest.mark.asyncio
    async def test_no_tool_choice_when_no_tools(self, mock_response_no_tools):
        """Test that tool_choice is not set when tools is None."""
        client = LLMClient()
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response_no_tools
            
            await client.chat_completion(
                messages=[{'role': 'user', 'content': 'what is 2+2?'}],
                tools=None
            )
            
            call_kwargs = mock_create.call_args[1]
            assert 'tool_choice' not in call_kwargs
            assert call_kwargs['tools'] is None

    @pytest.mark.asyncio
    async def test_tool_choice_not_passed_when_tools_empty(self, mock_response_no_tools):
        """Test that tool_choice is not passed to API when tools is empty list."""
        client = LLMClient()
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response_no_tools
            
            await client.chat_completion(
                messages=[{'role': 'user', 'content': 'test'}],
                tools=[]
            )
            
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs['tools'] == []
            # Empty list is falsy, so tool_choice should NOT be set
            assert 'tool_choice' not in call_kwargs

    @pytest.mark.asyncio
    async def test_kwargs_preservation(self, mock_response_with_tools):
        """Test that additional kwargs are preserved in the request."""
        client = LLMClient()
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response_with_tools
            
            tools = [{'type': 'function', 'function': {'name': 'test', 'parameters': {}}}]
            
            await client.chat_completion(
                messages=[{'role': 'user', 'content': 'test'}],
                tools=tools,
                temperature=0.5,
                max_tokens=100
            )
            
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs['temperature'] == 0.5
            assert call_kwargs['max_tokens'] == 100
            assert call_kwargs['tool_choice'] == 'auto'