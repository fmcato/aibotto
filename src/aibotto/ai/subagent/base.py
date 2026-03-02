"""Base subagent class with isolated LLM context and iteration management."""

import logging
from typing import Any

from aibotto.ai.agentic_loop_processor import (
    BaseAgenticLoopProcessor,
    ToolExecutionInterface,
)
from aibotto.ai.llm_client import LLMClient
from aibotto.ai.prompt_templates import DateTimeContext
from aibotto.ai.tool_tracker import ToolTracker
from .subagent_tool_executor import SubAgentToolExecutor
from .toolset import SubAgentToolset

logger = logging.getLogger(__name__)


class SubAgent(BaseAgenticLoopProcessor):
    """Base class for specialized subagents with isolated LLM context."""

    def __init__(self, max_iterations: int = 5):
        super().__init__(
            max_iterations=max_iterations,
            llm_client=LLMClient(),
            tracker=ToolTracker(id(self)),
        )
        self._instance_id = id(self)
        self._toolset = SubAgentToolset(self._instance_id)
        # Ensure compatibility with existing code
        self._tracker = self.tracker
        logger.info(
            f"Created SubAgent instance {self._instance_id} "
            f"(max_iterations: {max_iterations})"
        )

    def _get_system_prompt(self) -> str:
        """Get subagent-specific system prompt. Override in subclasses."""
        return "You are a helpful assistant."

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions available to this subagent. Override in subclasses."""
        return []

    def _register_tools(self) -> None:
        """Register tools available to this subagent. Override in subclasses."""
        pass

    def get_tool_execution_interface(self) -> ToolExecutionInterface:
        """Get the tool execution interface for this subagent."""
        return SubAgentToolExecutor(
            self._instance_id, self.tracker, self._toolset
        )

    async def execute_task(
        self,
        initial_message: str,
        task_instructions: str = "",
        user_id: int = 0,
        chat_id: int = 0,
    ) -> str:
        """
        Execute a task in isolated LLM context.

        Args:
            initial_message: The initial user message to process
            task_instructions: Additional instructions for the task
            user_id: User ID for proper tracking
            chat_id: Chat ID for proper tracking

        Returns:
            Final response string
        """

        # Build messages
        datetime_msg = DateTimeContext.get_current_datetime_message()
        logger.info(
            f"SubAgent {self._instance_id}: Added datetime context: "
            f"{datetime_msg['content']}"
        )

        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            datetime_msg,
        ]

        if task_instructions:
            messages.append({"role": "system", "content": f"Task: {task_instructions}"})

        messages.append({"role": "user", "content": initial_message})

        logger.info(
            f"SubAgent {self._instance_id}: Starting task execution "
            f"(user_id: {user_id}, chat_id: {chat_id})"
        )

        # Register tools for this subagent instance
        self._register_tools()

        return await self.process_iterations(
            messages, user_id=user_id, chat_id=chat_id, db_ops=None
        )
