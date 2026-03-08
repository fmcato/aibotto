"""
Base interfaces for tool executors.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Protocol


class ToolExecutionError(Exception):
    """Exception raised during tool execution."""


class ToolExecutor(ABC):
    """Abstract base class for tool executors with template method pattern."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__module__)

    async def execute(
        self, arguments: str, user_id: int = 0, db_ops: Any = None, chat_id: int = 0
    ) -> str:
        """Execute the tool with arguments.

        Args:
            arguments: JSON string of arguments
            user_id: User ID for logging
            db_ops: Database operations for saving results (optional, positional)
            chat_id: Chat ID for database operations (optional)

        Returns:
            Tool execution result as string
        """
        try:
            args = self._parse_arguments(arguments)
            result = await self._do_execute(args, user_id, chat_id, db_ops)
            await self._save_if_needed(db_ops, user_id, chat_id, result)
            return result
        except Exception as e:
            error_msg = str(e)
            await self._save_if_needed(db_ops, user_id, chat_id, error_msg)
            return error_msg

    def _parse_arguments(self, arguments: str) -> dict:
        """Parse JSON arguments with error handling.

        Args:
            arguments: JSON string of arguments

        Returns:
            Parsed arguments as dictionary

        Raises:
            ToolExecutionError: If JSON parsing fails
        """
        try:
            return json.loads(arguments)
        except json.JSONDecodeError as e:
            raise ToolExecutionError(f"Error parsing arguments: {e}")

    async def _save_if_needed(
        self, db_ops: Any, user_id: int, chat_id: int, content: str
    ) -> None:
        """Save result to database if db_ops is provided.

        Args:
            db_ops: Database operations instance (optional)
            user_id: User ID for logging
            chat_id: Chat ID for database operations
            content: Content to save
        """
        if db_ops:
            await db_ops.save_message_compat(
                user_id=user_id, chat_id=chat_id, role="system", content=content
            )

    @abstractmethod
    async def _do_execute(
        self, args: dict, user_id: int, chat_id: int = 0, db_ops: Any = None
    ) -> str:
        """Implement in subclass: actual execution logic.

        Args:
            args: Parsed arguments dictionary
            user_id: User ID for logging
            chat_id: Chat ID for database operations
            db_ops: Database operations (optional)

        Returns:
            Tool execution result as string

        Raises:
            ToolExecutionError: For expected execution errors
        """
        pass


class ToolExecutorFactory(Protocol):
    """Protocol for creating tool executors."""

    def get_executor(self, tool_name: str) -> ToolExecutor | None:
        """Get an executor for a specific tool name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool executor instance or None
        """
        pass
