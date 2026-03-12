"""
Subprocess runner mixin for CLI and Python executors.
"""

import asyncio
from typing import Protocol


class SubprocessLogger(Protocol):
    """Protocol for logging in subprocess execution."""

    def info(self, msg: str) -> None:
        """Log info message."""
        pass

    def error(self, msg: str) -> None:
        """Log error message."""
        pass

    def warning(self, msg: str) -> None:
        """Log warning message."""
        pass


class SubprocessRunner:
    """Mixin class providing subprocess execution functionality."""

    async def _run_subprocess(
        self, command: str, user_id: int, logger: SubprocessLogger, stdin: str | None = None
    ) -> str:
        """Run a command in a subprocess and return output.

        Args:
            command: Command to execute
            user_id: User ID for logging
            logger: Logger instance for subprocess operations
            stdin: Optional input data to pass to the command via stdin

        Returns:
            Command output or error message
        """
        logger.info(f"Starting subprocess for command: {command}")

        if stdin:
            logger.info(f"stdin input (first 200 chars): {stdin[:200]}...")

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if stdin else None,
        )

        stdin_bytes = stdin.encode("utf-8") if stdin else None
        stdout, stderr = await process.communicate(input=stdin_bytes)

        if process.returncode == 0:
            result = stdout.decode("utf-8", errors="ignore")
            logger.info(f"Command completed successfully for user {user_id}")
            logger.info(f"Command output (first 200 chars): {result[:200]}...")
            return result
        else:
            error_msg = stderr.decode("utf-8", errors="ignore")
            logger.error(
                f"Command failed with return code {process.returncode} for user {user_id}"
            )
            logger.error(f"Command error: {error_msg}")
            return f"Error: {error_msg}"
