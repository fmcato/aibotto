"""Enhanced agentic orchestrator functionality for LLM integration with tools."""

import logging
from typing import Any

from ..config.settings import Config
from ..db.operations import DatabaseOperations
from .agentic_loop_processor import BaseAgenticLoopProcessor, ToolExecutionInterface
from .llm_client import LLMClient
from .prompt_templates import SystemPrompts
from .tool_executor import ToolExecutor
from .tool_tracker import ToolTracker

logger = logging.getLogger(__name__)


class AgenticOrchestrator(BaseAgenticLoopProcessor):
    """Main orchestrator for agentic LLM+tool interactions."""

    def __init__(self) -> None:
        tracker = ToolTracker()
        super().__init__(
            max_iterations=Config.MAX_TOOL_ITERATIONS,
            llm_client=LLMClient(),
            tracker=tracker,
        )
        self.tool_executor = ToolExecutor(tracker=tracker)  # Share tracker instance
        logger.info("Initialized AgenticOrchestrator with BaseAgenticLoopProcessor")

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for the LLM."""
        return self.tool_executor._get_tool_definitions()

    def get_tool_execution_interface(self) -> ToolExecutionInterface:
        """Get the tool execution interface for this orchestrator."""
        return self.tool_executor

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

        return await self.process_iterations(
            messages, user_id=user_id, chat_id=chat_id, db_ops=db_ops
        )

    async def _prepare_messages(
        self,
        user_id: int,
        chat_id: int,
        message: str,
        db_ops: DatabaseOperations | None,
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
                role: str = msg["role"] or "user"
                content: str = msg["content"] or ""
                messages.append({"role": role, "content": content})

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
            return await self.process_iterations(messages, 0, 0, None)
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
