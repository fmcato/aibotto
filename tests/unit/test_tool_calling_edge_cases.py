"""
Unit tests for tool calling edge cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.ai.tool_calling import ToolCallingManager


class TestToolCallingEdgeCases:
    """Test cases for tool calling edge cases."""
    
    @pytest.fixture
    def tool_manager(self):
        """Create a ToolCallingManager instance for testing."""
        with patch('src.aibotto.ai.tool_calling.LLMClient') as mock_llm:
            with patch('src.aibotto.ai.tool_calling.EnhancedCLIExecutor') as mock_executor:
                manager = ToolCallingManager()
                manager.llm_client = MagicMock()
                manager.cli_executor = MagicMock()
                return manager
    
    @pytest.mark.asyncio
    async def test_tool_call_execution_error(self, tool_manager):
        """Test tool call execution with error."""
        # Mock tool calls with error
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = '{"command": "invalid_command"}'
        mock_tool_call.id = "test_id"
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        tool_manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
        
        # Mock database operations
        with patch('src.aibotto.ai.tool_calling.DatabaseOperations') as mock_db:
            mock_db_ops = MagicMock()
            mock_db_ops.get_conversation_history = AsyncMock(return_value=[])
            mock_db_ops.save_message = AsyncMock()
            mock_db.return_value = mock_db_ops
            
            # Mock CLI executor to raise error
            tool_manager.cli_executor.execute_command = AsyncMock(
                side_effect=Exception("Command failed")
            )
            
            # Mock the final LLM response after tool execution
            mock_final_response = MagicMock()
            mock_final_response.choices = [MagicMock()]
            mock_final_response.choices[0].message = MagicMock()
            mock_final_response.choices[0].message.content = "I encountered an error while trying to execute the command."
            tool_manager.llm_client.chat_completion.side_effect = [
                mock_response,  # First call with tool calls
                mock_final_response  # Second call for final response
            ]
            
            result = await tool_manager.process_user_request(
                123, 456, "test message", mock_db_ops
            )
            
            # Verify error handling
            assert isinstance(result, str)
            assert "error" in result.lower()
            tool_manager.cli_executor.execute_command.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unknown_tool_function(self, tool_manager):
        """Test handling of unknown tool functions."""
        # Mock tool calls with unknown function
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "unknown_function"
        mock_tool_call.function.arguments = '{"param": "value"}'
        mock_tool_call.id = "test_id"
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        tool_manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
        
        # Mock database operations
        with patch('src.aibotto.ai.tool_calling.DatabaseOperations') as mock_db:
            mock_db_ops = MagicMock()
            mock_db_ops.get_conversation_history = AsyncMock(return_value=[])
            mock_db_ops.save_message = AsyncMock()
            mock_db.return_value = mock_db_ops
            
            # Mock the final LLM response after tool execution
            mock_final_response = MagicMock()
            mock_final_response.choices = [MagicMock()]
            mock_final_response.choices[0].message = MagicMock()
            mock_final_response.choices[0].message.content = "I'm sorry, but I encountered an issue with the requested function."
            tool_manager.llm_client.chat_completion.side_effect = [
                mock_response,  # First call with tool calls
                mock_final_response  # Second call for final response
            ]
            
            result = await tool_manager.process_user_request(
                123, 456, "test message", mock_db_ops
            )
            
            # Verify unknown function handling
            assert isinstance(result, str)
            assert "unknown" in result.lower() or "issue" in result.lower()
    
    def test_factual_verification_edge_cases(self, tool_manager):
        """Test factual verification edge cases."""
        # Test with exact time
        exact_response = "The current time is exactly 14:30:00"
        exact_query = "what time is it"
        result = tool_manager._needs_factual_verification(exact_response, exact_query)
        assert result is False
        
        # Test with certain language
        certain_response = "The current time is precisely 2:30 PM"
        certain_query = "what time is it"
        result = tool_manager._needs_factual_verification(certain_response, certain_query)
        assert result is False
        
        # Test with non-factual uncertain response
        non_factual_uncertain = "I might be able to help you with that"
        non_factual_query = "how are you"
        result = tool_manager._needs_factual_verification(non_factual_uncertain, non_factual_query)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_fact_check_response_method(self, tool_manager):
        """Test fact_check_response method."""
        # Mock the executor
        tool_manager.cli_executor.execute_fact_check = AsyncMock(
            return_value="Fact-check completed"
        )
        
        result = await tool_manager.fact_check_response("test query", "test response")
        
        assert result == "Fact-check completed"
        tool_manager.cli_executor.execute_fact_check.assert_called_once_with(
            "test query", "test response"
        )
    
    @pytest.mark.asyncio
    async def test_process_user_request_general_error(self, tool_manager):
        """Test general error handling in process_user_request."""
        # Mock LLM to raise general error
        tool_manager.llm_client.chat_completion = AsyncMock(
            side_effect=Exception("General error")
        )
        
        # Mock database operations
        with patch('src.aibotto.ai.tool_calling.DatabaseOperations') as mock_db:
            mock_db_ops = MagicMock()
            mock_db_ops.get_conversation_history = AsyncMock(return_value=[])
            mock_db_ops.save_message = AsyncMock()
            mock_db.return_value = mock_db_ops
            
            result = await tool_manager.process_user_request(
                123, 456, "test message", mock_db_ops
            )
            
            # Verify error handling
            assert "error" in result.lower()