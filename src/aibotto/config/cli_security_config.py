"""
CLI security configuration for the application.
"""

from typing import Any

from .base_security_config import BaseSecurityConfig
from .env_loader import EnvLoader


class CLISecurityConfig(BaseSecurityConfig):
    """Security configuration for CLI commands."""

    # Maximum command length allowed for CLI commands
    MAX_COMMAND_LENGTH: int = EnvLoader.get_int("MAX_COMMAND_LENGTH", 300000)

    # Whitelist of allowed commands (empty = no whitelist)
    ALLOWED_COMMANDS: list[str] = EnvLoader.get_list("ALLOWED_COMMANDS")

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
