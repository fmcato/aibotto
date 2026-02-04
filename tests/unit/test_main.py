"""
Unit tests for main application entry point.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.main import main


class TestMainApplication:
    """Test cases for main application entry point."""
    
    @pytest.mark.asyncio
    async def test_main_success(self):
        """Test successful main execution."""
        with patch('src.aibotto.main.setup_logging') as mock_logging:
            with patch('src.aibotto.main.Config') as mock_config:
                with patch('src.aibotto.main.TelegramBot') as mock_bot:
                    # Mock configuration validation
                    mock_config.validate_config = MagicMock(return_value=True)
                    
                    # Mock bot
                    mock_bot_instance = MagicMock()
                    mock_bot.return_value = mock_bot_instance
                    
                    # Test main function
                    main()
                    
                    # Verify setup
                    mock_logging.assert_called_once()
                    mock_config.validate_config.assert_called_once()
                    mock_bot.assert_called_once()
                    mock_bot_instance.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_config_validation_failure(self):
        """Test main execution with config validation failure."""
        with patch('src.aibotto.main.setup_logging') as mock_logging:
            with patch('src.aibotto.main.Config') as mock_config:
                with patch('src.aibotto.main.TelegramBot') as mock_bot:
                    # Mock configuration validation failure
                    mock_config.validate_config = MagicMock(return_value=False)
                    
                    # Test main function
                    main()
                    
                    # Verify bot was not started
                    mock_bot.assert_not_called()
                    mock_bot.return_value.run.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self):
        """Test main execution with keyboard interrupt."""
        with patch('src.aibotto.main.setup_logging') as mock_logging:
            with patch('src.aibotto.main.Config') as mock_config:
                with patch('src.aibotto.main.TelegramBot') as mock_bot:
                    # Mock configuration validation
                    mock_config.validate_config = MagicMock(return_value=True)
                    
                    # Mock bot to raise KeyboardInterrupt
                    mock_bot_instance = MagicMock()
                    mock_bot_instance.run.side_effect = KeyboardInterrupt()
                    mock_bot.return_value = mock_bot_instance
                    
                    # Test main function
                    main()
                    
                    # Verify bot was started
                    mock_bot.assert_called_once()
                    mock_bot_instance.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_general_exception(self):
        """Test main execution with general exception."""
        with patch('src.aibotto.main.setup_logging') as mock_logging:
            with patch('src.aibotto.main.Config') as mock_config:
                with patch('src.aibotto.main.TelegramBot') as mock_bot:
                    # Mock configuration validation
                    mock_config.validate_config = MagicMock(return_value=True)
                    
                    # Mock bot to raise general exception
                    mock_bot_instance = MagicMock()
                    mock_bot_instance.run.side_effect = Exception("Bot crashed")
                    mock_bot.return_value = mock_bot_instance
                    
                    # Test main function
                    with pytest.raises(Exception) as exc_info:
                        main()
                    
                    # Verify exception was raised
                    assert "Bot crashed" in str(exc_info.value)
                    mock_bot.assert_called_once()
                    mock_bot_instance.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_logging_setup(self):
        """Test that logging is properly set up."""
        with patch('src.aibotto.main.setup_logging') as mock_logging:
            with patch('src.aibotto.main.Config') as mock_config:
                with patch('src.aibotto.main.TelegramBot') as mock_bot:
                    # Mock configuration validation
                    mock_config.validate_config = MagicMock(return_value=True)
                    
                    # Mock bot
                    mock_bot_instance = MagicMock()
                    mock_bot.return_value = mock_bot_instance
                    
                    # Test main function
                    main()
                    
                    # Verify logging was set up
                    mock_logging.assert_called_once()