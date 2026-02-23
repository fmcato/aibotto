"""
CLI command executor with safety measures.
"""

import asyncio
import logging
import shlex

from .security import SecurityManager

logger = logging.getLogger(__name__)


def _parse_command_args(command: str) -> list[str]:
    """Parse command string into arguments list.

    Args:
        command: Command string to parse

    Returns:
        List of arguments

    Raises:
        ValueError: If command is empty or invalid
    """
    if not command or not command.strip():
        raise ValueError("Empty command")

    try:
        # Use shlex to properly handle quoted arguments and escape sequences
        return shlex.split(command)
    except ValueError as e:
        raise ValueError(f"Invalid command format: {e}")


def _sanitize_args(args: list[str]) -> list[str]:
    """Sanitize command arguments to prevent injection.

    Args:
        args: List of command arguments

    Returns:
        Sanitized arguments list
    """
    sanitized = []
    for arg in args:
        # Remove any shell metacharacters that could be dangerous
        sanitized_arg = "".join(c for c in arg if c not in r'`$(){}[];&|*?<>~"\\')
        if sanitized_arg:  # Only add non-empty arguments
            sanitized.append(sanitized_arg)
    return sanitized


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
                return str(security_check["message"])

            # Parse and sanitize command arguments
            try:
                args = _parse_command_args(command)
                sanitized_args = _sanitize_args(args)
                executable = sanitized_args[0]
                if len(sanitized_args) > 1:
                    cmd_args = sanitized_args[1:]
                else:
                    cmd_args = []
            except ValueError as e:
                logger.error(f"Command parsing error: {e}")
                return f"Error: Invalid command format: {e}"

            # Execute command in a controlled environment using subprocess_exec
            logger.info(
                    f"Starting subprocess for executable: {executable}"
                    f" with args: {cmd_args}"
                )
            process = await asyncio.create_subprocess_exec(
                executable, *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
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

    def reload_security_rules(self, config_file: str = "security_config.json") -> None:
        """Reload security rules from configuration file."""
        try:
            self.security_manager.reload_security_rules(config_file)
            logger.info("CLI executor security rules reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload CLI executor security rules: {e}")
            raise

    def get_security_status(self) -> dict[str, object]:
        """Get current security status."""
        return self.security_manager.get_security_status()
