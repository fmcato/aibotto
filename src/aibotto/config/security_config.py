"""
Security configuration for the application.
"""

from typing import Any

from .base_security_config import BaseSecurityConfig
from .env_loader import EnvLoader


class SecurityConfig(BaseSecurityConfig):
    """Security configuration for the application."""

    # Maximum command length allowed
    MAX_COMMAND_LENGTH: int = EnvLoader.get_int("MAX_COMMAND_LENGTH", 300000)

    # Maximum Python code length allowed (higher than general commands)
    MAX_PYTHON_CODE_LENGTH: int = EnvLoader.get_int("MAX_PYTHON_CODE_LENGTH", 60000)

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
        if "MAX_PYTHON_CODE_LENGTH" in config:
            cls.MAX_PYTHON_CODE_LENGTH = config["MAX_PYTHON_CODE_LENGTH"]
        if "ALLOWED_COMMANDS" in config:
            cls.ALLOWED_COMMANDS = config["ALLOWED_COMMANDS"]
        if "BLOCKED_COMMANDS" in config:
            cls.BLOCKED_COMMANDS = config["BLOCKED_COMMANDS"]

    @classmethod
    def _get_specific_summary(cls) -> dict[str, Any]:
        """Get security rules summary for specific subclass."""
        return {
            "max_command_length": cls.MAX_COMMAND_LENGTH,
            "max_python_code_length": cls.MAX_PYTHON_CODE_LENGTH,
            "allowed_commands_count": len(cls.ALLOWED_COMMANDS),
            "blocked_commands_count": len(cls.BLOCKED_COMMANDS),
            "has_whitelist": bool(cls.ALLOWED_COMMANDS),
        }
