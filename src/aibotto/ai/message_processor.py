"""
Message processing utilities for LLM tool calling.
"""

from typing import Any


class MessageProcessor:
    """Utility class for processing LLM messages and tool calls."""

    @staticmethod
    def extract_tool_call_info(
        tool_call: Any
    ) -> tuple[str | None, str | None, str | None]:
        """Extract tool call ID, function name, and arguments from a tool call.

        Args:
            tool_call: Tool call object (dict or object format)

        Returns:
            Tuple of (tool_call_id, function_name, arguments)
        """
        if isinstance(tool_call, dict):
            return (
                tool_call.get("id"),
                tool_call.get("function", {}).get("name"),
                tool_call.get("function", {}).get("arguments"),
            )
        else:
            has_func = hasattr(tool_call, "function")
            return (
                getattr(tool_call, "id", None),
                getattr(tool_call.function, "name", None) if has_func else None,
                getattr(tool_call.function, "arguments", None) if has_func else None,
            )

    @staticmethod
    def extract_response_content(message_obj: Any) -> str:
        """Extract content from a message object.

        Args:
            message_obj: Message object (dict or object format)

        Returns:
            Message content as string
        """
        if isinstance(message_obj, dict):
            return message_obj.get("content", "") or ""
        else:
            return getattr(message_obj, "content", "") or ""

    @staticmethod
    def extract_tool_calls_from_response(message_obj: Any) -> list[Any] | None:
        """Extract tool calls from a message object.

        Args:
            message_obj: Message object (dict or object format)

        Returns:
            List of tool calls or None
        """
        if not isinstance(message_obj, dict):
            return None

        tool_calls = message_obj.get("tool_calls")
        if tool_calls is None or len(tool_calls) == 0:
            return None

        # Ensure tool_calls is a list
        if isinstance(tool_calls, dict):
            return [tool_calls]
        return list(tool_calls) if tool_calls else None
