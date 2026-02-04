"""
Unit tests for Config module.
"""

from unittest.mock import patch

from src.aibotto.config.settings import Config


class TestConfig:
    """Test cases for Config class."""

    def test_validate_config_success(self):
        """Test successful configuration validation."""
        with patch.object(Config, 'TELEGRAM_TOKEN', 'valid_token'), \
             patch.object(Config, 'OPENAI_API_KEY', 'valid_key'):

            result = Config.validate_config()
            assert result is True

    def test_validate_config_missing_token(self):
        """Test configuration validation with missing token."""
        with patch.object(Config, 'TELEGRAM_TOKEN', 'YOUR_TELEGRAM_TOKEN_HERE'):

            result = Config.validate_config()
            assert result is False

    def test_validate_config_missing_key(self):
        """Test configuration validation with missing API key."""
        with patch.object(Config, 'TELEGRAM_TOKEN', 'valid_token'), \
             patch.object(Config, 'OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY_HERE'):

            result = Config.validate_config()
            assert result is False
