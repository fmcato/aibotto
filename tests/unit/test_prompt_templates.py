"""
Test prompt templates module.
"""

import pytest

from src.aibotto.ai.prompt_templates import (
    DateTimeContext,
    SystemPrompts,
    ToolDescriptions,
)


class TestSystemPrompts:
    """Test SystemPrompts class methods."""

    def test_main_system_prompt_includes_credibility_guidelines(self):
        """Test that MAIN_SYSTEM_PROMPT includes source credibility guidelines."""
        prompt = SystemPrompts.MAIN_SYSTEM_PROMPT

        # Check for key credibility concepts
        assert "Source Credibility Guidelines" in prompt
        assert "High-Credibility Sources" in prompt
        assert ".edu" in prompt
        assert ".gov" in prompt
        assert "ai-generated" in prompt.lower()

    def test_tool_instructions_includes_web_search_credibility(self):
        """Test that get_tool_instructions includes web research credibility rules."""
        instructions = SystemPrompts.get_tool_instructions()

        # Check for web research credibility rules (subagent handles credibility evaluation)
        # Main agent is now instructed to use research_topic for discovering information
        assert "research_topic" in instructions or "research" in instructions.lower()
        assert "fetch_webpage" in instructions

    def test_tool_instructions_includes_turn_limit(self):
        """Test that get_tool_instructions includes dynamic turn limit."""
        instructions_5 = SystemPrompts.get_tool_instructions(max_turns=5)
        instructions_10 = SystemPrompts.get_tool_instructions(max_turns=10)

        assert "maximum of 5" in instructions_5
        assert "maximum of 10" in instructions_10

    def test_get_base_prompt_structure(self):
        """Test that get_base_prompt returns correct structure."""
        base_prompt = SystemPrompts.get_base_prompt()

        assert isinstance(base_prompt, list)
        assert len(base_prompt) == 3

        for message in base_prompt:
            assert "role" in message
            assert message["role"] == "system"
            assert isinstance(message["content"], str)

    def test_get_base_prompt_includes_all_components(self):
        """Test that base prompt includes all required components."""
        base_prompt = SystemPrompts.get_base_prompt()
        combined_content = "\n".join(msg["content"] for msg in base_prompt)

        # Check for all major components
        assert "Source Credibility Guidelines" in combined_content
        assert "CLI commands" in combined_content
        assert "Web search" in combined_content
        assert "Current date and time" in combined_content

    def test_get_conversation_prompt_includes_history(self):
        """Test that get_conversation_prompt includes conversation history."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        messages = SystemPrompts.get_conversation_prompt(history)

        assert len(messages) == 5
        assert messages[3] == history[0]
        assert messages[4] == history[1]

    def test_get_conversation_prompt_empty_history(self):
        """Test that get_conversation_prompt handles empty history."""
        messages = SystemPrompts.get_conversation_prompt([])

        assert len(messages) == 3
        for message in messages:
            assert message["role"] == "system"


class TestToolDescriptions:
    """Test ToolDescriptions class."""

    def test_web_search_description_includes_credibility_warning(self):
        """Test that web search tool description mentions credibility."""
        description = ToolDescriptions.WEB_SEARCH_TOOL_DESCRIPTION

        function_details = description["function"]
        desc_text = function_details["description"]

        assert "credibility" in desc_text.lower()
        assert "authoritative" in desc_text.lower()
        assert "ai-generated" in desc_text.lower()
        assert "cross-check" in desc_text.lower()

    def test_tool_definitions_includes_all_tools(self):
        """Test that get_tool_definitions returns all tools."""
        definitions = ToolDescriptions.get_tool_definitions()

        assert len(definitions) == 3

        tool_names = [tool["function"]["name"] for tool in definitions]
        assert "execute_cli_command" in tool_names
        assert "research_topic" in tool_names
        assert "fetch_webpage" in tool_names

    def test_cli_tool_structure(self):
        """Test CLI tool definition structure."""
        tool = ToolDescriptions.CLI_TOOL_DESCRIPTION

        assert tool["type"] == "function"
        assert tool["function"]["name"] == "execute_cli_command"
        assert "command" in tool["function"]["parameters"]["properties"]
        assert "command" in tool["function"]["parameters"]["required"]

    def test_research_tool_structure(self):
        """Test research tool definition structure."""
        tool = ToolDescriptions.RESEARCH_TOOL_DESCRIPTION

        assert tool["type"] == "function"
        assert tool["function"]["name"] == "research_topic"
        assert "query" in tool["function"]["parameters"]["properties"]
        assert "query" in tool["function"]["parameters"]["required"]
        assert "num_results" in tool["function"]["parameters"]["properties"]
        assert tool["function"]["parameters"]["properties"]["num_results"]["default"] == 5

    def test_web_fetch_tool_structure(self):
        """Test web fetch tool definition structure."""
        tool = ToolDescriptions.WEB_FETCH_TOOL_DESCRIPTION

        assert tool["type"] == "function"
        assert tool["function"]["name"] == "fetch_webpage"
        assert "url" in tool["function"]["parameters"]["properties"]
        assert "url" in tool["function"]["parameters"]["required"]
        assert "max_length" in tool["function"]["parameters"]["properties"]
        assert "no_citations" in tool["function"]["parameters"]["properties"]


class TestDateTimeContext:
    """Test DateTimeContext class."""

    def test_get_current_datetime_message_structure(self):
        """Test that datetime message has correct structure."""
        message = DateTimeContext.get_current_datetime_message()

        assert message["role"] == "system"
        assert isinstance(message["content"], str)
        assert "Current date and time:" in message["content"]
        assert "UTC" in message["content"]

    def test_get_current_datetime_message_format(self):
        """Test that datetime message includes ISO format."""
        message = DateTimeContext.get_current_datetime_message()

        assert "T" in message["content"]
        assert ":" in message["content"]
