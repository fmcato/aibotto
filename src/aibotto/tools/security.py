"""
Security manager for CLI command execution.
"""

import logging

from ..config.security_config import SecurityConfig

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manager for security-related operations."""

    def __init__(self) -> None:
        self.blocked_commands = SecurityConfig.BLOCKED_COMMANDS
        self.allowed_commands = SecurityConfig.ALLOWED_COMMANDS
        self.custom_blocked_patterns = SecurityConfig.CUSTOM_BLOCKED_PATTERNS
        self.max_command_length = SecurityConfig.MAX_COMMAND_LENGTH
        self.enable_audit_logging = SecurityConfig.ENABLE_AUDIT_LOGGING

    async def validate_command(self, command: str) -> dict[str, object]:
        """Validate command for security."""
        result = {"allowed": False, "message": ""}

        # Check command length
        if len(command) > self.max_command_length:
            result["message"] = (
                f"Error: Command too long (max {self.max_command_length} characters)"
            )
            if self.enable_audit_logging:
                logger.warning(f"Command blocked for length: {command[:50]}...")
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
                    if self.enable_audit_logging:
                        logger.warning(f"Blocked dangerous command: {command}")
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
                    if self.enable_audit_logging:
                        logger.warning(f"Blocked format command: {command}")
                    return result

        # Check for custom blocked patterns
        for pattern in self.custom_blocked_patterns:
            if pattern and pattern in command_lower:
                result["message"] = (
                    "Error: Command matches blocked pattern for security reasons"
                )
                if self.enable_audit_logging:
                    logger.warning(f"Blocked custom pattern '{pattern}': {command}")
                return result

        # Check if only allowed commands are specified (if whitelist is enabled)
        if self.allowed_commands:
            if not any(
                allowed in command_parts[0] for allowed in self.allowed_commands
            ):
                result["message"] = "Error: Command not in allowed list"
                if self.enable_audit_logging:
                    logger.warning(f"Command not in whitelist: {command}")
                return result

        # If we get here, the command is allowed
        if self.enable_audit_logging:
            logger.info(f"Command allowed: {command[:50]}...")

        result["allowed"] = True
        return result

    def reload_security_rules(self, config_file: str = "security_config.json") -> None:
        """Reload security rules from configuration file."""
        try:
            SecurityConfig.reload_from_file(config_file)
            # Update current instance
            self.blocked_commands = SecurityConfig.BLOCKED_COMMANDS
            self.allowed_commands = SecurityConfig.ALLOWED_COMMANDS
            self.custom_blocked_patterns = SecurityConfig.CUSTOM_BLOCKED_PATTERNS
            self.max_command_length = SecurityConfig.MAX_COMMAND_LENGTH
            self.enable_audit_logging = SecurityConfig.ENABLE_AUDIT_LOGGING

            logger.info("Security rules reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload security rules: {e}")
            raise

    def get_security_status(self) -> dict[str, object]:
        """Get current security configuration status."""
        return {
            "blocked_commands_count": len(self.blocked_commands),
            "allowed_commands_count": len(self.allowed_commands),
            "custom_patterns_count": len(self.custom_blocked_patterns),
            "max_command_length": self.max_command_length,
            "audit_logging_enabled": self.enable_audit_logging,
            "security_rules_summary": SecurityConfig.get_security_rules_summary(),
        }
