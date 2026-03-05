"""
Python code executor with relaxed length limits.
"""

from ...tools.python_security_manager import PythonSecurityManager
from ...tools.base import ToolExecutor, ToolExecutionError
from ...tools.subprocess_runner import SubprocessRunner


class PythonExecutor(ToolExecutor, SubprocessRunner):
    """Executor for Python code execution with higher length limits."""

    def __init__(self) -> None:
        super().__init__()
        self.security_manager = PythonSecurityManager()

    def _wrap_python_code(self, code: str) -> str:
        """Wrap Python code for execution.

        Args:
            code: Python code to wrap

        Returns:
            Complete command string for execution
        """
        if "\n" in code:
            return f"uv run python << 'EOF'\n{code}\nEOF"
        else:
            return f"uv run python -c '{code}'"

    async def _do_execute(self, args: dict, user_id: int, chat_id: int = 0) -> str:
        """Execute Python code safely and return output.

        Args:
            args: Parsed arguments with 'code' field containing Python code
            user_id: User ID for logging
            chat_id: Chat ID for database operations

        Returns:
            Execution result as string

        Raises:
            ToolExecutionError: If no code provided or security check fails
        """
        code = args.get("code")

        if not code:
            raise ToolExecutionError("No code provided")

        self.logger.info(f"Executing Python code for user {user_id}")

        security_check = await self.security_manager.validate_python_code(code)
        if not bool(security_check["allowed"]):
            self.logger.warning(f"Python code blocked for security: {code[:100]}...")
            return str(security_check["message"])

        command = self._wrap_python_code(code)
        return await self._run_subprocess(command, user_id, self.logger)
