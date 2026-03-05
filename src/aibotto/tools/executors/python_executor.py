"""
Python code executor with relaxed length limits.
"""

import asyncio
import json
import logging

from ...db.operations import DatabaseOperations
from ...tools.python_security_manager import PythonSecurityManager
from ..base import ToolExecutor

logger = logging.getLogger(__name__)


class PythonExecutor(ToolExecutor):
    """Executor for Python code execution with higher length limits."""

    def __init__(self) -> None:
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

    async def execute(
        self,
        arguments: str,
        user_id: int = 0,
        db_ops: DatabaseOperations | None = None,
        chat_id: int = 0,
    ) -> str:
        """Execute Python code safely and return output.

        Args:
            arguments: JSON string with 'code' field containing Python code
            user_id: User ID for logging
            db_ops: Database operations instance
            chat_id: Chat ID for database operations

        Returns:
            Execution result as string
        """
        try:
            args = json.loads(arguments)
            code = args.get("code")

            if not code:
                raise ValueError("No code provided")

            logger.info(f"Executing Python code for user {user_id}")

            # Validate Python code (raw code length, not wrapped command)
            security_check = await self.security_manager.validate_python_code(code)
            if not bool(security_check["allowed"]):
                logger.warning(f"Python code blocked for security: {code[:100]}...")
                error_result = str(security_check["message"])

                if db_ops:
                    await db_ops.save_message_compat(
                        user_id=user_id,
                        chat_id=chat_id,
                        role="system",
                        content=error_result,
                    )

                return error_result

            # Wrap the code after validation for execution
            command = self._wrap_python_code(code)

            logger.info("Starting subprocess for Python execution")

            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                result = stdout.decode("utf-8", errors="ignore")
                logger.info(
                    f"Python code executed successfully for user {user_id}: {result[:200]}..."
                )

                if db_ops:
                    await db_ops.save_message_compat(
                        user_id=user_id, chat_id=chat_id, role="system", content=result
                    )

                return result
            else:
                error_msg = stderr.decode("utf-8", errors="ignore")
                logger.error(
                    f"Python execution failed with return code "
                    f"{process.returncode} for user {user_id}"
                )
                logger.error(f"Python error: {error_msg}")

                error_result = f"Error: {error_msg}"
                if db_ops:
                    await db_ops.save_message_compat(
                        user_id=user_id,
                        chat_id=chat_id,
                        role="system",
                        content=error_result,
                    )

                return error_result

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Python arguments: {e}")
            error_result = f"Error parsing arguments: {str(e)}"
            if db_ops:
                await db_ops.save_message_compat(
                    user_id=user_id,
                    chat_id=chat_id,
                    role="system",
                    content=error_result,
                )
            return error_result
        except Exception as e:
            logger.error(f"Python execution error: {e}")
            error_result = f"Error executing Python code: {str(e)}"
            if db_ops:
                await db_ops.save_message_compat(
                    user_id=user_id,
                    chat_id=chat_id,
                    role="system",
                    content=error_result,
                )
            return error_result
