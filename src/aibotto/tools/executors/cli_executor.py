"""
CLI command executor with safety measures.
"""

from ...tools.cli_security_manager import CLISecurityManager
from ...tools.base import ToolExecutor, ToolExecutionError
from ...tools.subprocess_runner import SubprocessRunner


class CLIExecutor(ToolExecutor, SubprocessRunner):
    """Executor for CLI commands with safety features."""

    def __init__(self) -> None:
        super().__init__()
        self.security_manager = CLISecurityManager()

    async def _do_execute(self, args: dict, user_id: int, chat_id: int = 0) -> str:
        """Execute CLI command safely and return output.

        Args:
            args: Parsed arguments with 'command' field
            user_id: User ID for logging
            chat_id: Chat ID for database operations

        Returns:
            Command output or error message
        """
        command = args.get("command")

        if not command:
            raise ToolExecutionError("No command provided")

        self.logger.info(f"Executing CLI command for user {user_id}: {command}")

        security_check = await self.security_manager.validate_command(command)
        if not bool(security_check["allowed"]):
            self.logger.warning(f"Command blocked for security: {command}")
            return security_check["message"]

        return await self._run_subprocess(command, user_id, self.logger)
