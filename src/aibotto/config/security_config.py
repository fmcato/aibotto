"""
Security configuration for the application.
"""

import os


class SecurityConfig:
    """Security configuration for the application."""

    # Maximum command length allowed
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

    # Custom blocked patterns (for dynamic security rules)
    CUSTOM_BLOCKED_PATTERNS: list[str] = (
        os.getenv("CUSTOM_BLOCKED_PATTERNS", "").split(",")
        if os.getenv("CUSTOM_BLOCKED_PATTERNS")
        else []
    )

    # Security audit logging
    ENABLE_AUDIT_LOGGING: bool = (
            os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
        )

    @classmethod
    def reload_from_file(cls, config_file: str = "security_config.json") -> None:
        """Reload security configuration from file."""
        try:
            import json
            if os.path.exists(config_file):
                with open(config_file) as f:
                    config = json.load(f)

                # Update configuration values
                cls.MAX_COMMAND_LENGTH = config.get(
                    "MAX_COMMAND_LENGTH", cls.MAX_COMMAND_LENGTH
                )
                cls.ALLOWED_COMMANDS = config.get(
                    "ALLOWED_COMMANDS", cls.ALLOWED_COMMANDS
                )
                cls.BLOCKED_COMMANDS = config.get(
                    "BLOCKED_COMMANDS", cls.BLOCKED_COMMANDS
                )
                cls.CUSTOM_BLOCKED_PATTERNS = config.get(
                    "CUSTOM_BLOCKED_PATTERNS", cls.CUSTOM_BLOCKED_PATTERNS
                )
                cls.ENABLE_AUDIT_LOGGING = config.get(
                    "ENABLE_AUDIT_LOGGING", cls.ENABLE_AUDIT_LOGGING
                )

        except Exception as e:
            print(f"Warning: Could not reload security config from file: {e}")

    @classmethod
    def get_security_rules_summary(cls) -> dict:
        """Get summary of current security rules."""
        return {
            "max_command_length": cls.MAX_COMMAND_LENGTH,
            "allowed_commands_count": len(cls.ALLOWED_COMMANDS),
            "blocked_commands_count": len(cls.BLOCKED_COMMANDS),
            "custom_blocked_patterns_count": len(cls.CUSTOM_BLOCKED_PATTERNS),
            "audit_logging_enabled": cls.ENABLE_AUDIT_LOGGING,
            "has_whitelist": bool(cls.ALLOWED_COMMANDS),
        }
