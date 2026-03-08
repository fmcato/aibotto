"""Generic subagent executor for running subagents from tools."""

import logging
from dataclasses import dataclass, field
from typing import Any

from aibotto.ai.subagent.registry import SubAgentRegistry
from aibotto.db.operations import DatabaseOperations

logger = logging.getLogger(__name__)


@dataclass
class SubAgentConfig:
    """Configuration for subagent execution.

    Attributes:
        subagent_name: Name of registered subagent (e.g., "web_research")
        method: Method name to call on subagent (e.g., "execute_research")
        method_kwargs: Keyword arguments to pass to the method
        user_id: User ID for logging
        chat_id: Chat ID for logging
        db_ops: Database operations for tracking (optional)
    """

    subagent_name: str
    method: str
    method_kwargs: dict[str, Any] = field(default_factory=dict)
    user_id: int = 0
    chat_id: int = 0
    db_ops: DatabaseOperations | None = None


class SubAgentExecutor:
    """Generic executor for running subagents."""

    def __init__(self, config: SubAgentConfig):
        """Initialize executor with configuration.

        Args:
            config: Subagent execution configuration
        """
        self.config = config

    async def run(self) -> str:
        """Execute the subagent with the configured method.

        Returns:
            Result from subagent method execution

        Raises:
            RuntimeError: If subagent not found or method fails
        """
        logger.info(
            f"SubAgentExecutor: Starting {self.config.subagent_name}.{self.config.method} "
            f"with namespace (user_id: {self.config.user_id}, chat_id: {self.config.chat_id})"
        )

        # Create subagent instance via registry (handles config-driven properly)
        # Note: method_kwargs are NOT passed to constructor - they're used for the method call later
        subagent = SubAgentRegistry.create(self.config.subagent_name)
        if subagent is None:
            available = ", ".join(SubAgentRegistry.list_subagents())
            error_msg = f"Failed to create subagent '{self.config.subagent_name}'. Available: {available}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(
            f"SubAgentExecutor: Created {self.config.subagent_name} instance "
            f"(instance_id: {subagent._instance_id})"
        )

        # Save subagent to database if db_ops available
        db_subagent_id = None
        if self.config.db_ops:
            try:
                db_subagent_id = await self.config.db_ops.save_subagent(
                    subagent_name=self.config.subagent_name,
                    instance_id=subagent._instance_id,
                    user_id=self.config.user_id,
                    chat_id=self.config.chat_id,
                    max_iterations=subagent.max_iterations,
                    parent_agent="main",
                    task_description=str(self.config.method_kwargs),
                )
            except Exception as e:
                logger.warning(f"Failed to save subagent to database: {e}")

        # Get method from subagent
        if not hasattr(subagent, self.config.method):
            available = ", ".join([m for m in dir(subagent) if not m.startswith("_")])
            error_msg = (
                f"Method '{self.config.method}' not found on {self.config.subagent_name}. "
                f"Available methods: {available}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        method = getattr(subagent, self.config.method)

        # Prepare method kwargs with user_id/chat_id
        method_kwargs = self.config.method_kwargs.copy()
        method_kwargs["user_id"] = self.config.user_id
        method_kwargs["chat_id"] = self.config.chat_id

        logger.info(
            f"SubAgentExecutor: Calling {self.config.subagent_name}.{self.config.method} "
            f"with kwargs: {method_kwargs}"
        )

        # Execute method
        try:
            result = await method(**method_kwargs)
            logger.info(
                f"SubAgentExecutor: {self.config.subagent_name}.{self.config.method} "
                f"completed (instance_id: {subagent._instance_id})"
            )

            # Update subagent completion in database
            if self.config.db_ops and db_subagent_id:
                try:
                    await self.config.db_ops.update_subagent_completion(
                        db_subagent_id=db_subagent_id,
                        result_summary=result[:500] if result else None,
                        actual_iterations=subagent.tracker._iteration_count,
                    )
                except Exception as e:
                    logger.warning(f"Failed to update subagent completion: {e}")

            return result
        except Exception as e:
            error_msg = (
                f"Error executing {self.config.subagent_name}.{self.config.method}: {e}"
            )
            logger.error(error_msg)

            # Update subagent failure in database
            if self.config.db_ops and db_subagent_id:
                try:
                    await self.config.db_ops.update_subagent_completion(
                        db_subagent_id=db_subagent_id,
                        error_message=str(e),
                        actual_iterations=subagent.tracker._iteration_count,
                    )
                except Exception as db_e:
                    logger.warning(f"Failed to update subagent failure: {db_e}")

            raise RuntimeError(error_msg) from e
