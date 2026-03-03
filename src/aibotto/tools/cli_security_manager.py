"""
CLI security manager for command execution.
"""

import logging

from ..config.cli_security_config import CLISecurityConfig

logger = logging.getLogger(__name__)


class CLISecurityManager:
    """Manager for CLI command security operations."""

    def __init__(self) -> None:
        self.config = CLISecurityConfig()
        self.blocked_commands = self.config.BLOCKED_COMMANDS
        self.allowed_commands = self.config.ALLOWED_COMMANDS
        self.custom_blocked_patterns = self.config.CUSTOM_BLOCKED_PATTERNS
        self.max_command_length = self.config.MAX_COMMAND_LENGTH
        self.enable_audit_logging = self.config.ENABLE_AUDIT_LOGGING

    async def validate_command(self, command: str) -> dict[str, object]:
        """Validate CLI command for security."""
        result = {"allowed": False, "message": ""}

        logger.debug(f"CLI SECURITY CHECK: Starting validation for command (length: {len(command)}, limit: {self.max_command_length})")
        logger.debug(f"CLI SECURITY CHECK: Command preview: {command[:100]}...")

        # Check command length
        length_check = await self._check_command_length(command)
        if length_check:
            logger.warning(f"CLI SECURITY CHECK: Blocked by length check - {length_check['message']}")
            return length_check

        # Check blocked commands
        blocked_check = await self._check_blocked_commands(command)
        if blocked_check:
            logger.warning(f"CLI SECURITY CHECK: Blocked by command check - {blocked_check['message']}")
            return blocked_check

        # Check custom blocked patterns
        pattern_check = await self._check_custom_patterns(command)
        if pattern_check:
            logger.warning(f"CLI SECURITY CHECK: Blocked by pattern check - {pattern_check['message']}")
            return pattern_check

        # Check allowed commands whitelist
        whitelist_check = await self._check_allowed_commands(command)
        if whitelist_check:
            logger.warning(f"CLI SECURITY CHECK: Blocked by whitelist check - {whitelist_check['message']}")
            return whitelist_check

        # Command is allowed
        logger.info("CLI SECURITY CHECK: Command PASSED all security checks")
        if self.enable_audit_logging:
            logger.info(f"CLI Command allowed: {command[:50]}...")

        result["allowed"] = True
        return result

    async def _check_command_length(self, command: str) -> dict[str, object] | None:
        """Check if command length exceeds maximum."""
        logger.debug(f"CLI LENGTH CHECK: Command length={len(command)}, max={self.max_command_length}")
        if len(command) > self.max_command_length:
            message = (
                f"Error: Command too long (max {self.max_command_length} characters)"
            )
            if self.enable_audit_logging:
                logger.warning(f"CLI Command blocked for length: {command[:50]}...")
            return self._create_blocked_result_dict(message)
        logger.debug("CLI LENGTH CHECK: PASSED")
        return None

    async def _check_blocked_commands(self, command: str) -> dict[str, object] | None:
        """Check for blocked commands using precise matching."""
        command_lower = command.lower()
        command_parts = command.strip().split()

        logger.debug(f"CLI BLOCKED COMMANDS CHECK: Checking {len(self.blocked_commands)} blocked patterns")

        for danger in self.blocked_commands:
            logger.debug(f"CLI BLOCKED COMMANDS CHECK: Checking against blocked pattern: '{danger}'")
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
                    logger.warning(f"CLI BLOCKED COMMANDS CHECK: MATCHED - found '{danger}' in command")
                    return self._create_blocked_result(
                        f"Blocked dangerous command: {command}", danger
                    )
            # Special handling for format-related commands
            elif danger in ["format ", "format=", "format/"]:
                if any(
                    part.startswith(("format", "/format")) for part in command_parts
                ):
                    logger.warning("CLI BLOCKED COMMANDS CHECK: MATCHED - found format-related command")
                    return self._create_blocked_result(
                        f"Blocked format command: {command}", "format"
                    )
            # All other blocked commands - check if contained in command
            elif danger in command_lower:
                logger.warning(f"CLI BLOCKED COMMANDS CHECK: MATCHED - found '{danger}' in command (substring match)")
                return self._create_blocked_result(
                    f"Blocked command: {command}", danger
                )

        logger.debug("CLI BLOCKED COMMANDS CHECK: PASSED - no blocked commands found")
        return None

    async def _check_custom_patterns(self, command: str) -> dict[str, object] | None:
        """Check for custom blocked patterns."""
        command_lower = command.lower()

        for pattern in self.custom_blocked_patterns:
            if pattern and pattern in command_lower:
                message = "Error: Command matches blocked pattern for security reasons"
                if self.enable_audit_logging:
                    logger.warning(f"CLI Blocked custom pattern '{pattern}': {command}")
                return self._create_blocked_result_dict(message)

        return None

    async def _check_allowed_commands(self, command: str) -> dict[str, object] | None:
        """Check if command is in allowed whitelist (if enabled)."""
        if not self.allowed_commands:
            return None

        command_parts = command.strip().split()
        if not any(allowed in command_parts[0] for allowed in self.allowed_commands):
            message = "Error: Command not in allowed list"
            if self.enable_audit_logging:
                logger.warning(f"CLI Command not in whitelist: {command}")
            return self._create_blocked_result_dict(message)

        return None

    def _create_blocked_result_dict(self, message: str) -> dict[str, object]:
        """Create a standard blocked command result dict."""
        return {"allowed": False, "message": message}

    def _create_blocked_result(self, message: str, danger: str) -> dict[str, object]:
        """Create a blocked command result dict."""
        return {"allowed": False, "message": message}