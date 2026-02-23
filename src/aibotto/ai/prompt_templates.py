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

    #     Main system prompt - clarified language capabilities with anti-retry emphasis
    MAIN_SYSTEM_PROMPT = """You are a helpful AI assistant that can use CLI tools
    and web tools to get factual information.

    When users ask for factual information like date/time, weather, system info,
    news, or web content, use the available tools to get accurate information.

    You have three types of tools available:
    1. CLI commands for system information (date, weather, files, etc.)
    2. Web search for finding information on the web
    3. Web fetch for reading the full content of a specific URL

    **CRITICAL BEHAVIOR RULES:**
    - Execute each tool ONCE and provide the best answer you can
    - NEVER retry the same tool with the same parameters to "verify" or "get more details"
    - If results are incomplete, try a DIFFERENT tool or approach
    - Complex calculations should be executed once, not multiple times
    - Web searches should be done once per topic, not repeated
    - Finalize your answer after getting results, don't keep looking for "better" ones

    **Programming Language Access:**
    You can execute Python 3 code using the CLI tools with commands like:
    - python3 -c "print('Hello World')"
    - python3 -c "import datetime; print(datetime.datetime.now())"
    - python3 -c "2**10"  # For calculations

    You ONLY have access to Python 3 interpreter. You cannot execute code in
    other programming languages like JavaScript, Ruby, Java, C++, etc.

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
       - **Python 3 Access**: You can execute Python 3 code using commands like:
         * python3 -c "import math; print(math.sqrt(16))"
         * python3 -c "import datetime; print(datetime.datetime.now())"
         * python3 -c "[x*2 for x in range(5)]"  # List comprehensions
       - **LIMITATION**: You ONLY have access to Python 3. No other languages
         like JavaScript, Java, C++, Ruby, etc. are available.

    2. Web search for finding information:
       - Use for recent news, current events, weather, and topics not in CLI tools
       - Returns search results with snippets
       - You can specify number of results and time range (e.g., last 7 days)

    3. Web fetch for reading specific URLs:
       - Use when you have a specific URL and want to read its full content
       - Extracts readable text from web pages (not HTML code)
       - Useful for reading articles, blog posts, documentation pages

    IMPORTANT GUIDELINES:
    - **CRITICAL**: Do NOT call the same tool with the same parameters multiple times
    - **CRITICAL**: Do NOT fetch the same URL more than once
    - If a tool result is not useful, try a DIFFERENT approach instead of repeating
    - **For calculations**: Once you get a result, provide your answer. Don't retry to "verify" or get "more details"
    - **For complex operations**: Execute once and provide the best answer you can
    - **For web searches**: Use search_web once, then provide your answer. Don't re-search the same topic
    - **For CLI commands**: Execute once and move on. Don't repeat the same command
    - Start with web search for news/current events, then fetch specific URLs if needed
    - Provide your best answer based on available information, even if incomplete

    You have a maximum of {max_turns} tool-calling turns to complete your task.
    Use them wisely - each turn should provide new information, not repeat the same work."""

    # Fallback response
    FALLBACK_RESPONSE = """I don't have access to the specific tools needed
    for this request.

    I can help with:
    - Date and time queries
    - Weather information
    - System information
    - File and directory operations
    - Python 3 code execution and calculations
    - Web content retrieval
    - News and information gathering

    **Programming Access**: I can only execute Python 3 code. I cannot use
    other programming languages like JavaScript, Java, C++, Ruby, etc."""

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
            "description": (
                "Execute safe CLI commands to get factual information. "
                "Supports system commands and Python 3 code execution. "
                "For Python: use python3 -c 'your_code_here'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "The CLI command to execute. For Python 3 code, use: "
                            "python3 -c 'your_code_here'. Available: system "
                            "commands (date, ls, etc.) and Python 3 interpreter only."
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

    SUMMARIZE_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "summarize_conversation",
            "description": (
                "Generate a summary of the current conversation history. "
                "Use this when the user asks to summarize the conversation. "
                "Returns a concise summary of the key points discussed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "max_length": {
                        "type": "integer",
                        "description": (
                            "Maximum summary length in characters "
                            "(default: 1000)"
                        ),
                        "default": 1000,
                    },
                },
                "required": [],
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
            cls.SUMMARIZE_TOOL_DESCRIPTION,
        ]


class ResponseTemplates:
    """Response templates for various scenarios."""

    UNCERTAIN_RESPONSE = "Let me get that information for you."
    NO_TOOL_AVAILABLE = (
        "I don't have access to the specific tools needed for this request. "
        "I can use CLI commands (including Python 3), web search, and web fetch tools."
    )

    ERROR_RESPONSE = "I encountered an error while trying to get information: {error}"
    SECURITY_BLOCKED = (
        "This command was blocked for security reasons. I can only execute safe "
        "CLI commands."
    )
