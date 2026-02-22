"""
CLI command executor with safety measures.
"""

import asyncio
import json
import logging

from ...db.operations import DatabaseOperations
from ...tools.security import SecurityManager
from ..base import ToolExecutor

logger = logging.getLogger(__name__)


class CLIExecutor(ToolExecutor):
    """Executor for CLI commands with safety features."""

    def __init__(self) -> None:
        self.security_manager = SecurityManager()

    async def execute(
        self,
        arguments: str,
        user_id: int = 0,
        db_ops: DatabaseOperations | None = None,
        chat_id: int = 0,
    ) -> str:
        """Execute CLI command safely and return output."""
        try:
            # Parse arguments
            args = json.loads(arguments)
            command = args.get("command")

            if not command:
                raise ValueError("No command provided")

            # Log command execution
            logger.info(f"Executing CLI command for user {user_id}: {command}")

            # Security checks
            security_check = await self.security_manager.validate_command(command)
            if not bool(security_check["allowed"]):
                logger.warning(f"Command blocked for security: {command}")
                error_result = str(security_check["message"])

                if db_ops:
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", error_result
                    )

                return error_result

            # Execute command in a controlled environment
            logger.info(f"Starting subprocess for command: {command}")
            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                result = stdout.decode("utf-8", errors="ignore")
                logger.info(
                    f"Command completed successfully for user {user_id}: {command}"
                )
                logger.info(
                    f"Command output (first 200 chars): {result[:200]}..."
                )

                if db_ops:
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", result
                    )

                return result
            else:
                error_msg = stderr.decode("utf-8", errors="ignore")
                logger.error(
                    "Command failed with return code "
                    f"{process.returncode} for user {user_id}: {command}"
                )
                logger.error(f"Command error: {error_msg}")

                error_result = f"Error: {error_msg}"
                if db_ops:
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", error_result
                    )

                return error_result

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing CLI arguments: {e}")
            error_result = f"Error parsing arguments: {str(e)}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            error_result = f"Error executing command: {str(e)}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result
