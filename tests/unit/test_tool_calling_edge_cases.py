"""
Unit tests for tool calling edge cases.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.aibotto.ai.agentic_orchestrator import ToolCallingManager


class TestToolCallingEdgeCases:
    """Test cases for tool calling edge cases."""

    @pytest.fixture
    def tool_manager(self):
        """Create a ToolCallingManager instance for testing."""
        with patch('src.aibotto.ai.agentic_orchestrator.LLMClient') as mock_llm:
            manager = ToolCallingManager()
            manager.llm_client = AsyncMock()

            # Get the CLI executor from the tool registry and configure it
            from src.aibotto.tools.tool_registry import tool_registry
            cli_executor = tool_registry.get_executor("execute_cli_command")
            if cli_executor:
                cli_executor.execute = AsyncMock()

            return manager

    @pytest.mark.asyncio
    async def test_tool_call_execution_error(self, tool_manager):
        """Test tool call execution with error."""
        # Create proper mock objects - now using dict format since llm_client returns dict
        mock_tool_call = {
            "id": "test_id",
            "function": {
                "name": "execute_cli_command",
                "arguments": '{"command": "invalid_command"}'
            }
        }

        mock_response = {
            "choices": [{
                "message": {
                    "tool_calls": [mock_tool_call]
                }
            }]
        }

        # Mock second call (after tool execution)
        mock_final_response = {
            "choices": [{
                "message": {
                    "content": "Command failed due to error."
                }
            }]
        }

        tool_manager.llm_client.chat_completion.side_effect = [mock_response, mock_final_response]

        # Mock command execution to raise error
        from src.aibotto.tools.tool_registry import tool_registry
        cli_executor = tool_registry.get_executor("execute_cli_command")
        if cli_executor:
            cli_executor.execute = AsyncMock(side_effect=Exception("Command not found"))

        # Mock database operations
        with patch('src.aibotto.ai.agentic_orchestrator.DatabaseOperations') as mock_db:
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

    @pytest.mark.asyncio
    async def test_unknown_tool_function(self, tool_manager):
        """Test handling of unknown tool functions."""
        # Create proper mock objects - now using dict format
        mock_tool_call = {
            "id": "test_id",
            "function": {
                "name": "unknown_function",
                "arguments": '{"param": "value"}'
            }
        }

        mock_response = {
            "choices": [{
                "message": {
                    "tool_calls": [mock_tool_call]
                }
            }]
        }

        # Mock second call (after tool execution)
        mock_final_response = {
            "choices": [{
                "message": {
                    "content": "Unknown tool function handled."
                }
            }]
        }

        tool_manager.llm_client.chat_completion.side_effect = [mock_response, mock_final_response]

        # Mock database operations
        with patch('src.aibotto.ai.agentic_orchestrator.DatabaseOperations') as mock_db:
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

    # Removed fact_checker test as the module was deleted for being unnecessary

    @pytest.mark.asyncio
    async def test_process_user_request_general_error(self, tool_manager):
        """Test general error handling in process_user_request."""
        # Mock LLM to raise exception
        tool_manager.llm_client.chat_completion.side_effect = Exception("API Error")

        # Mock database operations
        with patch('src.aibotto.ai.agentic_orchestrator.DatabaseOperations') as mock_db:
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
