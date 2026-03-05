"""Generic tool for delegating tasks to specialized subagents."""

import logging

from aibotto.ai.subagent.subagent_executor import SubAgentExecutor, SubAgentConfig
from aibotto.tools.base import ToolExecutor, ToolExecutionError

logger = logging.getLogger(__name__)


class DelegateExecutor(ToolExecutor):
    """Generic executor for delegating tasks to any registered subagent."""

    async def _do_execute(self, args: dict, user_id: int, chat_id: int = 0) -> str:
        """Delegate task to specified subagent.

        Args:
            args: Parsed arguments with 'subagent_name', 'method', and 'task_description'
            user_id: User ID for logging
            chat_id: Chat ID for database operations

        Returns:
            Result from the subagent

        Raises:
            ToolExecutionError: If validation fails
        """
        subagent_name = args.get("subagent_name", "")
        method = args.get("method", "execute_task")
        task_description = args.get("task_description", "")

        if not subagent_name or not subagent_name.strip():
            raise ToolExecutionError("Error: subagent_name cannot be empty")

        if not task_description or not task_description.strip():
            raise ToolExecutionError("Error: task_description cannot be empty")

        config = SubAgentConfig(
            subagent_name=subagent_name,
            method=method,
            method_kwargs={"initial_message": task_description},
            user_id=user_id,
            chat_id=chat_id,
        )

        executor = SubAgentExecutor(config)
        result = await executor.run()

        logger.info(
            f"Delegated task to subagent '{subagent_name}' "
            f"(task: {task_description[:50]}...)"
        )
        return result


async def delegate_task(
    subagent_name: str,
    task_description: str,
    method: str = "execute_task",
    user_id: int = 0,
    chat_id: int = 0,
) -> str:
    """
    Delegate a task to a specialized subagent.

    Args:
        subagent_name: Name of the subagent to use (e.g., "web_research")
        task_description: Description of the task to accomplish
        method: Subagent method to call (default: "execute_task")
        user_id: User ID for proper tracking (default: 0)
        chat_id: Chat ID for proper tracking (default: 0)

    Returns:
        Result from the subagent
    """
    config = SubAgentConfig(
        subagent_name=subagent_name,
        method=method,
        method_kwargs={"initial_message": task_description},
        user_id=user_id,
        chat_id=chat_id,
    )
    executor = SubAgentExecutor(config)
    return await executor.run()
