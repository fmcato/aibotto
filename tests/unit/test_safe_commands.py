"""
Unit tests for safe command whitelist and validation.
Tests only safe, read-only commands to prevent any security risks.
"""

import pytest

from src.aibotto.tools.security import SecurityManager


class TestSafeCommands:
    """Test safe command validation with strict allowlist."""

    @pytest.fixture
    def security_manager(self):
        """Create security manager with test configuration."""
        manager = SecurityManager()
        # Override with test-specific safe commands
        manager.blocked_commands = ["rm -rf", "sudo", "dd", "mkfs", "fdisk", "shutdown", "reboot", "poweroff", "halt"]
        manager.allowed_commands = ["date", "ls", "pwd", "uname", "echo", "cat", "head", "tail", "wc", "grep"]
        return manager

    @pytest.mark.asyncio
    async def test_safe_date_command(self, security_manager):
        """Test that 'date' command is allowed."""
        result = await security_manager.validate_command("date")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_safe_ls_command(self, security_manager):
        """Test that 'ls' command is allowed."""
        result = await security_manager.validate_command("ls -la")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_safe_pwd_command(self, security_manager):
        """Test that 'pwd' command is allowed."""
        result = await security_manager.validate_command("pwd")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_safe_uname_command(self, security_manager):
        """Test that 'uname' command is allowed."""
        result = await security_manager.validate_command("uname -a")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_safe_echo_command(self, security_manager):
        """Test that 'echo' command is allowed."""
        result = await security_manager.validate_command('echo "hello world"')
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_blocked_rm_command(self, security_manager):
        """Test that 'rm -rf' command is blocked."""
        result = await security_manager.validate_command("rm -rf /")
        assert result["allowed"] is False
        assert "not allowed" in result["message"]

    @pytest.mark.asyncio
    async def test_blocked_sudo_command(self, security_manager):
        """Test that 'sudo' command is blocked."""
        result = await security_manager.validate_command("sudo rm -rf /")
        assert result["allowed"] is False
        assert "not allowed" in result["message"]

    @pytest.mark.asyncio
    async def test_blocked_dd_command(self, security_manager):
        """Test that 'dd' command is blocked."""
        result = await security_manager.validate_command("dd if=/dev/zero of=/dev/sda")
        assert result["allowed"] is False
        assert "not allowed" in result["message"]

    @pytest.mark.asyncio
    async def test_blocked_shutdown_command(self, security_manager):
        """Test that 'shutdown' command is blocked."""
        result = await security_manager.validate_command("shutdown -h now")
        assert result["allowed"] is False
        assert "not allowed" in result["message"]

    @pytest.mark.asyncio
    async def test_safe_cat_command(self, security_manager):
        """Test that 'cat' command is allowed."""
        result = await security_manager.validate_command("cat /etc/passwd")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_safe_head_command(self, security_manager):
        """Test that 'head' command is allowed."""
        result = await security_manager.validate_command("head -n 10 /etc/passwd")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_safe_tail_command(self, security_manager):
        """Test that 'tail' command is allowed."""
        result = await security_manager.validate_command("tail -n 10 /etc/passwd")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_safe_wc_command(self, security_manager):
        """Test that 'wc' command is allowed."""
        result = await security_manager.validate_command("wc -l /etc/passwd")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_safe_grep_command(self, security_manager):
        """Test that 'grep' command is allowed."""
        result = await security_manager.validate_command("grep root /etc/passwd")
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_blocked_format_command(self, security_manager):
        """Test that format-related commands are blocked."""
        result = await security_manager.validate_command("mkfs /dev/sda")
        assert result["allowed"] is False
        assert "not allowed" in result["message"]

    @pytest.mark.asyncio
    async def test_blocked_reboot_command(self, security_manager):
        """Test that reboot command is blocked."""
        result = await security_manager.validate_command("reboot")
        assert result["allowed"] is False
        assert "not allowed" in result["message"]

    @pytest.mark.asyncio
    async def test_blocked_poweroff_command(self, security_manager):
        """Test that poweroff command is blocked."""
        result = await security_manager.validate_command("poweroff")
        assert result["allowed"] is False
        assert "not allowed" in result["message"]

    @pytest.mark.asyncio
    async def test_blocked_halt_command(self, security_manager):
        """Test that halt command is blocked."""
        result = await security_manager.validate_command("halt")
        assert result["allowed"] is False
        assert "not allowed" in result["message"]

    @pytest.mark.asyncio
    async def test_blocked_fdisk_command(self, security_manager):
        """Test that fdisk command is blocked."""
        result = await security_manager.validate_command("fdisk /dev/sda")
        assert result["allowed"] is False
        assert "not allowed" in result["message"]
