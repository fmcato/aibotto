"""
Base security configuration classes for the AIBOTTO project.
"""

import os
from abc import ABC, abstractmethod
from typing import Any

from .env_loader import EnvLoader


class BaseSecurityConfig(ABC):
    """Base security configuration with common functionality."""

    # Common properties
    CUSTOM_BLOCKED_PATTERNS: list[str] = EnvLoader.get_list(
        "CUSTOM_BLOCKED_PATTERNS"
    )
    ENABLE_AUDIT_LOGGING: bool = EnvLoader.get_bool("ENABLE_AUDIT_LOGGING", True)

    @classmethod
    def reload_from_file(cls, config_file: str) -> None:
        """Reload security configuration from file.
        
        Args:
            config_file: Path to configuration file
        """
        try:
            import json

            if os.path.exists(config_file):
                with open(config_file) as f:
                    config = json.load(f)
                
                # Apply configuration values
                cls._apply_config(config)
                
        except Exception as e:
            print(f"Warning: Could not reload {cls.__name__} config from file: {e}")

    @classmethod
    @abstractmethod
    def _apply_config(cls, config: dict[str, Any]) -> None:
        """Apply configuration values. Must be implemented by subclasses."""
        pass

    @classmethod
    def get_security_rules_summary(cls) -> dict[str, Any]:
        """Get security rules summary.
        
        Returns:
            Dictionary containing security rules summary
        """
        return cls._get_base_summary() | cls._get_specific_summary()

    @classmethod
    def _get_base_summary(cls) -> dict[str, Any]:
        """Get common security rules summary.
        
        Returns:
            Common security rules
        """
        return {
            "custom_blocked_patterns_count": len(cls.CUSTOM_BLOCKED_PATTERNS),
            "audit_logging_enabled": cls.ENABLE_AUDIT_LOGGING,
        }

    @classmethod
    @abstractmethod
    def _get_specific_summary(cls) -> dict[str, Any]:
        """Get security rules summary for specific subclass.
        
        Returns:
            Specific security rules
        """
        pass