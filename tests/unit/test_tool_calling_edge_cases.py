"""
Unit tests for tool calling edge cases.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aibotto.ai.tool_calling import ToolCallingManager


class TestToolCallingEdgeCases:
    """Test cases for tool calling edge cases."""

    @pytest.fixture
    def tool_manager(self):
        """Create a ToolCallingManager instance for testing."""
        with patch('src.aibotto.ai.tool_calling.LLMClient') as mock_llm:
            with patch('src.aibotto.ai.tool_calling.CLIExecutor') as mock_executor:
                manager = ToolCallingManager()
                manager.llm_client = AsyncMock()
                manager.cli_executor = AsyncMock()
                return manager

    @pytest.mark.asyncio
    async def test_tool_call_execution_error(self, tool_manager):
        """Test tool call execution with error."""
        # Create proper mock objects
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = '{"command": "invalid_command"}'
        mock_tool_call.id = "test_id"

        mock_response = AsyncMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        # Mock second call (after tool execution)
        mock_final_response = AsyncMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message = MagicMock()
        mock_final_response.choices[0].message.content = "Command failed due to error."

        tool_manager.llm_client.chat_completion.side_effect = [mock_response, mock_final_response]

        # Mock command execution to raise error
        tool_manager.cli_executor.execute_command.side_effect = Exception("Command not found")

        # Mock database operations
        with patch('src.aibotto.ai.tool_calling.DatabaseOperations') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.get_conversation_history.return_value = []
            mock_db_instance.save_message.return_value = None

            # Process a message that will cause tool execution error
            response = await tool_manager.process_user_request(
                user_id=123, chat_id=456, message="test", db_ops=mock_db_instance
            )

            # Should handle error gracefully
            assert "Error:" in response or "error" in response.lower()
            tool_manager.cli_executor.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_tool_function(self, tool_manager):
        """Test handling of unknown tool functions."""
        # Create proper mock objects
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "unknown_function"
        mock_tool_call.function.arguments = '{"param": "value"}'
        mock_tool_call.id = "test_id"

        mock_response = AsyncMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        # Mock second call (after tool execution)
        mock_final_response = AsyncMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message = MagicMock()
        mock_final_response.choices[0].message.content = "Unknown tool function handled."

        tool_manager.llm_client.chat_completion.side_effect = [mock_response, mock_final_response]

        # Mock database operations
        with patch('src.aibotto.ai.tool_calling.DatabaseOperations') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.get_conversation_history.return_value = []
            mock_db_instance.save_message.return_value = None

            # Process a message with unknown tool function
            response = await tool_manager.process_user_request(
                user_id=123, chat_id=456, message="test", db_ops=mock_db_instance
            )

            # Should handle unknown function gracefully
            assert "Unknown tool function" in response or "Error:" in response or "I encountered an error" in response

    @pytest.mark.asyncio
    async def test_fact_check_response_method(self, tool_manager):
        """Test the fact_check_response method."""
        result = await tool_manager.fact_check_response("test query", "test response")
        assert "verify this information" in result

    @pytest.mark.asyncio
    async def test_process_user_request_general_error(self, tool_manager):
        """Test general error handling in process_user_request."""
        # Mock LLM to raise exception
        tool_manager.llm_client.chat_completion.side_effect = Exception("API Error")

        # Mock database operations
        with patch('src.aibotto.ai.tool_calling.DatabaseOperations') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.get_conversation_history.return_value = []
            mock_db_instance.save_message.return_value = None

            # Process a message that will cause general error
            response = await tool_manager.process_user_request(
                user_id=123, chat_id=456, message="test", db_ops=mock_db_instance
            )

            # Should return error message
            assert "Error:" in response or "error" in response.lower()
            assert "API Error" in response
