"""
Prompt templates for the AI system.
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class DateTimeContext:
    """Provides current date/time context for the LLM."""

    @classmethod
    def get_current_datetime_message(cls) -> dict[str, str]:
        """Get a system message with the current date and time.

        Returns:
            A system message dict with current date/time in ISO format.
        """
        now = datetime.now(UTC)
        # Format: 2025-01-15T14:30:00+00:00 Wednesday
        iso_format = now.isoformat()
        day_name = now.strftime("%A")

        return {
            "role": "system",
            "content": f"Current date and time: {iso_format} ({day_name}, UTC)"
        }


class SystemPrompts:
    """System prompts for the AI assistant."""

    # Main system prompt - simplified and generic
    MAIN_SYSTEM_PROMPT = """You are a helpful AI assistant that can use CLI tools
    and web tools to get factual information.

    When users ask for factual information like date/time, weather, system info,
    news, or web content, use the available tools to get accurate information.

    You have three types of tools available:
    1. CLI commands for system information (date, weather, files, etc.)
    2. Web search for finding information on the web
    3. Web fetch for reading the full content of a specific URL

    For web-related queries, current events, or when you need recent information,
    use the search_web tool. When you have a specific URL and want to read its
    content, use the fetch_webpage tool. For system information, use CLI commands.

    Provide a helpful response based on the actual information you received.
    Don't mention the tool commands or technical details."""

    # Default max turns (can be overridden)
    DEFAULT_MAX_TURNS = 5

    @classmethod
    def get_tool_instructions(cls, max_turns: int = 10) -> str:
        """Get tool instructions with dynamic turn limit.

        Args:
            max_turns: Maximum number of tool-calling turns allowed

        Returns:
            Tool instructions string with turn limit
        """
        return f"""You have three types of tools available:

    1. CLI commands for system information:
       - Use for date/time, system info, file operations, calculations
       - Examples: date, uname -a, ls -la, python3 -c "print(2**10)"

    2. Web search for finding information:
       - Use for recent news, current events, weather, and topics not in CLI tools
       - Returns search results with snippets
       - You can specify number of results and time range (e.g., last 7 days)

    3. Web fetch for reading specific URLs:
       - Use when you have a specific URL and want to read its full content
       - Extracts readable text from web pages (not HTML code)
       - Useful for reading articles, blog posts, documentation pages

    IMPORTANT GUIDELINES:
    - Do NOT call the same tool with the same parameters multiple times
    - Do NOT fetch the same URL more than once
    - If a tool result is not useful, try a DIFFERENT approach instead of repeating
    - Start with web search for news/current events, then fetch specific URLs if needed
    - Provide your best answer based on available information, even if incomplete

    You have a maximum of {max_turns} tool-calling turns to complete your task.
    Provide a final answer within this limit."""

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
    def get_base_prompt(cls, max_turns: int = 10) -> list[dict[str, str]]:
        """Get the base system prompt without conversation history.

        Args:
            max_turns: Maximum number of tool-calling turns allowed

        Returns:
            List of system message dicts
        """
        return [
            {"role": "system", "content": cls.MAIN_SYSTEM_PROMPT},
            {"role": "system", "content": cls.get_tool_instructions(max_turns)},
            DateTimeContext.get_current_datetime_message(),
        ]

    @classmethod
    def get_conversation_prompt(
        cls, conversation_history: list[dict[str, str]], max_turns: int = 10
    ) -> list[dict[str, str]]:
        """Get the complete conversation prompt with system message.

        Args:
            conversation_history: List of previous conversation messages
            max_turns: Maximum number of tool-calling turns allowed

        Returns:
            List of message dicts including system prompt and history
        """
        messages = cls.get_base_prompt(max_turns)

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

    WEB_FETCH_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": (
                "Fetch and extract readable text content from a specific URL. "
                "Use this when you have a URL and want to read its full content. "
                "Returns the page title, content, and metadata."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The URL to fetch. Must start with http:// or https://"
                        ),
                    },
                    "max_length": {
                        "type": "integer",
                        "description": (
                            "Maximum content length to return in characters "
                            "(default: 10000)"
                        ),
                        "default": 10000,
                    },
                    "include_links": {
                        "type": "boolean",
                        "description": (
                            "Whether to include link URLs in the output "
                            "(default: false)"
                        ),
                        "default": False,
                    },
                },
                "required": ["url"],
            },
        },
    }

    @classmethod
    def get_tool_definitions(cls) -> list[dict[str, Any]]:
        """Get all available tool definitions."""
        return [
            cls.CLI_TOOL_DESCRIPTION,
            cls.WEB_SEARCH_TOOL_DESCRIPTION,
            cls.WEB_FETCH_TOOL_DESCRIPTION,
        ]


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
