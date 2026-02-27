"""Enhanced agentic orchestrator functionality for LLM integration with tools."""

import logging
from typing import Any

from ..config.settings import Config
from ..db.operations import DatabaseOperations
from .iteration_manager import IterationManager
from .llm_client import LLMClient
from .message_processor import MessageProcessor
from .prompt_templates import SystemPrompts
from .tool_executor import ToolExecutor
from .tool_tracker import ToolTracker

logger = logging.getLogger(__name__)


class AgenticOrchestrator:
    """Main orchestrator for agentic LLM+tool interactions."""

    def __init__(self) -> None:
        self.llm_client = LLMClient()
        self.tool_executor = ToolExecutor()
        self.tracker = ToolTracker()
        self.max_iterations = Config.MAX_TOOL_ITERATIONS
        self.iteration_manager = IterationManager(self.max_iterations)
    
    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for the LLM."""
        return self.tool_executor._get_tool_definitions()
    
    async def _execute_tool_calls(
        self,
        tool_calls: list[Any],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> list[dict[str, Any]]:
        """Execute all tool calls in parallel and return results."""
        return await self.tool_executor.execute_tool_calls(
            tool_calls, user_id, chat_id, db_ops
        )

    async def _process_llm_iteration(
        self,
        messages: list[dict[str, Any]],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> tuple[str | None, list[dict[str, Any]] | None]:
        """Process a single LLM iteration.

        Args:
            messages: Conversation messages
            user_id: User ID for logging and database
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results (optional)

        Returns:
            Tuple of (final_response, tool_results)
            - If final_response is not None, it's the final response
            - If tool_results is not None, they should be added to messages
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
                await db_ops.save_message(
                    user_id, chat_id, 0, "system", error_msg
                )
            return error_msg, None

        choice = response["choices"][0]
        if "message" not in choice or not choice["message"]:
            error_msg = "Invalid response format: no message found"
            logger.error(error_msg)
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "system", error_msg
                )
            return error_msg, None

        message_obj = choice["message"]
        tool_calls = MessageProcessor.extract_tool_calls_from_response(message_obj)
        logger.info(
            f"LLM iteration {self.tracker._iteration_count} returned "
            f"{len(tool_calls) if tool_calls else 0} tool calls"
        )

        if tool_calls:
            # Execute tool calls
            tool_results = await self._execute_tool_calls(
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
            return None, tool_results
        else:
            # Final response
            final_content = MessageProcessor.extract_response_content(message_obj)
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "assistant", final_content
                )
            logger.info(
                f"Final response received in iteration {self.tracker._iteration_count}: "
                f"{len(final_content)} chars"
            )
            return final_content, None

    async def process_user_request(
        self,
        user_id: int,
        chat_id: int,
        message: str,
        db_ops: DatabaseOperations | None = None,
    ) -> str:
        """Process a user request with tool calling capabilities.

        Args:
            user_id: User ID for tracking
            chat_id: Chat ID for tracking
            message: User's message
            db_ops: Database operations for saving results

        Returns:
            Assistant's response
        """
        # Reset tracking for new request
        self.tracker.reset_tracking()

        # Prepare messages with conversation history
        messages = await self._prepare_messages(user_id, chat_id, message, db_ops)

        return await self.iteration_manager.process_iterations(
            self, messages, user_id, chat_id, db_ops
        )

    async def _prepare_messages(
        self,
        user_id: int,
        chat_id: int,
        message: str,
        db_ops: DatabaseOperations | None
    ) -> list[dict[str, str]]:
        """Prepare messages for LLM including conversation history.

        Args:
            user_id: User ID
            chat_id: Chat ID
            message: Current message
            db_ops: Database operations

        Returns:
            List of message dicts
        """
        # Get base system prompt
        messages = SystemPrompts.get_base_prompt(max_turns=self.max_iterations)

        # Add conversation history if available
        if db_ops:
            history = await db_ops.get_conversation_history(user_id, chat_id)
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current message
        messages.append({"role": "user", "content": message})

        return messages

    async def process_prompt_stateless(self, message: str) -> str:
        """Process a single prompt without database persistence (stateless).

        Args:
            message: The user's prompt/message

        Returns:
            The assistant's response
        """
        # Reset tracking for stateless processing - this is critical for CLI usage
        self.tracker.reset_stateless_tracking()

        # Prepare messages with system prompt (no history for stateless)
        messages = SystemPrompts.get_base_prompt(max_turns=self.max_iterations)
        messages.append({"role": "user", "content": message})

        try:
            return await self.iteration_manager.process_iterations(
                self, messages, 0, 0, None
            )
        except Exception as e:
            logger.error(f"Error in process_prompt_stateless: {e}")
            return f"Error: {e}"

    def cleanup_old_entries(self, max_age_hours: int = 24) -> None:
        """Clean up old entries from the global tracker to prevent memory leaks.

        Args:
            max_age_hours: Maximum age of entries to keep (default: 24 hours)
        """
        self.tracker.cleanup_old_entries(max_age_hours)


# Alias for backward compatibility
ToolCallingManager = AgenticOrchestrator