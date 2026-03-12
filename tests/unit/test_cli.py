"""
Unit tests for CLI module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aibotto.config.settings import Config
from src.aibotto.tools.executors.cli_executor import CLIExecutor


class TestCLIExecutor:
    """Test cases for CLIExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a CLIExecutor instance for testing."""
        with patch('src.aibotto.tools.executors.cli_executor.CLISecurityManager') as mock_security:
            executor = CLIExecutor()
            executor.security_manager = MagicMock()
            return executor

    @pytest.mark.asyncio
    async def test_execute_command_success(self, executor):
        """Test successful command execution."""
        executor.security_manager.validate_command = AsyncMock(return_value={"allowed": True})

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"hello\n", b""))
            mock_subprocess.return_value = mock_process

            arguments = '{"command": "echo hello"}'
            result = await executor.execute(arguments, 0, None, 0)

            assert result == "hello\n"
            executor.security_manager.validate_command.assert_called_once_with("echo hello")

    @pytest.mark.asyncio
    async def test_execute_command_blocked(self, executor):
        """Test command execution when blocked."""
        executor.security_manager.validate_command = AsyncMock(
            return_value={"allowed": False, "message": "Command blocked"}
        )

        arguments = '{"command": "rm -rf /"}'
        result = await executor.execute(arguments, 0, None, 0)

        assert result == "Command blocked"
        executor.security_manager.validate_command.assert_called_once_with("rm -rf /")

    @pytest.mark.asyncio
    async def test_execute_command_error(self, executor):
        """Test command execution when command fails."""
        executor.security_manager.validate_command = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"Command not found\n"))
            mock_subprocess.return_value = mock_process

            arguments = '{"command": "invalid_command"}'
            result = await executor.execute(arguments, 0, None, 0)

            assert result == "Error: Command not found\n"
            executor.security_manager.validate_command.assert_called_once_with("invalid_command")

    @pytest.mark.asyncio
    async def test_execute_command_with_stdin(self, executor):
        """Test command execution with stdin input."""
        executor.security_manager.validate_command = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"hello world\n", b""))
            mock_subprocess.return_value = mock_process

            arguments = '{"command": "grep hello", "stdin": "hello world"}'
            result = await executor.execute(arguments, 0, None, 0)

            assert result == "hello world\n"
            executor.security_manager.validate_command.assert_called_once_with("grep hello")
            mock_subprocess.assert_called_once()
            mock_process.communicate.assert_called_once_with(input=b"hello world")

    @pytest.mark.asyncio
    async def test_execute_command_with_stdin_error(self, executor):
        """Test command execution with stdin when command fails."""
        executor.security_manager.validate_command = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"Error processing input\n"))
            mock_subprocess.return_value = mock_process

            arguments = '{"command": "grep hello", "stdin": "hello"}'
            result = await executor.execute(arguments, 0, None, 0)

            assert result == "Error: Error processing input\n"
            executor.security_manager.validate_command.assert_called_once_with("grep hello")
            mock_process.communicate.assert_called_once_with(input=b"hello")


class TestSecurityManager:
    """Test cases for CLI SecurityManager class."""

    @pytest.fixture
    def security_manager(self):
        """Create a CLISecurityManager instance for testing."""
        from src.aibotto.tools.cli_security_manager import CLISecurityManager
        return CLISecurityManager()

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
        assert "blocked" in result["message"].lower()

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
        # Enable whitelist by modifying the config
        security_manager.config.ALLOWED_COMMANDS = ["echo", "ls"]
        security_manager.allowed_items = security_manager.config.ALLOWED_COMMANDS

        # Test allowed command
        result = await security_manager.validate_command("echo hello")
        assert result["allowed"] is True

        # Test blocked command
        result = await security_manager.validate_command("cat secret.txt")
        assert result["allowed"] is False
