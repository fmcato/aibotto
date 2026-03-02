"""
Reusable agentic loop processor with comprehensive tool calling capabilities.

This module provides a base class for agentic LLM interactions with tool calling,
extracting the mature, robust implementation from AgenticOrchestrator into a
reusable component that can be used by both the main orchestrator and subagents.
"""

import logging
from abc import abstractmethod
from typing import Any, Protocol

from aibotto.ai.iteration_manager import LLMProcessor
from aibotto.ai.llm_client import LLMClient
from aibotto.ai.message_processor import MessageProcessor
from aibotto.ai.tool_tracker import ToolTracker
from aibotto.db.operations import DatabaseOperations

logger = logging.getLogger(__name__)


class ToolExecutionInterface(Protocol):
    """Interface for tool execution implementations.

    Subclasses must implement this interface to provide tool execution
    capabilities specific to their needs (global tools vs subagent tools).
    """

    async def execute_tool_calls(
        self,
        tool_calls: list[Any],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> list[dict[str, Any]]:
        """Execute tool calls and return results.

        Args:
            tool_calls: List of tool call objects
            user_id: User ID for logging
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results

        Returns:
            List of tool results with tool_call_id and content
        """
        ...


class BaseAgenticLoopProcessor(LLMProcessor):
    """Base agentic loop processor with comprehensive tool calling logic.

    This class provides the mature, robust loop implementation extracted from
    AgenticOrchestrator, serving as the blueprint for all agentic interactions.
    Subclasses must implement ToolExecutionInterface and provide tool definitions.
    """

    def __init__(
        self,
        max_iterations: int,
        llm_client: LLMClient,
        tracker: Any = None,
    ) -> None:
        """Initialize the agentic loop processor.

        Args:
            max_iterations: Maximum number of iterations allowed
            llm_client: LLM client for making API calls
            tracker: Tool tracker for call deduplication (optional)
        """
        self.max_iterations = max_iterations
        self.llm_client = llm_client
        self.tracker = tracker if tracker else ToolTracker()
        logger.info(
            f"Initialized BaseAgenticLoopProcessor (max_iterations: {max_iterations})"
        )

    @abstractmethod
    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions available to this processor.

        Subclasses must implement this to provide appropriate tool definitions.

        Returns:
            List of tool definition dictionaries
        """
        ...

    @abstractmethod
    def get_tool_execution_interface(self) -> ToolExecutionInterface:
        """Get the tool execution interface for this processor.

        Subclasses must implement this to provide tool execution capabilities.

        Returns:
            ToolExecutionInterface instance
        """
        ...

    async def _process_llm_iteration(
        self,
        messages: list[dict[str, Any]],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> tuple[str | None, list[dict[str, Any]] | None, list[Any] | None]:
        """Process a single LLM iteration with comprehensive error handling.

        This method implements the mature loop logic from AgenticOrchestrator,
        providing robust validation, error handling, and tool execution.

        Args:
            messages: Conversation messages
            user_id: User ID for logging and database
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results (optional)

        Returns:
            Tuple of (final_response, tool_results, tool_calls)
            - If final_response is not None, it's the final response
            - If tool_results is not None, they should be added to messages
            - If tool_calls is not None, it should be added to messages before tool_results

        Raises:
            Any: Unhandled exceptions are caught and logged by the caller
        """
        # Track iteration number
        self.tracker.increment_iteration()
        logger.info(
            f"Starting LLM iteration {self.tracker._iteration_count} for user {user_id}, "
            f"chat {chat_id}, messages: {len(messages)}"
        )

        response = await self.llm_client.chat_completion(
            messages=messages,
            tools=self._get_tool_definitions(),
        )

        if "choices" not in response or len(response["choices"]) == 0:
            error_msg = "Invalid response format: no choices found"
            logger.error(error_msg)
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg, None, None

        choice = response["choices"][0]
        finish_reason = choice.get("finish_reason")
        if "message" not in choice or not choice["message"]:
            error_msg = "Invalid response format: no message found"
            logger.error(error_msg)
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg, None, None

        message_obj = choice["message"]

        # Handle non-terminal finish reasons
        if finish_reason == "length":
            error_msg = "Response truncated - max token limit reached"
            logger.error(error_msg)
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg, None, None
        elif finish_reason == "content_filter":
            error_msg = "Response blocked by content filter"
            logger.error(error_msg)
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg, None, None
        elif finish_reason in ("tool_calls", "function_call"):
            tool_calls = MessageProcessor.extract_tool_calls_from_response(message_obj)
            if not tool_calls:
                error_msg = (
                    f"Inconsistent response: finish_reason={finish_reason} "
                    "but no tool_calls found"
                )
                logger.error(error_msg)
                return error_msg, None, None

        tool_calls = MessageProcessor.extract_tool_calls_from_response(message_obj)
        logger.info(
            f"LLM iteration {self.tracker._iteration_count} returned "
            f"{len(tool_calls) if tool_calls else 0} tool calls"
        )

        if tool_calls:
            # Execute tool calls using subclass-specific implementation
            tool_executor = self.get_tool_execution_interface()
            tool_results = await tool_executor.execute_tool_calls(
                tool_calls, user_id, chat_id, db_ops
            )

            # Save assistant message with tool calls to history
            assistant_message = MessageProcessor.extract_response_content(message_obj)
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "assistant", assistant_message
                )

            logger.info(
                f"Tool execution completed for iteration {self.tracker._iteration_count}, "
                f"results: {len(tool_results)} tool results"
            )
            # Return tool_results and tool_calls so both can be added to messages
            return None, tool_results, tool_calls
        else:
            # Final response - validate content first
            final_content = MessageProcessor.extract_response_content(message_obj)
            if not final_content or not final_content.strip():
                error_msg = "Empty response from AI service"
                logger.error(error_msg)
                if db_ops:
                    await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
                return error_msg, None, None
            
            # Auto-execution hook for PythonScriptAgent
            from aibotto.ai.subagent.python_script_agent import PythonScriptAgent
            if isinstance(self, PythonScriptAgent):
                python_code = final_content.strip()
                if python_code:
                    result = await self._auto_execute_python(
                        python_code, user_id, chat_id, db_ops
                    )
                    
                    # Check if execution resulted in an error
                    if result.startswith("Error:") or result.startswith("Timeout:"):
                        # Return error to LLM for debugging
                        tool_result = {
                            "tool_call_id": "auto_python_exec",
                            "role": "tool",
                            "content": result
                        }
                        logger.info(
                            f"PythonScriptAgent auto-execution error: {result[:100]}"
                        )
                        return None, [tool_result], None
                    else:
                        # Success - return result
                        if db_ops:
                            await db_ops.save_message(
                                user_id, chat_id, 0, "assistant", result
                            )
                        logger.info(
                            f"PythonScriptAgent auto-execution success: "
                            f"{len(result)} chars"
                        )
                        return result, None, None
            
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "assistant", final_content
                )
            logger.info(
                f"Final response received in iteration {self.tracker._iteration_count}: "
                f"{len(final_content)} chars"
            )
            return final_content, None, None

    async def _auto_execute_python(
        self,
        code: str,
        user_id: int,
        chat_id: int,
        db_ops: DatabaseOperations | None,
    ) -> str:
        """Auto-execute Python code for PythonScriptAgent.

        Args:
            code: Python code to execute
            user_id: User ID for logging
            chat_id: Chat ID for database operations
            db_ops: Database operations instance

        Returns:
            Execution result or error message
        """
        try:
            # Get Python executor from subagent's toolset
            if hasattr(self, '_toolset'):
                executor = self._toolset.get_executor("execute_python")
                if not executor:
                    return "Error: Python executor not available"
                
                return await executor.execute(code, user_id, db_ops, chat_id)
            else:
                return "Error: Toolset not available"
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)[:100] if str(e) else ""
            return f"Error: {error_type}: {error_msg}"

    async def process_iterations(
        self,
        messages: list[dict[str, Any]],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> str:
        """Process LLM iterations using the iteration manager.

        Args:
            messages: Conversation messages
            user_id: User ID for logging
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results

        Returns:
            Assistant's response
        """
        from aibotto.ai.iteration_manager import IterationManager

        iteration_manager = IterationManager(self.max_iterations)
        return await iteration_manager.process_iterations(
            self, messages, user_id=user_id, chat_id=chat_id, db_ops=db_ops
        )

    def cleanup_old_entries(self, max_age_hours: int = 24) -> None:
        """Clean up old entries from the tracker to prevent memory leaks.

        Args:
            max_age_hours: Maximum age of entries to keep (default: 24 hours)
        """
        self.tracker.cleanup_old_entries(max_age_hours)

    def reset_tracking(self) -> None:
        """Reset tracking for new request."""
        self.tracker.reset_tracking()

    def reset_stateless_tracking(self) -> None:
        """Reset tracking for stateless processing."""
        self.tracker.reset_stateless_tracking()
