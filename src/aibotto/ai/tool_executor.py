"""
Tool execution orchestration functionality.
"""

import asyncio
import logging
import time
from typing import Any

from ..db.operations import DatabaseOperations
from ..tools.tool_registry import tool_registry
from .message_processor import MessageProcessor
from .tool_tracker import ToolTracker

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Orchestrates tool execution with logging and error handling."""

    def __init__(self) -> None:
        self.tracker = ToolTracker()
        
        # Register tool executors
        self._register_tools()

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for the LLM."""
        from .prompt_templates import ToolDescriptions
        return ToolDescriptions.get_tool_definitions()

    def _register_tools(self) -> None:
        """Register tool executors with the registry."""
        from ..tools.executors.cli_executor import CLIExecutor
        from ..tools.executors.web_fetch_executor import WebFetchExecutor
        from ..tools.executors.web_search_executor import WebSearchExecutor

        # Register executors
        tool_registry.register_executor("execute_cli_command", CLIExecutor())
        tool_registry.register_executor("search_web", WebSearchExecutor())
        tool_registry.register_executor("fetch_webpage", WebFetchExecutor())

        logger.info("Registered all tool executors")

    def get_executor(self, function_name: str):
        """Get executor for a specific tool function."""
        return tool_registry.get_executor(function_name)

    async def execute_single_tool(
        self,
        function_name: str | None,
        arguments: str | None,
        user_id: int = 0,
        db_ops: DatabaseOperations | None = None,
        chat_id: int = 0,
    ) -> str:
        """Execute a single tool and return the result.

        Args:
            function_name: Name of the tool function to execute
            arguments: JSON string of arguments
            user_id: User ID for logging (optional)
            db_ops: Database operations for saving results (optional)
            chat_id: Chat ID for database operations (optional)

        Returns:
            Tool execution result as string
        """
        start_time = time.time()

        if function_name is None:
            error_result = "No function name provided"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result

        if arguments is None:
            arguments = "{}"

        # Check for duplicate tool calls
        if self.tracker.is_duplicate_tool_call(function_name, arguments, user_id, chat_id):
            # Return early for duplicates to prevent infinite loops
            logger.warning(f"Skipping duplicate tool call: {function_name}")
            return (
                f"⚠️ Tool call '{function_name}' already executed in this "
                f"conversation. Skipping to prevent infinite loops."
            )

        # Track this call in recent calls
        self.tracker.track_tool_call(function_name, arguments)

        # Check for similar tool calls that might indicate retry logic issues
        if self.tracker.is_similar_tool_call(function_name, arguments, user_id, chat_id):
            logger.info(f"Implementing smart retry prevention for {function_name}")
            # For complex calculations, suggest optimization instead of retry
            if "python3" in arguments.lower() and "calc" in arguments.lower():
                return (
                    "🔄 I already attempted a similar calculation. Let me try a "
                    "different approach or provide you with what I found so far."
                )

        # Check if this call should be prevented due to retry patterns
        if self.tracker.should_prevent_retry(function_name, arguments, user_id, chat_id):
            logger.warning(
                f"Preventing retry of {function_name} - detected unnecessary "
                "retry pattern"
            )
            return (
                "🚫 I've already attempted this type of operation multiple "
                "times. Let me try a different approach or provide you with the "
                "results I have so far."
            )

        # Get executor from registry
        executor = self.get_executor(function_name)
        if not executor:
            error_result = f"Unknown tool function: {function_name}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result

        try:
            logger.info(
                f"Starting tool execution: {function_name} for user {user_id}, "
                f"chat {chat_id}, iteration {self.tracker._iteration_count}"
            )

            result = await executor.execute(arguments, user_id, db_ops, chat_id)
            execution_time = time.time() - start_time

            logger.info(
                f"Tool {function_name} completed in {execution_time:.2f}s for "
                f"user {user_id}: {result[:200]}..."
            )

            # Log slow executions (> 10 seconds)
            if execution_time > 10:
                logger.warning(
                    f"SLOW TOOL EXECUTION: {function_name} took {execution_time:.2f}s "
                    f"for user {user_id}, chat {chat_id}"
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Tool {function_name} failed after {execution_time:.2f}s for "
                f"user {user_id}: {e}"
            )
            error_result = f"Error executing {function_name}: {str(e)}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result

    async def execute_tool_calls(
        self,
        tool_calls: list[Any],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> list[dict[str, Any]]:
        """Execute all tool calls in parallel and return results.

        Args:
            tool_calls: List of tool call objects
            user_id: User ID for logging and database
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results (optional)

        Returns:
            List of tool results with tool_call_id and content
        """
        if not tool_calls:
            logger.info("No tool calls to execute")
            return []

        logger.info(
            f"Executing {len(tool_calls)} tool calls in parallel for user {user_id}, "
            f"chat {chat_id}, iteration {self.tracker._iteration_count}"
        )

        async def execute_single(tool_call: Any) -> dict[str, Any]:
            tool_call_id, function_name, arguments = (
                MessageProcessor.extract_tool_call_info(tool_call)
            )

            safe_args = arguments[:100] if arguments else "None"
            logger.info(
                f"Processing tool call {tool_call_id}: {function_name} "
                f"with arguments: {safe_args}..."
            )

            content = await self.execute_single_tool(
                function_name, arguments, user_id, db_ops, chat_id
            )

            logger.info(
                f"Tool call {tool_call_id} completed: {function_name} "
                f"result length: {len(content)} chars"
            )

            return {
                "tool_call_id": tool_call_id,
                "content": content,
            }

        return await asyncio.gather(
            *[execute_single(tc) for tc in tool_calls]
        )