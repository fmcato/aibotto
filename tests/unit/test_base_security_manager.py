"""
Unit tests for base security manager classes.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.aibotto.config.base_security_config import BaseSecurityConfig
from src.aibotto.tools.base_security_manager import BaseSecurityManager


class TestSecurityConfig(BaseSecurityConfig):
    """Test security config for base manager tests."""
    
    MAX_COMMAND_LENGTH: int = 100000
    ALLOWED_COMMANDS: list[str] = ["echo", "ls", "pwd"]
    BLOCKED_COMMANDS: list[str] = ["rm -rf", "sudo", "dd"]

    @classmethod
    def _apply_config(cls, config: dict) -> None:
        """Apply configuration values."""
        pass

    @classmethod
    def _get_specific_summary(cls) -> dict:
        """Get specific security rules summary."""
        return {}


class TestSecurityManager(BaseSecurityManager):
    """Test implementation of BaseSecurityManager."""
    
    def _get_blocked_items(self) -> list[str]:
        """Get blocked items list."""
        return self.config.BLOCKED_COMMANDS
    
    def _get_allowed_items(self) -> list[str]:
        """Get allowed items list."""
        return self.config.ALLOWED_COMMANDS
    
    def _get_max_length(self) -> int:
        """Get maximum length."""
        return self.config.MAX_COMMAND_LENGTH


class TestBaseSecurityManager:
    """Test cases for BaseSecurityManager."""

    @pytest.fixture
    def security_manager(self):
        """Create a security manager instance for testing."""
        return TestSecurityManager(TestSecurityConfig)

    def test_security_manager_initialization(self, security_manager):
        """Test security manager initialization."""
        assert security_manager.config is not None
        assert security_manager.max_length == 100000
        assert security_manager.blocked_items == ["rm -rf", "sudo", "dd"]
        assert security_manager.allowed_items == ["echo", "ls", "pwd"]
        assert isinstance(security_manager.custom_blocked_patterns, list)
        assert isinstance(security_manager.enable_audit_logging, bool)

    def test_create_blocked_result_dict(self, security_manager):
        """Test _create_blocked_result_dict method."""
        result = security_manager._create_blocked_result_dict("Test blocked message")
        
        assert result == {"allowed": False, "message": "Test blocked message"}

    def test_get_security_status(self, security_manager):
        """Test get_security_status method."""
        status = security_manager.get_security_status()
        
        assert "blocked_items_count" in status
        assert "allowed_items_count" in status
        assert "custom_patterns_count" in status
        assert "max_length" in status
        assert "audit_logging_enabled" in status
        assert "security_rules_summary" in status
        
        assert status["blocked_items_count"] == 3
        assert status["allowed_items_count"] == 3
        assert status["max_length"] == 100000

    @pytest.mark.asyncio
    async def test_validate_input_success(self, security_manager):
        """Test successful input validation."""
        result = await security_manager.validate_input("echo hello")
        
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_validate_input_blocked_by_length(self, security_manager):
        """Test input validation blocked by length."""
        long_input = "x" * 100001  # Exceeds max length
        result = await security_manager.validate_input(long_input)
        
        assert result["allowed"] is False
        assert "too long" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_input_blocked_by_blocked_items(self, security_manager):
        """Test input validation blocked by blocked items."""
        result = await security_manager.validate_input("sudo rm -rf /")
        
        assert result["allowed"] is False
        assert "Blocked item detected" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_input_blocked_by_allowed_items_whitelist(self, security_manager):
        """Test input validation blocked when whitelist exists but no allowed items found."""
        # Test with a command that doesn't contain allowed items
        result = await security_manager.validate_input("unknown_command")
        
        assert result["allowed"] is False
        assert "No allowed items found" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_input_allowed_with_allowed_items(self, security_manager):
        """Test input validation allowed when allowed items exist."""
        result = await security_manager.validate_input("echo hello")
        
        assert result["allowed"] is True
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_validate_input_blocked_by_custom_patterns(self, security_manager):
        """Test input validation blocked by custom patterns."""
        # Set custom patterns
        security_manager.custom_blocked_patterns = ["dangerous"]
        
        result = await security_manager.validate_input("dangerous operation")
        
        assert result["allowed"] is False
        assert "Custom blocked pattern detected" in result["message"]

    def test_reload_security_rules(self, security_manager):
        """Test reloading security rules."""
        # Test that reload method exists and can be called
        security_manager.reload_security_rules()
        # No specific assertions needed since this is mainly testing the method exists

    def test_inheritance(self):
        """Test that TestSecurityManager properly inherits from BaseSecurityManager."""
        assert issubclass(TestSecurityManager, BaseSecurityManager)

    @pytest.mark.asyncio
    async def test_validation_order(self, security_manager):
        """Test that validation steps are executed in the correct order."""
        # Mock the validation steps to track call order
        call_order = []
        
        original_check_length = security_manager._check_length
        original_check_blocked = security_manager._check_blocked_items
        original_check_custom = security_manager._check_custom_patterns
        original_check_allowed = security_manager._check_allowed_items
        
        async def mock_check_length(input_data):
            call_order.append("length")
            return None
        
        async def mock_check_blocked(input_data):
            call_order.append("blocked")
            return None
        
        async def mock_check_custom(input_data):
            call_order.append("custom")
            return None
        
        async def mock_check_allowed(input_data):
            call_order.append("allowed")
            return None
        
        # Replace methods with mocks
        security_manager._check_length = mock_check_length
        security_manager._check_blocked_items = mock_check_blocked
        security_manager._check_custom_patterns = mock_check_custom
        security_manager._check_allowed_items = mock_check_allowed
        
        try:
            await security_manager.validate_input("test input")
            
            # Check that methods were called in the correct order
            assert call_order == ["length", "blocked", "custom", "allowed"]
        finally:
            # Restore original methods
            security_manager._check_length = original_check_length
            security_manager._check_blocked_items = original_check_blocked
            security_manager._check_custom_patterns = original_check_custom
            security_manager._check_allowed_items = original_check_allowed