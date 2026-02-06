"""
End-to-end tests for parallel tool calling functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations


class TestParallelToolCalling:
    """Test cases for parallel tool calling functionality."""

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

        # Mock LLM client
        manager.llm_client = MagicMock()

        # Mock CLI executor
        manager.cli_executor = MagicMock()
        manager.cli_executor.execute_command = AsyncMock(
            return_value="Mock output"
        )

        yield manager

    @pytest.fixture
    async def db_ops(self):
        """Create database operations with in-memory database."""
        db_ops = DatabaseOperations()
        # Clear any existing data to avoid test contamination
        await db_ops.clear_conversation_history(12345, 67890)
        return db_ops

    @pytest.mark.asyncio
    async def test_parallel_tool_calls_execution(self, tool_manager, db_ops):
        """Test that multiple tool calls are executed in parallel."""
        # Mock the first LLM response (contains multiple tool calls)
        mock_tool_call_1 = MagicMock()
        mock_tool_call_1.function.name = "execute_cli_command"
        mock_tool_call_1.function.arguments = '{"command": "date"}'
        mock_tool_call_1.id = "tool_call_1"

        mock_tool_call_2 = MagicMock()
        mock_tool_call_2.function.name = "execute_cli_command"
        mock_tool_call_2.function.arguments = '{"command": "curl wttr.in?format=3"}'
        mock_tool_call_2.id = "tool_call_2"

        mock_first_response = MagicMock()
        mock_first_response.choices = [MagicMock()]
        mock_first_response.choices[0].message = MagicMock()
        mock_first_response.choices[0].message.content = "I need to get the current date and weather information."
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call_1, mock_tool_call_2]

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = MagicMock()
        mock_second_response.choices = [MagicMock()]
        mock_second_response.choices[0].message = MagicMock()
        mock_second_response.choices[0].message.content = "Today is Monday, February 3, 2026. The weather is 15°C."
        mock_second_response.choices[0].message.tool_calls = []

        # Set up the LLM client to return different responses
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="What's the weather and what time is it?",
            db_ops=db_ops
        )

        # The result should include information from both tool calls
        assert "Today is Monday, February 3, 2026" in result
        assert "15°C" in result

        # Verify that LLM was called twice
        assert tool_manager.llm_client.chat_completion.call_count == 2

        # Verify that both tool calls were made
        assert tool_manager.cli_executor.execute_command.call_count == 2

        # Verify that both tool calls were executed with the correct commands
        calls = tool_manager.cli_executor.execute_command.call_args_list
        assert any("date" in str(call) for call in calls)
        assert any("wttr.in" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_single_tool_call_still_works(self, tool_manager, db_ops):
        """Test that single tool calls still work as before."""
        # Mock the first LLM response (contains single tool call)
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = '{"command": "date"}'
        mock_tool_call.id = "tool_call_123"

        mock_first_response = MagicMock()
        mock_first_response.choices = [MagicMock()]
        mock_first_response.choices[0].message = MagicMock()
        mock_first_response.choices[0].message.content = "I need to get the current date."
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call]

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = MagicMock()
        mock_second_response.choices = [MagicMock()]
        mock_second_response.choices[0].message = MagicMock()
        mock_second_response.choices[0].message.content = "Today is Monday, February 3, 2026."
        mock_second_response.choices[0].message.tool_calls = []

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

        # The result should be the direct response
        assert "Today is Monday, February 3, 2026." in result

        # Verify that LLM was called twice
        assert tool_manager.llm_client.chat_completion.call_count == 2

        # Verify that tool call was made
        assert tool_manager.cli_executor.execute_command.call_count == 1

    @pytest.mark.asyncio
    async def test_error_handling_in_parallel_tool_calls(self, tool_manager, db_ops):
        """Test that errors in parallel tool calls are handled correctly."""
        # Mock the first LLM response (contains multiple tool calls, one will fail)
        mock_tool_call_1 = MagicMock()
        mock_tool_call_1.function.name = "execute_cli_command"
        mock_tool_call_1.function.arguments = '{"command": "date"}'
        mock_tool_call_1.id = "tool_call_1"

        mock_tool_call_2 = MagicMock()
        mock_tool_call_2.function.name = "execute_cli_command"
        mock_tool_call_2.function.arguments = '{"command": "invalid_command"}'
        mock_tool_call_2.id = "tool_call_2"

        mock_first_response = MagicMock()
        mock_first_response.choices = [MagicMock()]
        mock_first_response.choices[0].message = MagicMock()
        mock_first_response.choices[0].message.content = "I need to get information from multiple commands."
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call_1, mock_tool_call_2]

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = MagicMock()
        mock_second_response.choices = [MagicMock()]
        mock_second_response.choices[0].message = MagicMock()
        mock_second_response.choices[0].message.content = "Today is Monday, February 3, 2026. One command failed to execute."
        mock_second_response.choices[0].message.tool_calls = []

        # Set up the LLM client to return different responses
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Mock the CLI executor to raise an exception for one command
        async def mock_execute_command(command):
            if "date" in command:
                return "Mon Feb  3 10:30:45 UTC 2026"
            else:
                raise Exception("Command not found")

        tool_manager.cli_executor.execute_command = AsyncMock(side_effect=mock_execute_command)

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="Get date and run invalid command",
            db_ops=db_ops
        )

        # Check that the successful result is in the response
        assert "Today is Monday, February 3, 2026" in result

        # Check that error handling worked
        assert tool_manager.cli_executor.execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_three_parallel_tool_calls(self, tool_manager, db_ops):
        """Test that three tool calls can be executed in parallel."""
        # Mock the first LLM response (contains three tool calls)
        mock_tool_call_1 = MagicMock()
        mock_tool_call_1.function.name = "execute_cli_command"
        mock_tool_call_1.function.arguments = '{"command": "date"}'
        mock_tool_call_1.id = "tool_call_1"

        mock_tool_call_2 = MagicMock()
        mock_tool_call_2.function.name = "execute_cli_command"
        mock_tool_call_2.function.arguments = '{"command": "whoami"}'
        mock_tool_call_2.id = "tool_call_2"

        mock_tool_call_3 = MagicMock()
        mock_tool_call_3.function.name = "execute_cli_command"
        mock_tool_call_3.function.arguments = '{"command": "pwd"}'
        mock_tool_call_3.id = "tool_call_3"

        mock_first_response = MagicMock()
        mock_first_response.choices = [MagicMock()]
        mock_first_response.choices[0].message = MagicMock()
        mock_first_response.choices[0].message.content = "I need to get the current date, username, and working directory."
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call_1, mock_tool_call_2, mock_tool_call_3]

        # Mock the second LLM response (final response after tool execution)
        mock_second_response = MagicMock()
        mock_second_response.choices = [MagicMock()]
        mock_second_response.choices[0].message = MagicMock()
        mock_second_response.choices[0].message.content = "Today is Monday, February 3, 2026. You are user1 and your current directory is /home/user1."
        mock_second_response.choices[0].message.tool_calls = []

        # Set up the LLM client to return different responses
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_first_response, mock_second_response]
        )

        # Process the user request
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="Get date, username, and working directory",
            db_ops=db_ops
        )

        # Verify that LLM was called twice
        assert tool_manager.llm_client.chat_completion.call_count == 2

        # Verify that all three tool calls were made
        assert tool_manager.cli_executor.execute_command.call_count == 3

        # Verify that all commands were executed
        calls = tool_manager.cli_executor.execute_command.call_args_list
        commands = [str(call) for call in calls]
        assert any("date" in cmd for cmd in commands)
        assert any("whoami" in cmd for cmd in commands)
        assert any("pwd" in cmd for cmd in commands)