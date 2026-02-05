"""
Tests for enhanced tool calling functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations


class TestEnhancedToolCalling:
    """Test enhanced tool calling functionality."""

    @pytest.fixture
    def tool_manager(self):
        """Create a tool calling manager for testing."""
        return ToolCallingManager()

    @pytest.fixture
    def mock_db_ops(self):
        """Create mock database operations."""
        db_ops = MagicMock(spec=DatabaseOperations)
        db_ops.get_conversation_history = AsyncMock(return_value=[])
        db_ops.save_message = AsyncMock()
        return db_ops

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        with patch('src.aibotto.ai.tool_calling.LLMClient') as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_cli_executor(self):
        """Create mock CLI executor."""
        with patch('src.aibotto.ai.tool_calling.CLIExecutor') as mock:
            executor = MagicMock()
            executor.execute_command = AsyncMock(return_value="Command executed successfully")
            mock.return_value = executor
            yield executor

    async def test_single_tool_call_flow(self, tool_manager, mock_db_ops, mock_llm_client, mock_cli_executor):
        """Test basic single tool call flow."""
        # Setup LLM to return a tool call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [
            MagicMock(
                id="tool_1",
                function=MagicMock(
                    name="execute_cli_command",
                    arguments='{"command": "date"}'
                )
            )
        ]
        mock_llm_client.chat_completion = AsyncMock(return_value=mock_response)
        
        # Setup final response
        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message = MagicMock()
        final_response.choices[0].message.content = "The current date is 2024-01-15"
        mock_llm_client.chat_completion = AsyncMock(side_effect=[mock_response, final_response])
        
        # Execute
        result = await tool_manager.process_user_request(
            user_id=1, chat_id=1, message="What day is today?", db_ops=mock_db_ops
        )
        
        # Verify
        assert result == "The current date is 2024-01-15"
        mock_llm_client.chat_completion.assert_called_twice()
        mock_cli_executor.execute_command.assert_called_once_with("date")

    async def test_multiple_parallel_tool_calls(self, tool_manager, mock_db_ops, mock_llm_client, mock_cli_executor):
        """Test multiple parallel tool calls."""
        # Setup LLM to return multiple tool calls
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [
            MagicMock(
                id="tool_1",
                function=MagicMock(
                    name="execute_cli_command",
                    arguments='{"command": "date"}'
                )
            ),
            MagicMock(
                id="tool_2",
                function=MagicMock(
                    name="execute_cli_command",
                    arguments='{"command": "whoami"}'
                )
            )
        ]
        mock_llm_client.chat_completion = AsyncMock(return_value=mock_response)
        
        # Setup final response
        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message = MagicMock()
        final_response.choices[0].message.content = "Today is 2024-01-15 and you are user"
        mock_llm_client.chat_completion = AsyncMock(side_effect=[mock_response, final_response])
        
        # Execute
        result = await tool_manager.process_user_request(
            user_id=1, chat_id=1, message="What day is today and who am I?", db_ops=mock_db_ops
        )
        
        # Verify
        assert result == "Today is 2024-01-15 and you are user"
        mock_llm_client.chat_completion.assert_called_twice()
        assert mock_cli_executor.execute_command.call_count == 2

    async def test_tool_call_with_intermediate_message(self, tool_manager, mock_db_ops, mock_llm_client, mock_cli_executor):
        """Test tool call with intermediate message from LLM."""
        # This test will fail with current implementation but should pass with enhanced version
        # Setup LLM to return tool call first
        tool_response = MagicMock()
        tool_response.choices = [MagicMock()]
        tool_response.choices[0].message = MagicMock()
        tool_response.choices[0].message.tool_calls = [
            MagicMock(
                id="tool_1",
                function=MagicMock(
                    name="execute_cli_command",
                    arguments='{"command": "date"}'
                )
            )
        ]
        
        # Setup intermediate response (this is what we want to support)
        intermediate_response = MagicMock()
        intermediate_response.choices = [MagicMock()]
        intermediate_response.choices[0].message = MagicMock()
        intermediate_response.choices[0].message.content = "Let me get the current date for you..."
        intermediate_response.choices[0].message.tool_calls = None
        
        # Setup final response
        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message = MagicMock()
        final_response.choices[0].message.content = "The current date is 2024-01-15"
        
        mock_llm_client.chat_completion = AsyncMock(side_effect=[tool_response, intermediate_response, final_response])
        
        # Execute - this should fail with current implementation
        with pytest.raises(Exception):
            await tool_manager.process_user_request(
                user_id=1, chat_id=1, message="What day is today?", db_ops=mock_db_ops
            )

    async def test_iterative_tool_calls(self, tool_manager, mock_db_ops, mock_llm_client, mock_cli_executor):
        """Test iterative tool calls with multiple rounds."""
        # This test will fail with current implementation but should pass with enhanced version
        # Round 1: Get weather
        weather_response = MagicMock()
        weather_response.choices = [MagicMock()]
        weather_response.choices[0].message = MagicMock()
        weather_response.choices[0].message.tool_calls = [
            MagicMock(
                id="tool_1",
                function=MagicMock(
                    name="search_web",
                    arguments='{"query": "weather in London"}'
                )
            )
        ]
        
        # Round 2: Get time based on weather
        time_response = MagicMock()
        time_response.choices = [MagicMock()]
        time_response.choices[0].message = MagicMock()
        time_response.choices[0].message.content = "Now let me get the current time in London..."
        time_response.choices[0].message.tool_calls = [
            MagicMock(
                id="tool_2",
                function=MagicMock(
                    name="execute_cli_command",
                    arguments='{"command": "date"}'
                )
            )
        ]
        
        # Round 3: Final response
        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message = MagicMock()
        final_response.choices[0].message.content = "The weather in London is 72°F and it's currently 3:45 PM there."
        
        mock_llm_client.chat_completion = AsyncMock(side_effect=[weather_response, time_response, final_response])
        
        # Execute - this should fail with current implementation
        with pytest.raises(Exception):
            await tool_manager.process_user_request(
                user_id=1, chat_id=1, message="What's the weather and time in London?", db_ops=mock_db_ops
            )

    async def test_tool_call_dependencies(self, tool_manager, mock_db_ops, mock_llm_client, mock_cli_executor):
        """Test tool calls with dependencies (sequential execution)."""
        # This test will fail with current implementation but should pass with enhanced version
        # First tool: list files
        list_files_response = MagicMock()
        list_files_response.choices = [MagicMock()]
        list_files_response.choices[0].message = MagicMock()
        list_files_response.choices[0].message.tool_calls = [
            MagicMock(
                id="tool_1",
                function=MagicMock(
                    name="execute_cli_command",
                    arguments='{"command": "ls -la"}'
                )
            )
        ]
        
        # Second tool: get details of specific file (depends on first result)
        file_details_response = MagicMock()
        file_details_response.choices = [MagicMock()]
        file_details_response.choices[0].message = MagicMock()
        file_details_response.choices[0].message.content = "Now let me get details for the config file..."
        file_details_response.choices[0].message.tool_calls = [
            MagicMock(
                id="tool_2",
                function=MagicMock(
                    name="execute_cli_command",
                    arguments='{"command": "cat config.json"}'
                )
            )
        ]
        
        # Final response
        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message = MagicMock()
        final_response.choices[0].message.content = "Found the config file with settings..."
        
        mock_llm_client.chat_completion = AsyncMock(side_effect=[list_files_response, file_details_response, final_response])
        
        # Execute - this should fail with current implementation
        with pytest.raises(Exception):
            await tool_manager.process_user_request(
                user_id=1, chat_id=1, message="List files and show me the config file contents", db_ops=mock_db_ops
            )

    async def test_tool_call_error_handling(self, tool_manager, mock_db_ops, mock_llm_client, mock_cli_executor):
        """Test error handling in tool calls."""
        # Setup LLM to return a tool call that will fail
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [
            MagicMock(
                id="tool_1",
                function=MagicMock(
                    name="execute_cli_command",
                    arguments='{"command": "nonexistent_command"}'
                )
            )
        ]
        mock_llm_client.chat_completion = AsyncMock(return_value=mock_response)
        
        # Setup final response
        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message = MagicMock()
        final_response.choices[0].message.content = "Sorry, I couldn't execute that command."
        mock_llm_client.chat_completion = AsyncMock(side_effect=[mock_response, final_response])
        
        # Setup executor to raise an error
        mock_cli_executor.execute_command = AsyncMock(side_effect=Exception("Command not found"))
        
        # Execute
        result = await tool_manager.process_user_request(
            user_id=1, chat_id=1, message="Run a nonexistent command", db_ops=mock_db_ops
        )
        
        # Verify
        assert result == "Sorry, I couldn't execute that command."
        mock_cli_executor.execute_command.assert_called_once()

    async def test_no_tool_calls_direct_response(self, tool_manager, mock_db_ops, mock_llm_client, mock_cli_executor):
        """Test direct response without tool calls."""
        # Setup LLM to return direct response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].message.content = "Hello! How can I help you today?"
        mock_llm_client.chat_completion = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await tool_manager.process_user_request(
            user_id=1, chat_id=1, message="Hello", db_ops=mock_db_ops
        )
        
        # Verify
        assert result == "Hello! How can I help you today?"
        mock_llm_client.chat_completion.assert_called_once()
        mock_cli_executor.execute_command.assert_not_called()