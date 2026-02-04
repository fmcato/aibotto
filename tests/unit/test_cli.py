"""
Unit tests for CLI module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aibotto.cli.executor import CLIExecutor
from src.aibotto.cli.security import SecurityManager
from src.aibotto.config.settings import Config


class TestCLIExecutor:
    """Test cases for CLIExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a CLIExecutor instance for testing."""
        with patch('src.aibotto.cli.executor.SecurityManager') as mock_security:
            executor = CLIExecutor()
            executor.security_manager = MagicMock()
            return executor

    @pytest.mark.asyncio
    async def test_execute_command_success(self, executor):
        """Test successful command execution."""
        executor.security_manager.validate_command = AsyncMock(return_value={"allowed": True})

        with patch('asyncio.create_subprocess_shell') as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            result = await executor.execute_command("echo hello")

            assert result == "Success"
            executor.security_manager.validate_command.assert_called_once_with("echo hello")

    @pytest.mark.asyncio
    async def test_execute_command_blocked(self, executor):
        """Test command execution when blocked."""
        executor.security_manager.validate_command = AsyncMock(
            return_value={"allowed": False, "message": "Command blocked"}
        )

        result = await executor.execute_command("rm -rf /")

        assert result == "Command blocked"
        executor.security_manager.validate_command.assert_called_once_with("rm -rf /")


class TestSecurityManager:
    """Test cases for SecurityManager class."""

    @pytest.fixture
    def security_manager(self):
        """Create a SecurityManager instance for testing."""
        return SecurityManager()

    @pytest.mark.asyncio
    async def test_validate_command_allowed(self, security_manager):
        """Test command validation for allowed commands."""
        result = await security_manager.validate_command("echo hello")

        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_validate_command_blocked(self, security_manager):
        """Test command validation for blocked commands."""
        result = await security_manager.validate_command("rm -rf /")

        assert result["allowed"] is False
        assert "not allowed" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_command_too_long(self, security_manager):
        """Test command validation for commands that are too long."""
        long_command = "a" * (Config.MAX_COMMAND_LENGTH + 1)
        result = await security_manager.validate_command(long_command)

        assert result["allowed"] is False
        assert "too long" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_command_whitelist(self, security_manager):
        """Test command validation with whitelist enabled."""
        # Enable whitelist
        security_manager.allowed_commands = ["echo", "ls"]

        # Test allowed command
        result = await security_manager.validate_command("echo hello")
        assert result["allowed"] is True

        # Test blocked command
        result = await security_manager.validate_command("cat secret.txt")
        assert result["allowed"] is False
