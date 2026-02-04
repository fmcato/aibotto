"""
End-to-end tests for tool calling visibility and user experience.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Message, Update
from telegram.ext import ContextTypes

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations


class TestToolCallingVisibility:
    """Test cases for tool calling visibility to users."""

    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update."""
        update = MagicMock(spec=Update)
        update.effective_user.id = 12345
        update.effective_chat.id = 67890
        update.message = MagicMock(spec=Message)
        update.message.text = "What day is today?"
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
        with patch('src.aibotto.ai.tool_calling.LLMClient') as mock_llm:
            with patch('src.aibotto.ai.tool_calling.CLIExecutor') as mock_executor:
                manager = ToolCallingManager()

                # Mock LLM client
                manager.llm_client = MagicMock()

                # Mock CLI executor
                manager.cli_executor = MagicMock()
                manager.cli_executor.execute_command = AsyncMock(
                    return_value="Mon Feb  3 10:30:45 UTC 2026"
                )

                return manager

    @pytest.fixture
    async def db_ops(self):
        """Create database operations with in-memory database."""
        db_ops = DatabaseOperations()
        # Clear any existing data to avoid test contamination
        await db_ops.clear_conversation_history(12345, 67890)
        return db_ops

    @pytest.mark.asyncio
    async def test_tool_calling_flow_hides_intermediate_steps(self, tool_manager, db_ops):
        """Test that tool calling flow doesn't expose intermediate steps to users."""
        # Mock the first LLM response (contains tool call)
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = '{"command": "date"}'
        mock_tool_call.id = "tool_call_123"

        mock_first_response = MagicMock()
        mock_first_response.choices = [MagicMock()]
        mock_first_response.choices[0].message = MagicMock()
        mock_first_response.choices[0].message.content = "Let me get the current date for you."
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call]

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = MagicMock()
        mock_second_response.choices = [MagicMock()]
        mock_second_response.choices[0].message = MagicMock()
        mock_second_response.choices[0].message.content = "Today is Monday, February 3, 2026."

        # Set up the LLM client to return different responses
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="What day is today?",
            db_ops=db_ops
        )

        # The final result should be the processed response, not the tool call
        assert result == "Today is Monday, February 3, 2026."
        assert "execute_cli_command" not in result
        assert "tool_call_123" not in result

        # Verify that LLM was called twice (initial + with tool result)
        assert tool_manager.llm_client.chat_completion.call_count == 2

        # Verify that the command was executed
        tool_manager.cli_executor.execute_command.assert_called_once_with("date")

    @pytest.mark.asyncio
    async def test_direct_response_without_tool_calls(self, tool_manager, db_ops):
        """Test that direct responses (without tool calls) work correctly."""
        # Mock the LLM response (no tool calls)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Hello! I'm here to help you with factual information."
        # CRITICAL: Set tool_calls to an empty list, not a MagicMock
        mock_response.choices[0].message.tool_calls = []

        tool_manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="Hello",
            db_ops=db_ops
        )

        # The result should be the direct response
        assert result == "Hello! I'm here to help you with factual information."
        assert "execute_cli_command" not in result

        # Verify that LLM was called only once
        assert tool_manager.llm_client.chat_completion.call_count == 1

        # Verify that no command was executed
        tool_manager.cli_executor.execute_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_handling_in_tool_calling(self, tool_manager, db_ops):
        """Test that errors in tool calling are handled gracefully."""
        # Mock the first LLM response (contains tool call)
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = '{"command": "date"}'
        mock_tool_call.id = "tool_call_123"

        mock_first_response = MagicMock()
        mock_first_response.choices = [MagicMock()]
        mock_first_response.choices[0].message = MagicMock()
        mock_first_response.choices[0].message.content = "Let me get the current date for you."
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call]

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = MagicMock()
        mock_second_response.choices = [MagicMock()]
        mock_second_response.choices[0].message = MagicMock()
        mock_second_response.choices[0].message.content = "I encountered an issue getting that information. Let me try a different approach."

        # Set up the LLM client to return different responses
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Mock command execution to return an error
        tool_manager.cli_executor.execute_command = AsyncMock(
            return_value="Error: command not found"
        )

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="What day is today?",
            db_ops=db_ops
        )

        # The result should be a user-friendly error message, not the technical error
        assert "I encountered an issue" in result
        assert "Error: command not found" not in result

        # Verify that LLM was called twice
        assert tool_manager.llm_client.chat_completion.call_count == 2

    @pytest.mark.asyncio
    async def test_conversation_history_isolation(self, tool_manager, db_ops):
        """Test that tool calling doesn't expose previous tool calls in conversation history."""
        # Add some initial conversation history
        await db_ops.save_message(12345, 67890, 0, "user", "Hello")
        await db_ops.save_message(12345, 67890, 0, "assistant", "Hello! How can I help you today?")

        # Mock the first LLM response (contains tool call)
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = '{"command": "date"}'
        mock_tool_call.id = "tool_call_123"

        mock_first_response = MagicMock()
        mock_first_response.choices = [MagicMock()]
        mock_first_response.choices[0].message = MagicMock()
        mock_first_response.choices[0].message.content = "Let me get the current date for you."
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call]

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = MagicMock()
        mock_second_response.choices = [MagicMock()]
        mock_second_response.choices[0].message = MagicMock()
        mock_second_response.choices[0].message.content = "Today is Monday, February 3, 2026."

        # Set up the LLM client to return different responses
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="What day is today?",
            db_ops=db_ops
        )

        # Get the conversation history
        history = await db_ops.get_conversation_history(12345, 67890)

        # Verify that tool calls are not exposed in conversation history
        for message in history:
            assert "execute_cli_command" not in message.get("content", "")
            assert "tool_call_123" not in message.get("content", "")
            assert "[EXECUTED]" not in message.get("content", "")

        # The final result should be clean
        assert result == "Today is Monday, February 3, 2026."

    @pytest.mark.asyncio
    async def test_system_prompt_prevents_tool_call_exposure(self, tool_manager, db_ops):
        """Test that system prompts prevent tool call information from being exposed."""
        # Mock the first LLM response (contains tool call)
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = '{"command": "date"}'
        mock_tool_call.id = "tool_call_123"

        mock_first_response = MagicMock()
        mock_first_response.choices = [MagicMock()]
        mock_first_response.choices[0].message = MagicMock()
        mock_first_response.choices[0].message.content = "Let me get the current date for you."
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call]

        # Mock the second LLM response that should clean up the tool call info
        mock_second_response = MagicMock()
        mock_second_response.choices = [MagicMock()]
        mock_second_response.choices[0].message = MagicMock()
        mock_second_response.choices[0].message.content = "Today is Monday, February 3, 2026."

        # Set up the LLM client to return different responses
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="What day is today?",
            db_ops=db_ops
        )

        # The final result should not contain any tool call information
        assert result == "Today is Monday, February 3, 2026."
        assert "tool_call" not in result.lower()
        assert "execute_cli_command" not in result
        assert "function" not in result.lower()
        assert "arguments" not in result.lower()
