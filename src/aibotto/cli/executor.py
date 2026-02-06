"""
CLI command executor with safety measures.
"""

import asyncio
import logging

from .security import SecurityManager

logger = logging.getLogger(__name__)


class CLIExecutor:
    """Executor for CLI commands with safety features."""

    def __init__(self) -> None:
        self.security_manager = SecurityManager()

    async def execute_command(self, command: str) -> str:
        """Execute CLI command safely and return output."""
        try:
            # Log command execution
            logger.info(f"Executing CLI command: {command}")

            # Security checks
            security_check = await self.security_manager.validate_command(command)
            if not bool(security_check["allowed"]):
                logger.warning(f"Command blocked for security: {command}")
                return security_check["message"]

            # Execute command in a controlled environment
            logger.info(f"Starting subprocess for command: {command}")
            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                result = stdout.decode("utf-8", errors="ignore")
                logger.info(f"Command completed successfully: {command}")
                logger.info(f"Command output (first 200 chars): {result[:200]}...")
                return result
            else:
                error_msg = stderr.decode("utf-8", errors="ignore")
                logger.error(
                    f"Command failed with return code {process.returncode}: {command}"
                )
                logger.error(f"Command error: {error_msg}")
                return f"Error: {error_msg}"

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return f"Error executing command: {str(e)}"
