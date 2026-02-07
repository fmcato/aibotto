"""
Prompt templates for the AI system.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SystemPrompts:
    """System prompts for the AI assistant."""

    # Main system prompt - simplified and generic
    MAIN_SYSTEM_PROMPT = """You are a helpful AI assistant that can use CLI tools
    and web search to get factual information.

    When users ask for factual information like date/time, weather, system info,
    news, or web content, use the available tools to get accurate information.

    You have two types of tools available:
    1. CLI commands for system information (date, weather, files, etc.)
    2. Web search for current information, recent news, or topics not
       covered by CLI tools

    For web-related queries, current events, or when you need recent information,
    use the search_web tool. For system information, use CLI commands.

    Provide a helpful response based on the actual information you received.
    Don't mention the tool commands or technical details."""

    # Tool instructions
    TOOL_INSTRUCTIONS = """You have two types of tools available:

    1. CLI commands for system information:
       - Use for date/time, weather, system info, file operations
       - Examples: date, uname -a, ls -la, curl wttr.in/London?format=3

    2. Web search for current information:
       - Use for recent news, current events, or topics not covered by CLI tools
       - The search_web tool will extract content from web pages
       - You can specify number of results and time range (e.g., last 7 days)

    Choose the appropriate tool based on the user's request.
    For web-related queries, current events, or when you need recent information,
    use search_web. For system information, use CLI commands.
    - curl -A "Mozilla/5.0" https://example.com (for websites)"""

    # Fallback response
    FALLBACK_RESPONSE = """I don't have access to the specific tools needed
    for this request.

    I can help with:
    - Date and time queries
    - Weather information
    - System information
    - File and directory operations
    - Web content retrieval
    - News and information gathering"""

    @classmethod
    def get_conversation_prompt(
        cls, conversation_history: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Get the complete conversation prompt with system message."""
        messages = [
            {"role": "system", "content": cls.MAIN_SYSTEM_PROMPT},
            {"role": "system", "content": cls.TOOL_INSTRUCTIONS},
        ]

        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history)

        return messages


class ToolDescriptions:
    """Tool descriptions for the LLM."""

    CLI_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "execute_cli_command",
            "description": "Execute safe CLI commands to get factual information",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "The CLI command to execute. Choose an appropriate "
                            "command for the user's request."
                        ),
                    }
                },
                "required": ["command"],
            },
        },
    }

    WEB_SEARCH_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for current information using DuckDuckGo",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The search query. Use this for current information, "
                            "recent news, or topics not covered by CLI tools."
                        ),
                    },
                    "num_results": {
                        "type": "integer",
                        "description": (
                        "Maximum number of results to return "
                        "(1-10, default: 5)"
                    ),
                        "default": 5
                    },
                    "days_ago": {
                        "type": "integer",
                        "description": (
                            "Filter results from last N days (optional, "
                            "e.g., 7 for last week, 30 for last month)"
                        ),
                        "default": None
                    }
                },
                "required": ["query"],
            },
        },
    }

    @classmethod
    def get_tool_definitions(cls) -> list[dict[str, Any]]:
        """Get all available tool definitions."""
        return [cls.CLI_TOOL_DESCRIPTION, cls.WEB_SEARCH_TOOL_DESCRIPTION]


class ResponseTemplates:
    """Response templates for various scenarios."""

    UNCERTAIN_RESPONSE = "Let me get that information for you."
    NO_TOOL_AVAILABLE = (
        "I don't have access to the specific tools needed for this request."
    )

    ERROR_RESPONSE = "I encountered an error while trying to get information: {error}"
    SECURITY_BLOCKED = (
        "This command was blocked for security reasons. I can only execute safe "
        "CLI commands."
    )
