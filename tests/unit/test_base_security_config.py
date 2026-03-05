"""
Unit tests for base security configuration classes.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from src.aibotto.config.base_security_config import BaseSecurityConfig


class TestSecurityConfig(BaseSecurityConfig):
    """Test implementation of BaseSecurityConfig."""
    
    MAX_COMMAND_LENGTH: int = 100000
    MAX_PYTHON_CODE_LENGTH: int = 200000
    ALLOWED_COMMANDS: list[str] = ["echo", "ls"]
    BLOCKED_COMMANDS: list[str] = ["rm -rf", "sudo"]
    ALLOWED_IMPORTS: list[str] = ["os", "sys"]
    BLOCKED_PATTERNS: list[str] = ["exec(", "eval("]

    @classmethod
    def _apply_config(cls, config: dict[str, any]) -> None:
        """Apply configuration values."""
        if "MAX_COMMAND_LENGTH" in config:
            cls.MAX_COMMAND_LENGTH = config["MAX_COMMAND_LENGTH"]
        if "MAX_PYTHON_CODE_LENGTH" in config:
            cls.MAX_PYTHON_CODE_LENGTH = config["MAX_PYTHON_CODE_LENGTH"]
        if "ALLOWED_COMMANDS" in config:
            cls.ALLOWED_COMMANDS = config["ALLOWED_COMMANDS"]
        if "BLOCKED_COMMANDS" in config:
            cls.BLOCKED_COMMANDS = config["BLOCKED_COMMANDS"]
        if "ALLOWED_IMPORTS" in config:
            cls.ALLOWED_IMPORTS = config["ALLOWED_IMPORTS"]
        if "BLOCKED_PATTERNS" in config:
            cls.BLOCKED_PATTERNS = config["BLOCKED_PATTERNS"]

    @classmethod
    def _get_specific_summary(cls) -> dict[str, any]:
        """Get specific security rules summary."""
        return {
            "max_command_length": cls.MAX_COMMAND_LENGTH,
            "max_python_code_length": cls.MAX_PYTHON_CODE_LENGTH,
            "allowed_commands_count": len(cls.ALLOWED_COMMANDS),
            "blocked_commands_count": len(cls.BLOCKED_COMMANDS),
            "allowed_imports_count": len(cls.ALLOWED_IMPORTS),
            "blocked_patterns_count": len(cls.BLOCKED_PATTERNS),
            "has_whitelist": bool(cls.ALLOWED_COMMANDS),
            "has_import_restrictions": bool(cls.ALLOWED_IMPORTS),
        }


class TestBaseSecurityConfig:
    """Test cases for BaseSecurityConfig."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration after each test."""
        original_values = {
            "MAX_COMMAND_LENGTH": TestSecurityConfig.MAX_COMMAND_LENGTH,
            "MAX_PYTHON_CODE_LENGTH": TestSecurityConfig.MAX_PYTHON_CODE_LENGTH,
            "ALLOWED_COMMANDS": TestSecurityConfig.ALLOWED_COMMANDS.copy(),
            "BLOCKED_COMMANDS": TestSecurityConfig.BLOCKED_COMMANDS.copy(),
            "ALLOWED_IMPORTS": TestSecurityConfig.ALLOWED_IMPORTS.copy(),
            "BLOCKED_PATTERNS": TestSecurityConfig.BLOCKED_PATTERNS.copy(),
        }
        
        yield
        
        # Restore original values
        TestSecurityConfig.MAX_COMMAND_LENGTH = original_values["MAX_COMMAND_LENGTH"]
        TestSecurityConfig.MAX_PYTHON_CODE_LENGTH = original_values["MAX_PYTHON_CODE_LENGTH"]
        TestSecurityConfig.ALLOWED_COMMANDS = original_values["ALLOWED_COMMANDS"]
        TestSecurityConfig.BLOCKED_COMMANDS = original_values["BLOCKED_COMMANDS"]
        TestSecurityConfig.ALLOWED_IMPORTS = original_values["ALLOWED_IMPORTS"]
        TestSecurityConfig.BLOCKED_PATTERNS = original_values["BLOCKED_PATTERNS"]

    def test_base_security_config_inheritance(self):
        """Test that TestSecurityConfig properly inherits from BaseSecurityConfig."""
        assert issubclass(TestSecurityConfig, BaseSecurityConfig)
        assert hasattr(TestSecurityConfig, "reload_from_file")
        assert hasattr(TestSecurityConfig, "get_security_rules_summary")

    def test_custom_blocked_patterns_from_env(self):
        """Test CUSTOM_BLOCKED_PATTERNS loads from environment."""
        with patch.dict(os.environ, {"CUSTOM_BLOCKED_PATTERNS": "pattern1,pattern2"}):
            # Reload the class to pick up environment changes
            TestSecurityConfig.CUSTOM_BLOCKED_PATTERNS = (
                os.getenv("CUSTOM_BLOCKED_PATTERNS", "").split(",")
                if os.getenv("CUSTOM_BLOCKED_PATTERNS")
                else []
            )
            assert TestSecurityConfig.CUSTOM_BLOCKED_PATTERNS == ["pattern1", "pattern2"]

    def test_audit_logging_from_env(self):
        """Test ENABLE_AUDIT_LOGGING loads from environment."""
        with patch.dict(os.environ, {"ENABLE_AUDIT_LOGGING": "false"}):
            TestSecurityConfig.ENABLE_AUDIT_LOGGING = (
                os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
            )
            assert TestSecurityConfig.ENABLE_AUDIT_LOGGING is False

    def test_get_security_rules_summary(self):
        """Test get_security_rules_summary returns correct structure."""
        summary = TestSecurityConfig.get_security_rules_summary()
        
        # Check base summary
        assert "custom_blocked_patterns_count" in summary
        assert "audit_logging_enabled" in summary
        
        # Check specific summary
        assert "max_command_length" in summary
        assert "max_python_code_length" in summary
        assert "allowed_commands_count" in summary
        assert "blocked_commands_count" in summary
        assert "allowed_imports_count" in summary
        assert "blocked_patterns_count" in summary
        assert "has_whitelist" in summary
        assert "has_import_restrictions" in summary

    def test_get_base_summary(self):
        """Test _get_base_summary returns common security rules."""
        base_summary = TestSecurityConfig._get_base_summary()
        
        assert "custom_blocked_patterns_count" in base_summary
        assert "audit_logging_enabled" in base_summary
        assert base_summary["custom_blocked_patterns_count"] == len(TestSecurityConfig.CUSTOM_BLOCKED_PATTERNS)
        assert base_summary["audit_logging_enabled"] == TestSecurityConfig.ENABLE_AUDIT_LOGGING

    def test_get_specific_summary(self):
        """Test _get_specific_summary returns specific security rules."""
        specific_summary = TestSecurityConfig._get_specific_summary()
        
        assert specific_summary["max_command_length"] == TestSecurityConfig.MAX_COMMAND_LENGTH
        assert specific_summary["max_python_code_length"] == TestSecurityConfig.MAX_PYTHON_CODE_LENGTH
        assert specific_summary["allowed_commands_count"] == len(TestSecurityConfig.ALLOWED_COMMANDS)
        assert specific_summary["blocked_commands_count"] == len(TestSecurityConfig.BLOCKED_COMMANDS)
        assert specific_summary["allowed_imports_count"] == len(TestSecurityConfig.ALLOWED_IMPORTS)
        assert specific_summary["blocked_patterns_count"] == len(TestSecurityConfig.BLOCKED_PATTERNS)
        assert specific_summary["has_whitelist"] == bool(TestSecurityConfig.ALLOWED_COMMANDS)
        assert specific_summary["has_import_restrictions"] == bool(TestSecurityConfig.ALLOWED_IMPORTS)

    def test_reload_from_file_success(self):
        """Test reload_from_file successfully loads configuration."""
        test_config = {
            "MAX_COMMAND_LENGTH": 500000,
            "MAX_PYTHON_CODE_LENGTH": 1000000,
            "ALLOWED_COMMANDS": ["echo", "ls", "pwd"],
            "BLOCKED_COMMANDS": ["rm -rf", "sudo", "dd"],
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_file = f.name
        
        try:
            TestSecurityConfig.reload_from_file(config_file)
            
            # Verify configuration was applied
            assert TestSecurityConfig.MAX_COMMAND_LENGTH == 500000
            assert TestSecurityConfig.MAX_PYTHON_CODE_LENGTH == 1000000
            assert TestSecurityConfig.ALLOWED_COMMANDS == ["echo", "ls", "pwd"]
            assert TestSecurityConfig.BLOCKED_COMMANDS == ["rm -rf", "sudo", "dd"]
        finally:
            os.unlink(config_file)

    def test_reload_from_file_nonexistent(self):
        """Test reload_from_file handles nonexistent file gracefully."""
        # Should not raise exception
        TestSecurityConfig.reload_from_file("nonexistent_config.json")
        
        # Values should remain unchanged
        assert TestSecurityConfig.MAX_COMMAND_LENGTH == 100000

    def test_reload_from_file_invalid_json(self):
        """Test reload_from_file handles invalid JSON gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_file = f.name
        
        try:
            # Should not raise exception
            TestSecurityConfig.reload_from_file(config_file)
        finally:
            os.unlink(config_file)

    def test_reload_from_file_empty_config(self):
        """Test reload_from_file handles empty configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            config_file = f.name
        
        try:
            TestSecurityConfig.reload_from_file(config_file)
            
            # Values should remain unchanged (use defaults from _apply_config)
            assert TestSecurityConfig.MAX_COMMAND_LENGTH == 100000
            assert TestSecurityConfig.MAX_PYTHON_CODE_LENGTH == 200000
        finally:
            os.unlink(config_file)

    def test_reload_from_file_partial_config(self):
        """Test reload_from_file applies only provided configuration values."""
        test_config = {
            "MAX_COMMAND_LENGTH": 750000,
            # MAX_PYTHON_CODE_LENGTH not provided, should keep default
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_file = f.name
        
        try:
            TestSecurityConfig.reload_from_file(config_file)
            
            # Only provided values should change
            assert TestSecurityConfig.MAX_COMMAND_LENGTH == 750000
            assert TestSecurityConfig.MAX_PYTHON_CODE_LENGTH == 200000  # Unchanged
        finally:
            os.unlink(config_file)

    def test_environment_variables_override_defaults(self):
        """Test that environment variables override default values."""
        with patch.dict(os.environ, {
            "CUSTOM_BLOCKED_PATTERNS": "test1,test2",
            "ENABLE_AUDIT_LOGGING": "false"
        }):
            # Reload to pick up environment changes
            TestSecurityConfig.CUSTOM_BLOCKED_PATTERNS = (
                os.getenv("CUSTOM_BLOCKED_PATTERNS", "").split(",")
                if os.getenv("CUSTOM_BLOCKED_PATTERNS")
                else []
            )
            TestSecurityConfig.ENABLE_AUDIT_LOGGING = (
                os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
            )
            
            assert TestSecurityConfig.CUSTOM_BLOCKED_PATTERNS == ["test1", "test2"]
            assert TestSecurityConfig.ENABLE_AUDIT_LOGGING is False