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
        length_check = await self._check_command_length(command)
        if length_check:
            return length_check

        # Check blocked commands
        blocked_check = await self._check_blocked_commands(command)
        if blocked_check:
            return blocked_check

        # Check custom blocked patterns
        pattern_check = await self._check_custom_patterns(command)
        if pattern_check:
            return pattern_check

        # Check allowed commands whitelist
        whitelist_check = await self._check_allowed_commands(command)
        if whitelist_check:
            return whitelist_check

        # Command is allowed
        if self.enable_audit_logging:
            logger.info(f"Command allowed: {command[:50]}...")

        result["allowed"] = True
        return result

    async def _check_command_length(self, command: str) -> dict[str, object] | None:
        """Check if command length exceeds maximum."""
        if len(command) > self.max_command_length:
            message = f"Error: Command too long (max {self.max_command_length} characters)"
            if self.enable_audit_logging:
                logger.warning(f"Command blocked for length: {command[:50]}...")
            return self._create_blocked_result_dict(message)
        return None

    async def _check_blocked_commands(self, command: str) -> dict[str, object] | None:
        """Check for blocked commands using precise matching."""
        command_lower = command.lower()
        command_parts = command.strip().split()

        for danger in self.blocked_commands:
            # Most dangerous commands should be blocked exactly
            if danger in ["rm -rf", "sudo", "dd", "mkfs", "fdisk", "shutdown", "reboot", "poweroff", "halt"]:
                if danger in command_lower:
                    return self._create_blocked_result(
                        f"Blocked dangerous command: {command}", danger
                    )
            # Special handling for format-related commands
            elif danger in ["format ", "format=", "format/"]:
                if any(part.startswith(("format", "/format")) for part in command_parts):
                    return self._create_blocked_result(
                        f"Blocked format command: {command}", "format"
                    )
            # All other blocked commands - check if contained in command
            elif danger in command_lower:
                return self._create_blocked_result(
                    f"Blocked command: {command}", danger
                )

        return None

    async def _check_custom_patterns(self, command: str) -> dict[str, object] | None:
        """Check for custom blocked patterns."""
        command_lower = command.lower()

        for pattern in self.custom_blocked_patterns:
            if pattern and pattern in command_lower:
                message = "Error: Command matches blocked pattern for security reasons"
                if self.enable_audit_logging:
                    logger.warning(f"Blocked custom pattern '{pattern}': {command}")
                return self._create_blocked_result_dict(message)

        return None

    async def _check_allowed_commands(self, command: str) -> dict[str, object] | None:
        """Check if command is in allowed whitelist (if enabled)."""
        if not self.allowed_commands:
            return None

        command_parts = command.strip().split()
        if not any(
            allowed in command_parts[0] for allowed in self.allowed_commands
        ):
            message = "Error: Command not in allowed list"
            if self.enable_audit_logging:
                logger.warning(f"Command not in whitelist: {command}")
            return self._create_blocked_result_dict(message)

        return None

    def _create_blocked_result_dict(self, message: str) -> dict[str, object]:
        """Create a standard blocked command result dict."""
        return {
            "allowed": False,
            "message": message
        }

    def _create_blocked_result(
        self, log_message: str, danger_type: str
    ) -> dict[str, object]:
        """Create a standard blocked command result."""
        if self.enable_audit_logging:
            logger.warning(log_message)
        return self._create_blocked_result_dict("Error: Command not allowed for security reasons")

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
