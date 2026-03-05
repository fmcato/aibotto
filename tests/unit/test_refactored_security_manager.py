"""
Tests for refactored security manager classes.
"""

import pytest

from src.aibotto.tools.security import SecurityManager
from src.aibotto.tools.cli_security_manager import CLISecurityManager
from src.aibotto.tools.python_security_manager import PythonSecurityManager


class TestRefactoredSecurityManager:
    """Test refactored security manager functionality."""

    @pytest.mark.asyncio
    async def test_security_manager_initialization(self):
        """Test SecurityManager initializes correctly."""
        manager = SecurityManager()
        assert manager.config is not None
        assert manager.blocked_items == manager.config.BLOCKED_COMMANDS
        assert manager.allowed_items == manager.config.ALLOWED_COMMANDS
        assert manager.max_length == manager.config.MAX_COMMAND_LENGTH

    @pytest.mark.asyncio
    async def test_cli_security_manager_initialization(self):
        """Test CLISecurityManager initializes correctly."""
        manager = CLISecurityManager()
        assert manager.config is not None
        assert manager.blocked_items == manager.config.BLOCKED_COMMANDS
        assert manager.allowed_items == manager.config.ALLOWED_COMMANDS
        assert manager.max_length == manager.config.MAX_COMMAND_LENGTH

    @pytest.mark.asyncio
    async def test_python_security_manager_initialization(self):
        """Test PythonSecurityManager initializes correctly."""
        manager = PythonSecurityManager()
        assert manager.config is not None
        assert manager.blocked_items == manager.config.BLOCKED_PATTERNS
        assert manager.allowed_items == manager.config.ALLOWED_IMPORTS
        assert manager.max_length == manager.config.MAX_PYTHON_CODE_LENGTH

    @pytest.mark.asyncio
    async def test_security_manager_validate_command_safe(self):
        """Test SecurityManager validates safe commands."""
        manager = SecurityManager()
        result = await manager.validate_command("date")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_cli_security_manager_validate_command_safe(self):
        """Test CLISecurityManager validates safe commands."""
        manager = CLISecurityManager()
        result = await manager.validate_command("ls -la")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_python_security_manager_validate_safe_code(self):
        """Test PythonSecurityManager validates safe code."""
        manager = PythonSecurityManager()
        result = await manager.validate_python_code("print('hello')")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_security_manager_validate_blocked_command(self):
        """Test SecurityManager blocks dangerous commands."""
        manager = SecurityManager()
        result = await manager.validate_command("rm -rf /")
        assert result["allowed"] is False
        assert "Blocked" in result["message"]

    @pytest.mark.asyncio
    async def test_cli_security_manager_validate_blocked_command(self):
        """Test CLISecurityManager blocks dangerous commands."""
        manager = CLISecurityManager()
        result = await manager.validate_command("rm -rf /")
        assert result["allowed"] is False
        assert "Blocked" in result["message"]

    @pytest.mark.asyncio
    async def test_python_security_manager_validate_blocked_code(self):
        """Test PythonSecurityManager blocks dangerous code."""
        manager = PythonSecurityManager()
        result = await manager.validate_python_code("import os; os.system('rm -rf /')")
        assert result["allowed"] is False
        assert "Blocked" in result["message"]

    @pytest.mark.asyncio
    async def test_base_class_method_override(self):
        """Test that subclass methods properly override base class."""
        cli_manager = CLISecurityManager()
        python_manager = PythonSecurityManager()

        # Verify abstract methods are implemented
        assert hasattr(cli_manager, '_get_blocked_items')
        assert hasattr(cli_manager, '_get_allowed_items')
        assert hasattr(cli_manager, '_get_max_length')
        assert hasattr(python_manager, '_get_blocked_items')
        assert hasattr(python_manager, '_get_allowed_items')
        assert hasattr(python_manager, '_get_max_length')

        # Verify they return correct values
        assert cli_manager._get_blocked_items() == cli_manager.config.BLOCKED_COMMANDS
        assert python_manager._get_blocked_items() == python_manager.config.BLOCKED_PATTERNS
        assert cli_manager._get_max_length() == cli_manager.config.MAX_COMMAND_LENGTH
        assert python_manager._get_max_length() == python_manager.config.MAX_PYTHON_CODE_LENGTH

    @pytest.mark.asyncio
    async def test_reload_security_rules(self):
        """Test reload_security_rules method."""
        manager = SecurityManager()
        initial_max_length = manager.max_length

        # Reload should reinitialize properties
        manager.reload_security_rules()
        assert manager.max_length == initial_max_length
        assert manager.blocked_items == manager.config.BLOCKED_COMMANDS

    @pytest.mark.asyncio
    async def test_get_security_status(self):
        """Test get_security_status method."""
        manager = CLISecurityManager()
        status = manager.get_security_status()

        assert "blocked_items_count" in status
        assert "allowed_items_count" in status
        assert "custom_patterns_count" in status
        assert "max_length" in status
        assert "audit_logging_enabled" in status
        assert "security_rules_summary" in status

    @pytest.mark.asyncio
    async def test_cli_specific_blocked_item_check(self):
        """Test CLI-specific blocked item checking with special format handling."""
        manager = CLISecurityManager()

        # Test format command blocking
        result = await manager.validate_command("format c:")
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_python_import_extraction(self):
        """Test Python import statement extraction."""
        manager = PythonSecurityManager()

        # Test various import statements
        code = """
import os
import sys
from math import sqrt
from collections import defaultdict
"""
        imports = manager._extract_import_statements(code)
        assert "os" in imports
        assert "math" in imports
        assert "collections" in imports

    @pytest.mark.asyncio
    async def test_max_length_validation(self):
        """Test max length validation with custom length."""
        manager = CLISecurityManager(max_length=10)

        # Test short command
        result = await manager.validate_command("ls")
        assert result["allowed"] is True

        # Test long command
        long_command = "ls " + "a" * 100
        result = await manager.validate_command(long_command)
        assert result["allowed"] is False
        assert "too long" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_custom_blocked_patterns(self):
        """Test custom blocked patterns validation."""
        manager = SecurityManager()
        manager.custom_blocked_patterns = ["dangerous_keyword"]

        result = await manager.validate_command("echo dangerous_keyword")
        assert result["allowed"] is False
        assert "dangerous_keyword" in result["message"]

    @pytest.mark.asyncio
    async def test_allowed_items_whitelist(self):
        """Test allowed items whitelist functionality."""
        manager = SecurityManager()
        manager.allowed_items = ["ls", "pwd"]

        # Test allowed command
        result = await manager.validate_command("ls -la")
        assert result["allowed"] is True

        # Test blocked command (not in whitelist)
        result = await manager.validate_command("cat file.txt")
        assert result["allowed"] is False
        assert "not in allowed list" in result["message"]