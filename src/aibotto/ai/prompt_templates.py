"""
Prompt templates for the AI system.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class SystemPrompts:
    """System prompts for the AI assistant."""

    # Main system prompt - simplified and generic
    MAIN_SYSTEM_PROMPT = """You are a helpful AI assistant that can use CLI tools
    to get factual information.

    When users ask for factual information like date/time, weather, system info,
    news, or web content, use the available tools to get accurate information.

    Provide a helpful response based on the actual information you received.
    Don't mention the tool commands or technical details."""

    # Tool instructions
    TOOL_INSTRUCTIONS = """You can execute safe CLI commands to get factual
    information.

    For web requests, use curl with silent mode (-s) and a browser-like user
    agent to avoid being blocked.

    Examples:
    - curl wttr.in/London?format=3 (for weather)
    - curl -s "https://api.example.com/data" (for API calls)
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
        cls, conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
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

    @classmethod
    def get_tool_definitions(cls) -> List[Dict]:
        """Get all available tool definitions."""
        return [cls.CLI_TOOL_DESCRIPTION]


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