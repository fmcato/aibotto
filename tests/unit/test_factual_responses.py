"""
Unit tests for factual response system.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aibotto.ai.prompt_templates import SystemPrompts, ToolDescriptions
from src.aibotto.ai.tool_calling import ToolCallingManager


class TestFactualResponses:
    """Test cases for factual response system."""

    @pytest.fixture
    def tool_manager(self):
        """Create a ToolCallingManager instance for testing."""
        with patch('src.aibotto.ai.tool_calling.LLMClient') as mock_llm:
            with patch('src.aibotto.ai.tool_calling.CLIExecutor') as mock_executor:
                mock_llm.return_value = AsyncMock()
                mock_executor.return_value = AsyncMock()

                manager = ToolCallingManager()
                manager.llm_client = mock_llm.return_value
                manager.cli_executor = mock_executor.return_value

                yield manager

    def test_system_prompts_structure(self):
        """Test that system prompts are properly structured."""
        # Test main system prompt
        assert "helpful AI assistant" in SystemPrompts.MAIN_SYSTEM_PROMPT
        assert "CLI tools" in SystemPrompts.MAIN_SYSTEM_PROMPT

        # Test tool instructions
        assert "curl" in SystemPrompts.TOOL_INSTRUCTIONS
        assert "CLI commands" in SystemPrompts.TOOL_INSTRUCTIONS
        assert "Web search" in SystemPrompts.TOOL_INSTRUCTIONS

        # Test fallback response
        assert "don't have access" in SystemPrompts.FALLBACK_RESPONSE

    def test_tool_descriptions(self):
        """Test that tool descriptions are properly structured."""
        tools = ToolDescriptions.get_tool_definitions()
        assert len(tools) == 2

        # Check that both CLI and web search tools are present
        tool_names = [tool["function"]["name"] for tool in tools]
        assert "execute_cli_command" in tool_names
        assert "search_web" in tool_names
        assert "safe CLI commands" in tool["function"]["description"]

    @pytest.mark.asyncio
    async def test_direct_response_handling(self, tool_manager):
        """Test handling of direct responses without tool calls."""
        # Mock LLM response without tool calls
        tool_manager.llm_client.chat_completion.return_value = AsyncMock()
        tool_manager.llm_client.chat_completion.return_value.choices = [
            MagicMock(message=MagicMock(content="Today is Monday.", tool_calls=None))
        ]

        # Mock database operations
        with patch('src.aibotto.ai.tool_calling.DatabaseOperations') as mock_db:
            mock_db.return_value = AsyncMock()
            mock_db.return_value.get_conversation_history.return_value = []
            mock_db.return_value.save_message.return_value = None

            # Process a simple message
            response = await tool_manager.process_user_request(
                user_id=123, chat_id=456, message="What day is it?", db_ops=mock_db.return_value
            )

            # Should return direct response
            assert "Today is Monday" in response
            # Should not have called execute_command
            tool_manager.cli_executor.execute_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_tool_call_execution(self, tool_manager):
        """Test execution of tool calls."""
        # Mock LLM response with tool calls
        mock_response = AsyncMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function = MagicMock()
        mock_response.choices[0].message.tool_calls[0].function.name = "execute_cli_command"
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"command": "date"}'
        mock_response.choices[0].message.tool_calls[0].id = "test_id"

        # Mock second call (after tool execution)
        mock_final_response = AsyncMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message = MagicMock()
        mock_final_response.choices[0].message.content = "Today is Monday."

        # Set up side effect for the second call
        tool_manager.llm_client.chat_completion.side_effect = [mock_response, mock_final_response]

        # Mock command execution result
        tool_manager.cli_executor.execute_command.return_value = "Mon Feb  3 10:30:45 UTC 2026"

        # Mock database operations
        with patch('src.aibotto.ai.tool_calling.DatabaseOperations') as mock_db:
            mock_db.return_value = AsyncMock()
            mock_db.return_value.get_conversation_history.return_value = []
            mock_db.return_value.save_message.return_value = None

            # Process a message that requires tool usage
            response = await tool_manager.process_user_request(
                user_id=123, chat_id=456, message="What day is it?", db_ops=mock_db.return_value
            )

            # Should return processed response
            assert "Today is Monday" in response
            # Should have called execute_command
            tool_manager.cli_executor.execute_command.assert_called_once_with("date")

    @pytest.mark.asyncio
    async def test_factual_verification_trigger(self, tool_manager):
        """Test when factual verification is triggered."""
        # Test case 1: Uncertain response with factual query
        uncertain_response = "It's probably around 2 PM"
        factual_query = "what time is it"
        assert tool_manager._needs_factual_verification(uncertain_response, factual_query) == True

        # Test case 2: Certain response with factual query
        certain_response = "The current time is 2:30 PM"
        assert tool_manager._needs_factual_verification(certain_response, factual_query) == False

        # Test case 3: Non-factual query
        non_factual_response = "I think the weather is nice"
        non_factual_query = "how are you"
        assert tool_manager._needs_factual_verification(non_factual_response, non_factual_query) == False

    @pytest.mark.asyncio
    async def test_get_factual_commands_info(self, tool_manager):
        """Test getting factual commands information."""
        result = await tool_manager.get_factual_commands_info()
        assert "factual information" in result

    @pytest.mark.asyncio
    async def test_fact_check_response(self, tool_manager):
        """Test fact-checking a response."""
        result = await tool_manager.fact_check_response("what time is it", "it's probably 2 PM")
        assert "verify this information" in result
