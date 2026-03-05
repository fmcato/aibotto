"""
CLI security configuration for the application.
"""

import os
from typing import Any

from .base_security_config import BaseSecurityConfig


class CLISecurityConfig(BaseSecurityConfig):
    """Security configuration for CLI commands."""

    # Maximum command length allowed for CLI commands
    MAX_COMMAND_LENGTH: int = int(os.getenv("MAX_COMMAND_LENGTH", "300000"))

    # Whitelist of allowed commands (empty = no whitelist)
    ALLOWED_COMMANDS: list[str] = (
        os.getenv("ALLOWED_COMMANDS", "").split(",")
        if os.getenv("ALLOWED_COMMANDS")
        else []
    )

    # Blacklist of blocked commands
    BLOCKED_COMMANDS: list[str] = [
        "rm -rf",
        "sudo",
        "dd",
        "mkfs",
        "fdisk",
        "format ",
        "format=",
        "format/",
        "shutdown",
        "reboot",
        "poweroff",
        "halt",
    ]

    @classmethod
    def _apply_config(cls, config: dict[str, Any]) -> None:
        """Apply configuration values."""
        if "MAX_COMMAND_LENGTH" in config:
            cls.MAX_COMMAND_LENGTH = config["MAX_COMMAND_LENGTH"]
        if "ALLOWED_COMMANDS" in config:
            cls.ALLOWED_COMMANDS = config["ALLOWED_COMMANDS"]
        if "BLOCKED_COMMANDS" in config:
            cls.BLOCKED_COMMANDS = config["BLOCKED_COMMANDS"]

    @classmethod
    def _get_specific_summary(cls) -> dict[str, Any]:
        """Get security rules summary for specific subclass."""
        return {
            "max_command_length": cls.MAX_COMMAND_LENGTH,
            "allowed_commands_count": len(cls.ALLOWED_COMMANDS),
            "blocked_commands_count": len(cls.BLOCKED_COMMANDS),
            "has_whitelist": bool(cls.ALLOWED_COMMANDS),
        }
