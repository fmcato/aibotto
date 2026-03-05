"""
Security manager for CLI command execution.
"""

import logging
from typing import Any

from ..config.security_config import SecurityConfig
from .base_security_manager import BaseSecurityManager

logger = logging.getLogger(__name__)


class SecurityManager(BaseSecurityManager):
    """Manager for security-related operations."""

    def __init__(self, max_length: int | None = None) -> None:
        super().__init__(SecurityConfig, max_length)

    async def validate_command(self, command: str) -> dict[str, Any]:
        """Validate command for security."""
        return await self.validate_input(command)

    # Override specific validation methods for CLI commands
    def _get_blocked_items(self) -> list[str]:
        """Get blocked commands list."""
        return self.config.BLOCKED_COMMANDS
    
    def _get_allowed_items(self) -> list[str]:
        """Get allowed commands list."""
        return self.config.ALLOWED_COMMANDS
    
    def _get_max_length(self) -> int:
        """Get maximum command length."""
        return self.config.MAX_COMMAND_LENGTH
    
    
    async def _check_blocked_items(self, command: str) -> dict[str, Any] | None:
        """Check for blocked commands using precise matching."""
        command_lower = command.lower()
        command_parts = command.strip().split()

        for danger in self.blocked_items:
            # Most dangerous commands should be blocked exactly
            if danger in [
                "rm -rf",
                "sudo",
                "dd",
                "mkfs",
                "fdisk",
                "shutdown",
                "reboot",
                "poweroff",
                "halt",
            ]:
                if danger in command_lower:
                    logger.warning(
                        f"BLOCKED COMMANDS CHECK: MATCHED - found '{danger}' in command"
                    )
                    return self._create_blocked_result_dict(
                        f"Blocked dangerous command: {command}"
                    )
            # Special handling for format-related commands
            elif danger in ["format ", "format=", "format/"]:
                if any(
                    part.startswith(("format", "/format")) for part in command_parts
                ):
                    logger.warning(
                        "BLOCKED COMMANDS CHECK: MATCHED - found format-related command"
                    )
                    return self._create_blocked_result_dict(
                        f"Blocked format command: {command}"
                    )
            # All other blocked commands - check if contained in command
            elif danger in command_lower:
                logger.warning(
                    f"BLOCKED COMMANDS CHECK: MATCHED - found '{danger}' in command (substring match)"
                )
                return self._create_blocked_result_dict(
                    f"Blocked command: {command}"
                )

        logger.debug("BLOCKED COMMANDS CHECK: PASSED - no blocked commands found")
        return None
    
    async def _check_allowed_items(self, command: str) -> dict[str, Any] | None:
        """Check if command is in allowed whitelist (if enabled)."""
        if not self.allowed_items:
            return None

        command_parts = command.strip().split()
        if not any(allowed in command_parts[0] for allowed in self.allowed_items):
            message = "Error: Command not in allowed list"
            if self.enable_audit_logging:
                logger.warning(f"Command not in whitelist: {command}")
            return self._create_blocked_result_dict(message)

        return None
