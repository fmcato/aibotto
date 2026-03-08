"""
Tool execution orchestration functionality.
"""

import asyncio
import logging
import time
from typing import Any

from ..db.operations import DatabaseOperations
from aibotto.tools.toolset import get_toolset
from .message_processor import MessageProcessor
from .tool_tracker import ToolTracker

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Orchestrates tool execution with logging, error handling, and optional isolation.

    Supports both main agent (global toolset, no concurrency limit) and
    subagent (custom toolset, concurrency limited) modes.
    """

    def __init__(
        self,
        tracker: ToolTracker | None = None,
        toolset: Any = None,
        max_concurrent: int | None = None,
        instance_id: int | None = None,
    ) -> None:
        """Initialize tool executor with optional subagent configuration.

        Args:
            tracker: Tool tracker for deduplication (default: new global tracker)
            toolset: Custom toolset for isolated tool access (default: global toolset)
            max_concurrent: Maximum concurrent tool executions (default: no limit)
            instance_id: Instance ID for namespaced logging (default: None)
        """
        self.tracker = tracker if tracker else ToolTracker()
        self._toolset = toolset
        self.max_concurrent = max_concurrent
        self.instance_id = instance_id

        self._register_tools()

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for the LLM."""
        from .prompt_templates import ToolDescriptions

        return ToolDescriptions.get_tool_definitions()

    def _get_log_prefix(self) -> str:
        """Get logging prefix with optional instance context.

        Returns:
            Log prefix string
        """
        if self.instance_id:
            return f"SubAgent {self.instance_id}"
        return "ToolExecutor"

    def _log(self, level: str, message: str) -> None:
        """Log message with instance context.

        Args:
            level: Log level (info, warning, error, debug)
            message: Message to log
        """
        prefixed_message = f"{self._get_log_prefix()}: {message}"
        getattr(logger, level)(prefixed_message)

    def _register_tools(self) -> None:
        """Ensure tool executors are available via toolset."""
        if self._toolset is None:
            global_toolset = get_toolset()

            if not global_toolset.is_initialized():
                global_toolset.initialize_once()

            self._log("info", "Tool executors available via global toolset")
        else:
            self._log(
                "info",
                f"Tool executors available via custom toolset"
                f"{f' for instance {self.instance_id}' if self.instance_id else ''}",
            )

    def get_executor(self, function_name: str):
        """Get executor for a specific tool function.

        Args:
            function_name: Name of the tool function

        Returns:
            Tool executor instance or None
        """
        if self._toolset is not None:
            return self._toolset.get_executor(function_name)
        global_toolset = get_toolset()
        return global_toolset.get_executor(function_name)

    async def execute_single_tool(
        self,
        function_name: str | None,
        arguments: str | None,
        user_id: int = 0,
        db_ops: DatabaseOperations | None = None,
        chat_id: int = 0,
        message_id: int = 0,
        tool_call_id: str | None = None,
    ) -> str:
        """Execute a single tool and return the result.

        Args:
            function_name: Name of the tool function to execute
            arguments: JSON string of arguments
            user_id: User ID for logging (optional)
            db_ops: Database operations for saving results (optional)
            chat_id: Chat ID for database operations (optional)
            message_id: Message ID for database tracking (optional)
            tool_call_id: Tool call ID for database tracking (optional)

        Returns:
            Tool execution result as string
        """
        start_time = time.time()

        if function_name is None:
            error_result = "No function name provided"
            if db_ops:
                await db_ops.save_message_compat(
                    user_id=user_id,
                    chat_id=chat_id,
                    role="system",
                    content=error_result,
                )
            return error_result

        if arguments is None:
            arguments = "{}"

        if self.tracker.is_duplicate_tool_call(
            function_name, arguments, user_id, chat_id
        ):
            self._log("warning", f"Skipping duplicate tool call: {function_name}")
            return (
                f"⚠️ Tool call '{function_name}' already executed in this "
                f"conversation. Skipping to prevent infinite loops."
            )

        self.tracker.track_tool_call(function_name, arguments, user_id, chat_id)

        if self.tracker.is_similar_tool_call(
            function_name, arguments, user_id, chat_id
        ):
            self._log(
                "info", f"Implementing smart retry prevention for {function_name}"
            )
            if "python3" in arguments.lower() and "calc" in arguments.lower():
                return (
                    "🔄 I already attempted a similar calculation. Let me try a "
                    "different approach or provide you with what I found so far."
                )

        executor = self.get_executor(function_name)
        if not executor:
            error_result = f"Unknown tool function: {function_name}"
            if db_ops:
                await db_ops.save_message_compat(
                    user_id=user_id,
                    chat_id=chat_id,
                    role="system",
                    content=error_result,
                )
            return error_result

        source_agent = (
            "main" if not self.instance_id else f"subagent_{self.instance_id}"
        )

        try:
            self._log(
                "info",
                f"Starting tool execution: {function_name} for user {user_id}, "
                f"chat {chat_id}, iteration {self.tracker._iteration_count}",
            )

            if db_ops and tool_call_id is not None:
                try:
                    await db_ops.save_tool_call(
                        message_id=message_id,
                        tool_name=function_name,
                        tool_call_id=tool_call_id,
                        arguments_json=arguments,
                        source_agent=source_agent,
                        subagent_instance_id=self.instance_id,
                        iteration_number=self.tracker._iteration_count,
                    )
                except Exception as e:
                    self._log("warning", f"Failed to save tool call: {e}")

            result = await executor.execute(arguments, user_id, db_ops, chat_id)
            execution_time = time.time() - start_time

            self._log(
                "info",
                f"Tool {function_name} completed in {execution_time:.2f}s for "
                f"user {user_id}: {result[:200]}...",
            )

            if execution_time > 10:
                self._log(
                    "warning",
                    f"SLOW TOOL EXECUTION: {function_name} took {execution_time:.2f}s "
                    f"for user {user_id}, chat {chat_id}",
                )

            if db_ops and tool_call_id is not None:
                try:
                    await db_ops.update_tool_call_result(
                        tool_call_id=tool_call_id,
                        result_content=result,
                        status="completed",
                    )
                except Exception as e:
                    self._log("warning", f"Failed to update tool call result: {e}")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self._log(
                "error",
                f"Tool {function_name} failed after {execution_time:.2f}s for "
                f"user {user_id}: {e}",
            )
            error_result = f"Error executing {function_name}: {str(e)}"
            if db_ops:
                await db_ops.save_message_compat(
                    user_id=user_id,
                    chat_id=chat_id,
                    role="system",
                    content=error_result,
                )

            if db_ops and tool_call_id is not None:
                try:
                    await db_ops.update_tool_call_result(
                        tool_call_id=tool_call_id,
                        result_content=error_result,
                        status="failed",
                        error_message=str(e),
                    )
                except Exception as db_e:
                    self._log("warning", f"Failed to update tool call failure: {db_e}")

            return error_result

    async def execute_tool_calls(
        self,
        tool_calls: list[Any],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
        message_id: int = 0,
    ) -> list[dict[str, Any]]:
        """Execute all tool calls in parallel with optional concurrency limit.

        Args:
            tool_calls: List of tool call objects
            user_id: User ID for logging and database
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results (optional)
            message_id: Message ID for database tracking (optional)

        Returns:
            List of tool results with tool_call_id and content
        """
        if not tool_calls:
            self._log("info", "No tool calls to execute")
            return []

        self._log(
            "info",
            f"Executing {len(tool_calls)} tool calls for user {user_id}, "
            f"chat {chat_id}, iteration {self.tracker._iteration_count}",
        )

        async def execute_single(tool_call: Any) -> dict[str, Any]:
            tool_call_id, function_name, arguments = (
                MessageProcessor.extract_tool_call_info(tool_call)
            )

            safe_args = arguments[:100] if arguments else "None"
            self._log(
                "info",
                f"Processing tool call {tool_call_id}: {function_name} "
                f"with arguments: {safe_args}...",
            )

            content = await self.execute_single_tool(
                function_name,
                arguments,
                user_id,
                db_ops,
                chat_id,
                message_id,
                tool_call_id,
            )

            self._log(
                "info",
                f"Tool call {tool_call_id} completed: {function_name} "
                f"result length: {len(content)} chars",
            )

            return {
                "tool_call_id": tool_call_id,
                "content": content,
            }

        if self.max_concurrent:
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def execute_with_limit(tool_call: Any) -> dict[str, Any]:
                async with semaphore:
                    return await execute_single(tool_call)

            return await asyncio.gather(
                *[execute_with_limit(tc) for tc in tool_calls],
                return_exceptions=False,
            )
        else:
            return await asyncio.gather(*[execute_single(tc) for tc in tool_calls])
