"""Direct Python code executor without subprocess overhead."""

import asyncio
import io
import logging
import sys
import time
from typing import Any

from ...db.operations import DatabaseOperations
from ..base import ToolExecutor

logger = logging.getLogger(__name__)


class PythonDirectExecutor(ToolExecutor):
    """Direct Python code execution without subprocess overhead."""

    def __init__(self) -> None:
        self.timeout_seconds = 45

    async def execute(
        self,
        arguments: str,
        user_id: int = 0,
        db_ops: DatabaseOperations | None = None,
        chat_id: int = 0,
    ) -> str:
        """Execute Python code directly with timeout.

        Args:
            arguments: Raw Python code (not JSON-wrapped)
            user_id: User ID for logging
            db_ops: Database operations instance
            chat_id: Chat ID for database operations

        Returns:
            Execution stdout or error message
        """
        start_time = time.time()

        if not arguments or not arguments.strip():
            result = "Error: Empty code - whitespace or empty string provided"
            logger.warning(f"Python execution: empty code for user {user_id}")
            return result

        python_code = arguments.strip()

        logger.info(f"Executing Python code for user {user_id} ({len(python_code)} chars)")

        try:
            result = await self._execute_with_timeout(python_code)

            elapsed = time.time() - start_time
            logger.info(
                f"Python execution completed for user {user_id} in {elapsed:.3f}s"
            )

            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", result)

            return result

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            error_result = f"Error: Timeout after {self.timeout_seconds} seconds"
            logger.warning(
                f"Python execution timed out for user {user_id} after {elapsed:.3f}s"
            )
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result

        except Exception as e:
            elapsed = time.time() - start_time
            error_type = type(e).__name__
            error_msg = str(e)[:100] if str(e) else ""
            error_result = f"Error: {error_type}"
            if error_msg:
                error_result += f": {error_msg}"

            logger.error(
                f"Python execution error for user {user_id} after {elapsed:.3f}s: "
                f"{error_type}: {error_msg}"
            )

            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)

            return error_result

    async def _execute_with_timeout(self, code: str) -> str:
        """Execute Python code with timeout and stdout capture.

        Args:
            code: Python code to execute

        Returns:
            Captured stdout or status message

        Raises:
            asyncio.TimeoutError: If execution exceeds timeout
        """
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        namespace: dict[str, Any] = {}

        try:
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, self._exec_code_sync, code, namespace
                ),
                timeout=self.timeout_seconds,
            )

            output = sys.stdout.getvalue()
            return output.strip() if output.strip() else "Script executed but produced no output"

        finally:
            sys.stdout = old_stdout

    def _exec_code_sync(self, code: str, namespace: dict[str, Any]) -> None:
        """Execute Python code synchronously.
        
        Args:
            code: Python code to execute
            namespace: Execution namespace
        
        Note: Using exec is intentional - this is a Python code executor tool.
        Security is handled by restricting command execution through CLI tool validation.
        """
        # Basic builtins for Python execution
        namespace.update({
            "__builtins__": __builtins__,
        })
        
        # nosemgrep: python.lang.security.audit.dangerous-exec-use.dangerous-exec-use
        exec(code, namespace)
