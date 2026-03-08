"""
End-to-end tests for parallel tool calling functionality.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Update, Message
from telegram.ext import ContextTypes

from src.aibotto.ai.agentic_orchestrator import ToolCallingManager


class TestParallelToolCalling:
    """Test cases for parallel tool calling functionality."""

    @pytest.fixture
    def mock_db_ops(self):
        """Create mock database operations."""
        db_ops = MagicMock()
        db_ops.get_conversation_history = AsyncMock(return_value=[])
        db_ops.save_message = AsyncMock()
        db_ops.save_message_compat = AsyncMock()
        db_ops.get_or_create_conversation = AsyncMock(return_value=1)
        db_ops.get_user_aspects = AsyncMock(return_value=[])
        return db_ops

    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update."""
        update = MagicMock(spec=Update)
        update.effective_user.id = 12345
        update.effective_chat.id = 67890
        update.message = MagicMock(spec=Message)
        update.message.text = "What's the weather and what time is it?"
        update.message.reply_text = AsyncMock()
        update.message.edit_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create a mock Telegram context."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        return context

    @pytest.fixture
    def tool_manager(self):
        """Create a ToolCallingManager with mocked dependencies."""
        manager = ToolCallingManager()

        # Mock LLM client - must be AsyncMock since it's awaited
        manager.llm_client = AsyncMock()

        # Mock tool executor
        manager.tool_executor = MagicMock()
        # ToolExecutor implements ToolExecutionInterface which requires execute_tool_calls
        manager.tool_executor.execute_tool_calls = AsyncMock(
            return_value=[{"tool_call_id": "test", "content": "Mock output"}]
        )
        # Also need execute_tool method
        manager.tool_executor.execute_tool = AsyncMock(
            return_value="Mock output"
        )
        # Also need _get_tool_definitions method
        manager.tool_executor._get_tool_definitions = MagicMock(return_value=[])

        yield manager

    @pytest.mark.asyncio
    async def test_parallel_tool_calls_execution(self, tool_manager, mock_db_ops):
        """Test that multiple tool calls are executed in parallel."""
        # Mock the first LLM response (contains multiple tool calls)
        mock_first_response = {
            "choices": [{
                "message": {
                    "content": "I need to get the current date and weather information.",
                    "tool_calls": [
                        {
                            "id": "tool_call_1",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "date"}'
                            }
                        },
                        {
                            "id": "tool_call_2",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "curl wttr.in?format=3"}'
                            }
                        }
                    ]
                }
            }]
        }

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = {
            "choices": [{
                "message": {
                    "content": "Today is Monday, February 3, 2026. The weather is 15°C.",
                    "tool_calls": []
                }
            }]
        }

        # Set up the LLM client to return different responses
        # llm_client is an AsyncMock, so chat_completion should be AsyncMock too
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="What's the weather and what time is it?",
            db_ops=mock_db_ops
        )

        # The result should include information from both tool calls
        assert "Today is Monday, February 3, 2026" in result
        assert tool_manager.llm_client.chat_completion.call_count == 2

    @pytest.mark.asyncio
    async def test_single_tool_call_still_works(self, tool_manager, mock_db_ops):
        """Test that single tool calls still work as before."""
        # Mock the first LLM response (contains single tool call)
        mock_first_response = {
            "choices": [{
                "message": {
                    "content": "I need to get the current date.",
                    "tool_calls": [
                        {
                            "id": "tool_call_123",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "date"}'
                            }
                        }
                    ]
                }
            }]
        }

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = {
            "choices": [{
                "message": {
                    "content": "Today is Monday, February 3, 2026.",
                    "tool_calls": []
                }
            }]
        }

        # Set up the LLM client to return different responses
        # llm_client is an AsyncMock, so chat_completion should be AsyncMock too
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="What day is today?",
            db_ops=mock_db_ops
        )

        # The result should be the direct response
        assert "Today is Monday, February 3, 2026." in result
        assert tool_manager.llm_client.chat_completion.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handling_in_parallel_tool_calls(self, tool_manager, mock_db_ops):
        """Test that errors in parallel tool calls are handled correctly."""
        # Mock the first LLM response (contains multiple tool calls, one will fail)
        mock_first_response = {
            "choices": [{
                "message": {
                    "content": "I need to get information from multiple commands.",
                    "tool_calls": [
                        {
                            "id": "tool_call_1",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "date"}'
                            }
                        },
                        {
                            "id": "tool_call_2",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "invalid_command"}'
                            }
                        }
                    ]
                }
            }]
        }

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = {
            "choices": [{
                "message": {
                    "content": "Today is Monday, February 3, 2026. One command failed to execute.",
                    "tool_calls": []
                }
            }]
        }

        # Set up the LLM client to return different responses
        # llm_client is an AsyncMock, so chat_completion should be AsyncMock too
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Mock the tool executor to raise an exception for one command
        async def mock_execute_tool(function_name, arguments, user_id, chat_id, db_ops):
            if "date" in str(arguments):
                return "Mon Feb  3 10:30:45 UTC 2026"
            else:
                raise Exception("Command not found")

        tool_manager.tool_executor.execute_tool = AsyncMock(side_effect=mock_execute_tool)

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="Get date and run invalid command",
            db_ops=mock_db_ops
        )

        # Check that the successful result is in the response
        assert "Today is Monday, February 3, 2026" in result
        assert tool_manager.llm_client.chat_completion.call_count == 2

    @pytest.mark.asyncio
    async def test_three_parallel_tool_calls(self, tool_manager, mock_db_ops):
        """Test that three tool calls can be executed in parallel."""
        # Mock the first LLM response (contains three tool calls)
        mock_first_response = {
            "choices": [{
                "message": {
                    "content": "I need to get the current date, username, and working directory.",
                    "tool_calls": [
                        {
                            "id": "tool_call_1",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "date"}'
                            }
                        },
                        {
                            "id": "tool_call_2",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "whoami"}'
                            }
                        },
                        {
                            "id": "tool_call_3",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "pwd"}'
                            }
                        }
                    ]
                }
            }]
        }

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = {
            "choices": [{
                "message": {
                    "content": "Today is Monday, February 3, 2026. You are user1 and your current directory is /home/user1.",
                    "tool_calls": []
                }
            }]
        }

        # Set up the LLM client to return different responses
        # llm_client is an AsyncMock, so chat_completion should be AsyncMock too
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="Get date, username, and working directory",
            db_ops=mock_db_ops
        )

        # Verify that LLM was called twice
        assert tool_manager.llm_client.chat_completion.call_count == 2
        assert "Today is Monday, February 3, 2026" in result
        assert "user1" in result
        assert "/home/user1" in result
