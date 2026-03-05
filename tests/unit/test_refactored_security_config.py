"""
Unit tests for refactored security configuration classes.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from src.aibotto.config.security_config import SecurityConfig
from src.aibotto.config.cli_security_config import CLISecurityConfig
from src.aibotto.config.python_security_config import PythonSecurityConfig


class TestSecurityConfig:
    """Test cases for SecurityConfig."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration after each test."""
        original_values = {
            "MAX_COMMAND_LENGTH": SecurityConfig.MAX_COMMAND_LENGTH,
            "MAX_PYTHON_CODE_LENGTH": SecurityConfig.MAX_PYTHON_CODE_LENGTH,
            "ALLOWED_COMMANDS": SecurityConfig.ALLOWED_COMMANDS.copy(),
            "BLOCKED_COMMANDS": SecurityConfig.BLOCKED_COMMANDS.copy(),
        }
        
        yield
        
        # Restore original values
        SecurityConfig.MAX_COMMAND_LENGTH = original_values["MAX_COMMAND_LENGTH"]
        SecurityConfig.MAX_PYTHON_CODE_LENGTH = original_values["MAX_PYTHON_CODE_LENGTH"]
        SecurityConfig.ALLOWED_COMMANDS = original_values["ALLOWED_COMMANDS"]
        SecurityConfig.BLOCKED_COMMANDS = original_values["BLOCKED_COMMANDS"]

    def test_inheritance(self):
        """Test that SecurityConfig properly inherits from BaseSecurityConfig."""
        from src.aibotto.config.base_security_config import BaseSecurityConfig
        assert issubclass(SecurityConfig, BaseSecurityConfig)

    def test_get_security_rules_summary(self):
        """Test get_security_rules_summary returns correct structure."""
        summary = SecurityConfig.get_security_rules_summary()
        
        assert "max_command_length" in summary
        assert "max_python_code_length" in summary
        assert "allowed_commands_count" in summary
        assert "blocked_commands_count" in summary
        assert "custom_blocked_patterns_count" in summary
        assert "audit_logging_enabled" in summary
        assert "has_whitelist" in summary

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
            SecurityConfig.reload_from_file(config_file)
            
            # Verify configuration was applied
            assert SecurityConfig.MAX_COMMAND_LENGTH == 500000
            assert SecurityConfig.MAX_PYTHON_CODE_LENGTH == 1000000
            assert SecurityConfig.ALLOWED_COMMANDS == ["echo", "ls", "pwd"]
            assert SecurityConfig.BLOCKED_COMMANDS == ["rm -rf", "sudo", "dd"]
        finally:
            os.unlink(config_file)


class TestCLISecurityConfig:
    """Test cases for CLISecurityConfig."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration after each test."""
        original_values = {
            "MAX_COMMAND_LENGTH": CLISecurityConfig.MAX_COMMAND_LENGTH,
            "ALLOWED_COMMANDS": CLISecurityConfig.ALLOWED_COMMANDS.copy(),
            "BLOCKED_COMMANDS": CLISecurityConfig.BLOCKED_COMMANDS.copy(),
        }
        
        yield
        
        # Restore original values
        CLISecurityConfig.MAX_COMMAND_LENGTH = original_values["MAX_COMMAND_LENGTH"]
        CLISecurityConfig.ALLOWED_COMMANDS = original_values["ALLOWED_COMMANDS"]
        CLISecurityConfig.BLOCKED_COMMANDS = original_values["BLOCKED_COMMANDS"]

    def test_inheritance(self):
        """Test that CLISecurityConfig properly inherits from BaseSecurityConfig."""
        from src.aibotto.config.base_security_config import BaseSecurityConfig
        assert issubclass(CLISecurityConfig, BaseSecurityConfig)

    def test_get_security_rules_summary(self):
        """Test get_security_rules_summary returns correct structure."""
        summary = CLISecurityConfig.get_security_rules_summary()
        
        assert "max_command_length" in summary
        assert "allowed_commands_count" in summary
        assert "blocked_commands_count" in summary
        assert "custom_blocked_patterns_count" in summary
        assert "audit_logging_enabled" in summary
        assert "has_whitelist" in summary

    def test_reload_from_file_success(self):
        """Test reload_from_file successfully loads configuration."""
        test_config = {
            "MAX_COMMAND_LENGTH": 750000,
            "ALLOWED_COMMANDS": ["echo", "ls", "pwd"],
            "BLOCKED_COMMANDS": ["rm -rf", "sudo", "dd"],
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_file = f.name
        
        try:
            CLISecurityConfig.reload_from_file(config_file)
            
            # Verify configuration was applied
            assert CLISecurityConfig.MAX_COMMAND_LENGTH == 750000
            assert CLISecurityConfig.ALLOWED_COMMANDS == ["echo", "ls", "pwd"]
            assert CLISecurityConfig.BLOCKED_COMMANDS == ["rm -rf", "sudo", "dd"]
        finally:
            os.unlink(config_file)


class TestPythonSecurityConfig:
    """Test cases for PythonSecurityConfig."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration after each test."""
        original_values = {
            "MAX_PYTHON_CODE_LENGTH": PythonSecurityConfig.MAX_PYTHON_CODE_LENGTH,
            "ALLOWED_IMPORTS": PythonSecurityConfig.ALLOWED_IMPORTS.copy(),
            "BLOCKED_PATTERNS": PythonSecurityConfig.BLOCKED_PATTERNS.copy(),
        }
        
        yield
        
        # Restore original values
        PythonSecurityConfig.MAX_PYTHON_CODE_LENGTH = original_values["MAX_PYTHON_CODE_LENGTH"]
        PythonSecurityConfig.ALLOWED_IMPORTS = original_values["ALLOWED_IMPORTS"]
        PythonSecurityConfig.BLOCKED_PATTERNS = original_values["BLOCKED_PATTERNS"]

    def test_inheritance(self):
        """Test that PythonSecurityConfig properly inherits from BaseSecurityConfig."""
        from src.aibotto.config.base_security_config import BaseSecurityConfig
        assert issubclass(PythonSecurityConfig, BaseSecurityConfig)

    def test_get_security_rules_summary(self):
        """Test get_security_rules_summary returns correct structure."""
        summary = PythonSecurityConfig.get_security_rules_summary()
        
        assert "max_python_code_length" in summary
        assert "allowed_imports_count" in summary
        assert "blocked_patterns_count" in summary
        assert "custom_blocked_patterns_count" in summary
        assert "audit_logging_enabled" in summary
        assert "has_import_restrictions" in summary

    def test_reload_from_file_success(self):
        """Test reload_from_file successfully loads configuration."""
        test_config = {
            "MAX_PYTHON_CODE_LENGTH": 120000,
            "ALLOWED_IMPORTS": ["os", "sys", "json"],
            "BLOCKED_PATTERNS": ["exec(", "eval("],
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_file = f.name
        
        try:
            PythonSecurityConfig.reload_from_file(config_file)
            
            # Verify configuration was applied
            assert PythonSecurityConfig.MAX_PYTHON_CODE_LENGTH == 120000
            assert PythonSecurityConfig.ALLOWED_IMPORTS == ["os", "sys", "json"]
            assert PythonSecurityConfig.BLOCKED_PATTERNS == ["exec(", "eval("]
        finally:
            os.unlink(config_file)

    def test_blocked_patterns_not_modified_by_reload(self):
        """Test that BLOCKED_PATTERNS is not modified by reload_from_file."""
        original_blocked_patterns = PythonSecurityConfig.BLOCKED_PATTERNS.copy()
        
        test_config = {
            "MAX_PYTHON_CODE_LENGTH": 120000,
            # BLOCKED_PATTERNS not provided in config
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_file = f.name
        
        try:
            PythonSecurityConfig.reload_from_file(config_file)
            
            # BLOCKED_PATTERNS should remain unchanged
            assert PythonSecurityConfig.BLOCKED_PATTERNS == original_blocked_patterns
        finally:
            os.unlink(config_file)