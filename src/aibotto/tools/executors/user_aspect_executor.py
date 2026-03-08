"""
User aspect executor for storing discovered user characteristics.
"""

from typing import Any

from ...tools.base import ToolExecutor, ToolExecutionError


class UserAspectExecutor(ToolExecutor):
    """Executor for storing user aspects."""

    def __init__(self) -> None:
        super().__init__()
        self._db_ops = None

    async def execute(
        self, arguments: str, user_id: int = 0, db_ops: Any = None, chat_id: int = 0
    ) -> str:
        """Execute the tool with given arguments using template method pattern.

        Args:
            arguments: JSON string of arguments
            user_id: User ID for logging
            db_ops: Database operations instance
            chat_id: Chat ID for database operations

        Returns:
            Tool execution result as string
        """
        self._db_ops = db_ops
        return await super().execute(arguments, user_id, db_ops, chat_id)

    async def _do_execute(
        self, args: dict, user_id: int, chat_id: int = 0, db_ops: Any = None
    ) -> str:
        """Store a user aspect with validation.

        Args:
            args: Parsed arguments with 'category', 'aspect', and optional 'confidence'
            user_id: User ID for storing the aspect
            chat_id: Chat ID (not used but required by signature)

        Returns:
            Confirmation message with stored aspect details

        Raises:
            ToolExecutionError: If required fields are missing or validation fails
        """
        category = args.get("category")
        aspect = args.get("aspect")
        confidence = args.get("confidence", 0.5)

        if not category or not isinstance(category, str) or not category.strip():
            raise ToolExecutionError(
                "Category is required and must be a non-empty string"
            )

        if not aspect or not isinstance(aspect, str) or not aspect.strip():
            raise ToolExecutionError(
                "Aspect is required and must be a non-empty string"
            )

        if not isinstance(confidence, (int, float)):
            raise ToolExecutionError("Confidence must be a number")

        if confidence < 0 or confidence > 1:
            raise ToolExecutionError("Confidence must be between 0 and 1")

        self.logger.info(
            f"Storing user aspect: {category} = {aspect} (confidence: {confidence})"
        )

        if self._db_ops:
            await self._db_ops.store_user_aspect(user_id, category, aspect, confidence)

        return f"Stored user aspect: {category} - {aspect}"
