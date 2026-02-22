"""
Unit tests for factual response system.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.aibotto.ai.prompt_templates import SystemPrompts, ToolDescriptions
from src.aibotto.ai.tool_calling import ToolCallingManager


class TestFactualResponses:
    """Test cases for factual response system."""

    @pytest.fixture
    def tool_manager(self):
        """Create a ToolCallingManager instance for testing."""
        with patch('src.aibotto.ai.tool_calling.LLMClient') as mock_llm:
            mock_llm.return_value = AsyncMock()
            
            manager = ToolCallingManager()
            manager.llm_client = mock_llm.return_value

            # Get the CLI executor from the tool registry and configure it
            from src.aibotto.tools.tool_registry import tool_registry
            cli_executor = tool_registry.get_executor("execute_cli_command")
            if cli_executor:
                cli_executor.execute = AsyncMock(return_value="Mock command output")

            yield manager

    def test_system_prompts_structure(self):
        """Test that system prompts are properly structured."""
        # Test main system prompt
        assert "helpful AI assistant" in SystemPrompts.MAIN_SYSTEM_PROMPT
        assert "CLI tools" in SystemPrompts.MAIN_SYSTEM_PROMPT

        # Test tool instructions (now a method)
        tool_instructions = SystemPrompts.get_tool_instructions()
        assert "python3" in tool_instructions
        assert "CLI commands" in tool_instructions
        assert "Web search" in tool_instructions

        # Test fallback response
        assert "don't have access" in SystemPrompts.FALLBACK_RESPONSE

    def test_tool_descriptions(self):
        """Test that tool descriptions are properly structured."""
        tools = ToolDescriptions.get_tool_definitions()
        assert len(tools) == 4

        # Check that all tools are present
        tool_names = [tool["function"]["name"] for tool in tools]
        assert "execute_cli_command" in tool_names
        assert "search_web" in tool_names
        assert "fetch_webpage" in tool_names

        # Check that CLI tool description mentions safe commands
        for tool in tools:
            if tool["function"]["name"] == "execute_cli_command":
                assert "safe CLI commands" in tool["function"]["description"]
                break

        # Check that fetch_webpage tool has required parameters
        for tool in tools:
            if tool["function"]["name"] == "fetch_webpage":
                assert "url" in tool["function"]["parameters"]["required"]
                break

    @pytest.mark.asyncio
    async def test_direct_response_handling(self, tool_manager):
        """Test handling of direct responses without tool calls."""
        # Mock LLM response without tool calls - return a dictionary like the real API
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "Today is Monday.",
                        "tool_calls": None
                    }
                }
            ]
        }

        # Mock the chat_completion method to return our mock response
        async def mock_chat_completion(*args, **kwargs):
            return mock_response

        tool_manager.llm_client.chat_completion = mock_chat_completion

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

    @pytest.mark.asyncio
    async def test_tool_call_execution(self, tool_manager):
        """Test execution of tool calls."""
        # Test that CLI executor can execute commands directly
        # Since the CLI executor is mocked, we'll test that it was called correctly
        test_command = "date"
        
        # Get the CLI executor from the tool registry
        from src.aibotto.tools.tool_registry import tool_registry
        cli_executor = tool_registry.get_executor("execute_cli_command")
        
        # Skip test if CLI executor is not available
        if not cli_executor:
            pytest.skip("CLI executor not available")
            
        # Execute the command
        result = await cli_executor.execute('{"command": "' + test_command + '"}', user_id=123)

        # Should return a string (the mock result)
        assert isinstance(result, str)
        assert len(result) > 0

        # Test that the command was executed successfully
        assert "command not found" not in result.lower()

    @pytest.mark.asyncio
    async def test_factual_verification_trigger(self, tool_manager):
        """Test when factual verification is triggered."""
        # Import the FactChecker directly since it's no longer in ToolCallingManager
        from src.aibotto.ai.fact_checker import FactChecker
        
        # Test case 1: Uncertain response with factual query
        uncertain_response = "It's probably around 2 PM"
        factual_query = "what time is it"
        assert FactChecker.needs_factual_verification(uncertain_response, factual_query) == True

        # Test case 2: Certain response with factual query
        certain_response = "The current time is 2:30 PM"
        assert FactChecker.needs_factual_verification(certain_response, factual_query) == False

        # Test case 3: Non-factual query
        non_factual_response = "I think the weather is nice"
        non_factual_query = "how are you"
        from src.aibotto.ai.fact_checker import FactChecker
        assert FactChecker.needs_factual_verification(non_factual_response, non_factual_query) == False

    @pytest.mark.asyncio
    async def test_get_factual_commands_info(self, tool_manager):
        """Test getting factual commands information."""
        from src.aibotto.ai.fact_checker import FactChecker
        result = await FactChecker.get_factual_commands_info()
        assert "factual information" in result

    @pytest.mark.asyncio
    async def test_fact_check_response(self, tool_manager):
        """Test fact-checking a response."""
        from src.aibotto.ai.fact_checker import FactChecker
        result = await FactChecker.fact_check_response("what time is it", "it's probably 2 PM")
        assert "verify this information" in result
