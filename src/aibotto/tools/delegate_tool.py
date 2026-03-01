"""Generic tool for delegating tasks to specialized subagents."""

import json
import logging
from typing import Any

from aibotto.ai.subagent.subagent_executor import SubAgentExecutor, SubAgentConfig
from aibotto.tools.base import ToolExecutor

logger = logging.getLogger(__name__)


class DelegateExecutor(ToolExecutor):
    """Generic executor for delegating tasks to any registered subagent."""

    async def execute(
        self,
        arguments: str,
        user_id: int = 0,
        db_ops: Any = None,
        chat_id: int = 0,
    ) -> str:
        """Delegate task to specified subagent."""
        try:
            args = json.loads(arguments)
            subagent_name = args.get("subagent_name", "")
            method = args.get("method", "execute_task")
            task_description = args.get("task_description", "")
            
            if not subagent_name or not subagent_name.strip():
                return "Error: subagent_name cannot be empty"
            
            if not task_description or not task_description.strip():
                return "Error: task_description cannot be empty"

            # Configure subagent execution
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

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in delegate_tool arguments: {e}")
            return "Error: Invalid arguments format. Expected JSON."
        except Exception as e:
            logger.error(f"Delegate tool error: {e}")
            return f"Error delegating task: {str(e)}"


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
        subagent_name: Name of the subagent to use (e.g., "web_research", "python_script")
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