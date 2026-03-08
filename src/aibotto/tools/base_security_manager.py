"""
Base security manager classes for the AIBOTTO project.
"""

import logging
from abc import ABC
from typing import Any

logger = logging.getLogger(__name__)


class BaseSecurityManager(ABC):
    """Base security manager with common validation logic."""

    def __init__(self, config_class: type, max_length: int | None = None) -> None:
        """Initialize security manager with configuration.

        Args:
            config_class: Configuration class to use
            max_length: Optional maximum length override
        """
        self.config = config_class()
        self._initialize_properties(max_length)

    def _initialize_properties(self, max_length: int | None = None) -> None:
        """Initialize security properties from config."""
        # Common properties
        self.custom_blocked_patterns = self.config.CUSTOM_BLOCKED_PATTERNS
        self.enable_audit_logging = self.config.ENABLE_AUDIT_LOGGING

        # Specific properties to be set by subclasses
        self.blocked_items = self._get_blocked_items()
        self.allowed_items = self._get_allowed_items()
        self.max_length = (
            max_length if max_length is not None else self._get_max_length()
        )

    def _get_blocked_items(self) -> list[str]:
        """Get blocked items list. Override in subclasses."""
        return []

    def _get_allowed_items(self) -> list[str]:
        """Get allowed items list. Override in subclasses."""
        return []

    def _get_max_length(self) -> int:
        """Get maximum length. Override in subclasses."""
        return 0

    async def validate_input(self, input_data: str) -> dict[str, Any]:
        """Template method for input validation.

        Args:
            input_data: Input data to validate

        Returns:
            Dictionary with validation result
        """
        result = {"allowed": False, "message": ""}

        logger.debug(
            f"SECURITY CHECK: Starting validation for input (length: {len(input_data)}, limit: {self.max_length})"
        )
        logger.debug(f"SECURITY CHECK: Input preview: {input_data[:100]}...")

        # Validation steps in order of execution
        validation_steps = [
            self._check_length,
            self._check_blocked_items,
            self._check_custom_patterns,
            self._check_allowed_items,
        ]

        for step in validation_steps:
            check_result = await step(input_data)
            if check_result:
                logger.warning(
                    f"SECURITY CHECK: Blocked by {step.__name__} - {check_result['message']}"
                )
                return check_result

        # All checks passed
        logger.info("SECURITY CHECK: Input PASSED all security checks")
        if self.enable_audit_logging:
            logger.info(f"Input allowed: {input_data[:50]}...")

        result["allowed"] = True
        return result

    async def _check_length(self, input_data: str) -> dict[str, Any] | None:
        """Check input length."""
        if len(input_data) > self.max_length:
            return self._create_blocked_result_dict(
                f"Input too long ({len(input_data)} > {self.max_length} characters)"
            )
        return None

    async def _check_blocked_items(self, input_data: str) -> dict[str, Any] | None:
        """Check for blocked items."""
        if not self.blocked_items:
            return None

        for item in self.blocked_items:
            if item in input_data:
                return self._create_blocked_result_dict(
                    f"Blocked item detected: {item}"
                )
        return None

    async def _check_custom_patterns(self, input_data: str) -> dict[str, Any] | None:
        """Check custom blocked patterns."""
        if not self.custom_blocked_patterns:
            return None

        for pattern in self.custom_blocked_patterns:
            if pattern in input_data:
                return self._create_blocked_result_dict(
                    f"Custom blocked pattern detected: {pattern}"
                )
        return None

    async def _check_allowed_items(self, input_data: str) -> dict[str, Any] | None:
        """Check allowed items whitelist."""
        if not self.allowed_items:
            return None

        for item in self.allowed_items:
            if item in input_data:
                break
        else:
            # No allowed items found
            return self._create_blocked_result_dict("No allowed items found in input")
        return None

    def _create_blocked_result_dict(self, message: str) -> dict[str, Any]:
        """Create standard blocked result."""
        return {"allowed": False, "message": message}

    def reload_security_rules(self, config_file: str = "security_config.json") -> None:
        """Reload security rules from configuration."""
        self.config.reload_from_file(config_file)
        self._initialize_properties()

    def get_security_status(self) -> dict[str, Any]:
        """Get security status."""
        return {
            "blocked_items_count": len(self.blocked_items),
            "allowed_items_count": len(self.allowed_items),
            "custom_patterns_count": len(self.custom_blocked_patterns),
            "max_length": self.max_length,
            "audit_logging_enabled": self.enable_audit_logging,
            "security_rules_summary": self.config.get_security_rules_summary(),
        }
