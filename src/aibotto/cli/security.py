"""
Security manager for CLI command execution.
"""

import logging

from ..config.settings import Config

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manager for security-related operations."""

    def __init__(self):
        self.blocked_commands = Config.BLOCKED_COMMANDS
        self.allowed_commands = Config.ALLOWED_COMMANDS

    async def validate_command(self, command: str) -> dict[str, bool]:
        """Validate command for security."""
        result = {"allowed": False, "message": ""}

        # Check command length
        if len(command) > Config.MAX_COMMAND_LENGTH:
            result["message"] = (
                f"Error: Command too long (max {Config.MAX_COMMAND_LENGTH} characters)"
            )
            return result

        # Check for blocked commands using more precise matching
        command_lower = command.lower()
        command_parts = command.strip().split()

        # Check for exact blocked command matches
        for danger in self.blocked_commands:
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
                # These are dangerous commands that should be blocked exactly
                if danger in command_lower:
                    result["message"] = (
                        "Error: Command not allowed for security reasons"
                    )
                    return result
            elif danger in ["format ", "format=", "format/"]:
                # Special handling for format-related commands
                # Check if it's actually a format command (not URL parameter)
                if any(
                    part.startswith(("format", "/format")) for part in command_parts
                ):
                    result["message"] = (
                        "Error: Command not allowed for security reasons"
                    )
                    return result

        # Check if only allowed commands are specified (if whitelist is enabled)
        if self.allowed_commands:
            if not any(
                allowed in command_parts[0] for allowed in self.allowed_commands
            ):
                result["message"] = "Error: Command not in allowed list"
                return result

        result["allowed"] = True
        return result
