"""
Subagent-specific tool execution interface for isolated tool access.

This module provides the tool execution implementation for subagents,
extracting the logic from the nested SubProcessor class in the base SubAgent.
"""

import asyncio
import logging
from typing import Any

from aibotto.ai.message_processor import MessageProcessor
from aibotto.ai.tool_tracker import ToolTracker
from aibotto.db.operations import DatabaseOperations
from aibotto.tools.toolset import get_toolset
from ..agentic_loop_processor import ToolExecutionInterface

logger = logging.getLogger(__name__)


class SubAgentToolExecutor(ToolExecutionInterface):
    """Tool executor for subagents with isolated tool access and tracking.

    This class provides tool execution capabilities specifically for subagents,
    using instance-specific tool registries and isolated tracking to prevent
    cross-contamination between different subagent invocations.
    """

    def __init__(self, instance_id: int, tracker: ToolTracker, toolset=None) -> None:
        """Initialize the subagent tool executor.

        Args:
            instance_id: Unique instance ID for this subagent
            tracker: Sub-agent tracker for namespaced call tracking
            toolset: Subagent-specific toolset (optional, defaults to global)
        """
        self.instance_id = instance_id
        self.tracker = tracker
        self._toolset = toolset

        logger.info(
            f"Created SubAgentToolExecutor for instance {instance_id} "
            f"with tracker type {type(tracker).__name__}, toolset {'local' if toolset else 'global'}"
        )

    def _get_toolset(self):
        """Get the toolset instance.

        Returns:
            Toolset instance (subagent-specific or global)
        """
        return self._toolset if self._toolset is not None else get_toolset()

    async def execute_tool_calls(
        self,
        tool_calls: list[Any],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> list[dict[str, Any]]:
        """Execute tool calls in parallel using subagent-specific tool access.

        Args:
            tool_calls: List of tool call objects
            user_id: User ID for logging
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results

        Returns:
            List of tool results with tool_call_id and content
        """
        if not tool_calls:
            logger.info(f"SubAgent {self.instance_id}: No tool calls to execute")
            return []

        logger.info(
            f"SubAgent {self.instance_id}: Executing {len(tool_calls)} tool calls "
            f"for user {user_id}, chat {chat_id}"
        )

        async def execute_single_tool_call(tool_call: Any) -> dict[str, Any]:
            """Execute a single tool call with proper error handling."""
            tool_call_id, function_name, arguments = (
                MessageProcessor.extract_tool_call_info(tool_call)
            )

            logger.info(
                f"SubAgent {self.instance_id}: Executing tool {function_name} "
                f"for user {user_id}, chat {chat_id}"
            )

            # Get tool from global toolset
            global_toolset = self._get_toolset()
            tool_executor = (
                global_toolset.get_executor(function_name) if function_name else None
            )
            if not tool_executor or not function_name:
                error_result = f"Unknown tool function: {function_name}"
                logger.warning(
                    f"SubAgent {self.instance_id}: Unknown tool - {function_name}"
                )
                return {
                    "tool_call_id": tool_call_id,
                    "content": error_result,
                }

            try:
                # Execute the tool
                result = await tool_executor.execute(
                    arguments or "{}", user_id, db_ops, chat_id
                )
                logger.info(
                    f"SubAgent {self.instance_id}: Tool {function_name} completed "
                    f"successfully for user {user_id}"
                )
                return {
                    "tool_call_id": tool_call_id,
                    "content": result,
                }
            except Exception as e:
                error_result = f"Error executing {function_name}: {str(e)}"
                logger.error(
                    f"SubAgent {self.instance_id}: Tool {function_name} failed - {e}"
                )
                return {
                    "tool_call_id": tool_call_id,
                    "content": error_result,
                }

        # Execute tool calls in parallel with concurrency limit
        max_concurrent = getattr(
            __import__("aibotto.config.settings").config.Config,
            "SUBAGENT_MAX_CONCURRENT_TOOLS",
            5,
        )
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_limit(tool_call: Any) -> dict[str, Any]:
            """Execute a single tool call with concurrency limit."""
            async with semaphore:
                return await execute_single_tool_call(tool_call)

        # Execute all tool calls in parallel
        results = await asyncio.gather(
            *[execute_with_limit(tc) for tc in tool_calls], return_exceptions=False
        )

        logger.info(
            f"SubAgent {self.instance_id}: Tool execution completed for "
            f"{len(results)} tool calls"
        )
        return results
