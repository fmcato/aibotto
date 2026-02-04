"""
Unit tests for factual response system.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.ai.prompt_templates import SystemPrompts, ToolDescriptions
from src.aibotto.cli.enhanced_executor import EnhancedCLIExecutor


class TestFactualResponses:
    """Test cases for factual response system."""
    
    @pytest.fixture
    def tool_manager(self):
        """Create a ToolCallingManager instance for testing."""
        with patch('src.aibotto.ai.tool_calling.LLMClient') as mock_llm:
            with patch('src.aibotto.ai.tool_calling.EnhancedCLIExecutor') as mock_executor:
                manager = ToolCallingManager()
                manager.llm_client = MagicMock()
                manager.cli_executor = MagicMock()
                return manager
    
    def test_system_prompt_structure(self):
        """Test that system prompts are properly structured."""
        messages = SystemPrompts.get_conversation_prompt([])
        
        # Should have system messages
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "system"
        
        # Should contain critical rules
        system_content = messages[0]["content"]
        assert "ALWAYS use available tools" in system_content
        assert "NEVER invent or hallucinate" in system_content
        assert "When uncertain about any factual information" in system_content
    
    def test_tool_descriptions(self):
        """Test that tool descriptions are enhanced."""
        tools = ToolDescriptions.get_tool_definitions()
        
        assert len(tools) == 1
        tool = tools[0]
        assert tool["function"]["name"] == "execute_cli_command"
        
        # Should include enhanced description
        description = tool["function"]["description"]
        assert "factual information" in description
        assert "ANY factual query" in description
    
    def test_uncertainty_detection(self, tool_manager):
        """Test detection of uncertain responses."""
        # Test uncertain response
        uncertain_response = "It's probably around 2 PM today"
        uncertain_query = "what time is it"
        
        result = tool_manager._needs_factual_verification(uncertain_response, uncertain_query)
        assert result is True
        
        # Test certain response
        certain_response = "The current time is 2:30 PM"
        certain_query = "what time is it"
        
        result = tool_manager._needs_factual_verification(certain_response, certain_query)
        assert result is False
        
        # Test non-factual query
        non_factual_response = "How are you today?"
        non_factual_query = "how are you"
        
        result = tool_manager._needs_factual_verification(non_factual_response, non_factual_query)
        assert result is False
    
    def test_factual_indicators(self, tool_manager):
        """Test detection of factual query indicators."""
        # Test factual query
        factual_query = "what time is it today"
        factual_response = "It might be around 2 PM"
        
        result = tool_manager._needs_factual_verification(factual_response, factual_query)
        assert result is True
        
        # Test non-factual query
        non_factual_query = "how are you"
        non_factual_response = "I'm doing well"
        
        result = tool_manager._needs_factual_verification(non_factual_response, non_factual_query)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_enhanced_command_suggestions(self):
        """Test enhanced command suggestion system."""
        executor = EnhancedCLIExecutor()
        
        # Test time query
        time_query = "what time is it"
        suggestion = executor.suggest_command(time_query)
        assert suggestion is not None
        assert suggestion.command == "date"
        assert suggestion.confidence == 0.9
        
        # Test weather query
        weather_query = "what's the weather like"
        suggestion = executor.suggest_command(weather_query)
        assert suggestion is not None
        assert "curl" in suggestion.command
        assert "wttr.in" in suggestion.command
        
        # Test system query
        system_query = "tell me about the system"
        suggestion = executor.suggest_command(system_query)
        assert suggestion is not None
        assert suggestion.command == "uname -a"
        
        # Test unknown query
        unknown_query = "tell me a joke"
        suggestion = executor.suggest_command(unknown_query)
        assert suggestion is None
    
    @pytest.mark.asyncio
    async def test_fact_check_response(self, tool_manager):
        """Test fact-check response functionality."""
        # Mock the executor
        tool_manager.cli_executor.execute_fact_check = AsyncMock(
            return_value="Fact-check result: Current time is 14:30"
        )
        
        result = await tool_manager.fact_check_response("what time is it", "it's probably 2 PM")
        assert "Fact-check result" in result
        tool_manager.cli_executor.execute_fact_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_factual_commands_info(self, tool_manager):
        """Test getting factual commands information."""
        # Mock the executor
        tool_manager.cli_executor.get_available_commands_info = AsyncMock(
            return_value="🛠️ Available commands: date, ls, uname -a"
        )
        
        result = await tool_manager.get_factual_commands_info()
        assert "Available commands" in result
        tool_manager.cli_executor.get_available_commands_info.assert_called_once()
    
    def test_prompt_templates_structure(self):
        """Test that prompt templates are properly structured."""
        # Test main system prompt
        main_prompt = SystemPrompts.MAIN_SYSTEM_PROMPT
        assert "CRITICAL RULES" in main_prompt
        assert "AVAILABLE TOOLS" in main_prompt
        assert "WHEN TO USE TOOLS" in main_prompt
        assert "RESPONSE STYLE" in main_prompt
        assert "EXAMPLES" in main_prompt
        
        # Test tool instructions
        tool_instructions = SystemPrompts.TOOL_INSTRUCTIONS
        assert "When using CLI tools" in tool_instructions
        assert "Common commands for different requests" in tool_instructions
        
        # Test fallback response
        fallback = SystemPrompts.FALLBACK_RESPONSE
        assert "I don't have access to the specific tools" in fallback
        assert "I can help you with" in fallback
    
    def test_response_templates(self):
        """Test response templates."""
        from src.aibotto.ai.prompt_templates import ResponseTemplates
        
        # Test tool execution success template
        success = ResponseTemplates.TOOL_EXECUTION_SUCCESS.format(
            command="date", output="Mon Feb 2 14:30:00 UTC 2026"
        )
        assert "Command executed: date" in success
        assert "Output:" in success
        
        # Test error response template
        error = ResponseTemplates.ERROR_RESPONSE.format(error="Connection failed")
        assert "I encountered an error while trying to get information: Connection failed" in error
        
        # Test uncertain response template
        uncertain = ResponseTemplates.UNCERTAIN_RESPONSE
        assert "Let me get that information" in uncertain