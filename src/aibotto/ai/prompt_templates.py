"""
System prompts and tool definitions for the AIBot.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class SystemPrompts:
    """System prompts for the AI assistant."""

    # Main system prompt - simplified and generic
    MAIN_SYSTEM_PROMPT = """You are a helpful AI assistant that can use CLI tools to get factual information.

When users ask for factual information like date/time, weather, system info, news, or web content, use the available tools to get accurate information.

After getting tool results, provide a natural, helpful response based on the actual information you received. Don't mention the tool commands or technical details.

Keep responses concise and focused on what the user actually asked for."""

    # Simple tool instructions
    TOOL_INSTRUCTIONS = """You can execute safe CLI commands to get factual information.

For web requests, use curl with silent mode (-s) and a browser-like user agent to avoid being blocked.

Examples:
- Date/time: `date`
- Weather: `curl -s wttr.in?format=3`
- News/websites: `curl -s -A \"Mozilla/5.0\" https://www.cnn.com`
- System info: `uname -a`, `ls -la`

Use simple, direct commands that match what the user is asking for."""

    # Fallback response
    FALLBACK_RESPONSE = """I don't have access to the specific tools needed for this request.

I can help with:
- Current date and time
- File system information
- System details
- Weather information
- News and web content

For other questions, please use appropriate tools or consult relevant sources."""

    @classmethod
    def get_conversation_prompt(cls, conversation_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Get the complete conversation prompt with system message."""
        messages = [
            {"role": "system", "content": cls.MAIN_SYSTEM_PROMPT},
            {"role": "system", "content": cls.TOOL_INSTRUCTIONS}
        ]
        messages.extend(conversation_history)
        return messages


class ToolDescriptions:
    """Tool descriptions."""

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
                        "description": "The CLI command to execute. Choose an appropriate command for the user's request.",
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
    """Templates for common response types."""

    TOOL_EXECUTION_SUCCESS = "Command executed: {command}\nOutput:\n{output}"
    TOOL_EXECUTION_ERROR = "Command failed: {command}\nError: {error}"

    FACTUAL_RESPONSE = "{result}"
    WEATHER_RESPONSE = "Weather: {result}"
    TIME_RESPONSE = "Current time and date: {result}"

    UNCERTAIN_RESPONSE = "Let me get that information for you."
    NO_TOOL_AVAILABLE = "I don't have access to the specific tools needed for this request."

    ERROR_RESPONSE = "I encountered an error while trying to get information: {error}"
    SECURITY_BLOCKED = "This command was blocked for security reasons. I can only execute safe CLI commands."