"""
Unit tests for bot module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aibotto.bot.handlers import BaseHandler, CommandHandler, MessageHandler
from src.aibotto.bot.telegram_bot import TelegramBot


class TestBaseHandler:
    """Test cases for BaseHandler abstract class."""

    def test_base_handler_abstract(self):
        """Test that BaseHandler is abstract."""
        with pytest.raises(TypeError):
            BaseHandler()


class TestCommandHandler:
    """Test cases for CommandHandler class."""

    @pytest.fixture
    def mock_callback(self):
        """Create a mock callback function."""
        return AsyncMock()

    @pytest.fixture
    def command_handler(self, mock_callback):
        """Create a CommandHandler instance."""
        return CommandHandler("test", mock_callback)

    @pytest.mark.asyncio
    async def test_handle_command(self, command_handler, mock_callback):
        """Test command handling."""

        # Mock update and context
        mock_update = MagicMock()
        mock_context = MagicMock()

        await command_handler.handle(mock_update, mock_context)

        mock_callback.assert_called_once_with(mock_update, mock_context)

    def test_command_handler_initialization(self):
        """Test CommandHandler initialization."""
        mock_callback = AsyncMock()
        handler = CommandHandler("start", mock_callback)

        assert handler.command == "start"
        assert handler.callback == mock_callback


class TestMessageHandler:
    """Test cases for MessageHandler class."""

    @pytest.fixture
    def mock_callback(self):
        """Create a mock callback function."""
        return AsyncMock()

    @pytest.fixture
    def message_handler(self, mock_callback):
        """Create a MessageHandler instance."""
        return MessageHandler(mock_callback)

    @pytest.mark.asyncio
    async def test_handle_message(self, message_handler, mock_callback):
        """Test message handling."""

        # Mock update and context
        mock_update = MagicMock()
        mock_context = MagicMock()

        await message_handler.handle(mock_update, mock_context)

        mock_callback.assert_called_once_with(mock_update, mock_context)

    def test_message_handler_initialization(self):
        """Test MessageHandler initialization."""
        mock_callback = AsyncMock()
        handler = MessageHandler(mock_callback)

        assert handler.callback == mock_callback


class TestTelegramBot:
    """Test cases for TelegramBot class."""

    @pytest.fixture
    def telegram_bot(self):
        """Create a TelegramBot instance for testing."""
        with patch('src.aibotto.bot.telegram_bot.Application') as mock_app:
            with patch('src.aibotto.bot.telegram_bot.DatabaseOperations') as mock_db:
                with patch('src.aibotto.bot.telegram_bot.ToolCallingManager') as mock_tool:
                    bot = TelegramBot()
                    bot.application = MagicMock()
                    bot.db_ops = MagicMock()
                    bot.tool_manager = MagicMock()
                    return bot

    @pytest.mark.asyncio
    async def test_handle_start(self, telegram_bot):
        """Test /start command handling."""

        # Mock update
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        mock_update.effective_user.id = 123
        mock_update.effective_chat.id = 456

        # Mock context
        mock_context = MagicMock()

        await telegram_bot._handle_start(mock_update, mock_context)

        mock_message.reply_text.assert_called_once()
        reply_text = mock_message.reply_text.call_args[0][0]
        assert "Hello!" in reply_text
        assert "AI assistant" in reply_text

    @pytest.mark.asyncio
    async def test_handle_help(self, telegram_bot):
        """Test /help command handling."""

        # Mock update
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        mock_update.effective_user.id = 123
        mock_update.effective_chat.id = 456

        # Mock context
        mock_context = MagicMock()

        await telegram_bot._handle_help(mock_update, mock_context)

        mock_message.reply_text.assert_called_once()
        reply_text = mock_message.reply_text.call_args[0][0]
        assert "Help" in reply_text
        assert "AI Bot Help" in reply_text

    @pytest.mark.asyncio
    async def test_handle_message_success(self, telegram_bot):
        """Test successful message handling."""

        # Mock update
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message
        mock_update.effective_user.id = 123
        mock_update.effective_chat.id = 456
        mock_update.message.text = "What time is it?"

        # Mock context
        mock_context = MagicMock()

        # Mock thinking message
        mock_thinking = MagicMock()
        mock_thinking.edit_text = AsyncMock()
        mock_message.reply_text = AsyncMock(return_value=mock_thinking)

        # Mock tool manager response
        telegram_bot.tool_manager.process_user_request = AsyncMock(
            return_value="The current time is 2:30 PM"
        )

        await telegram_bot._handle_message(mock_update, mock_context)

        # Verify thinking message was edited
        mock_thinking.edit_text.assert_called_once_with("The current time is 2:30 PM", parse_mode="MarkdownV2")
        telegram_bot.tool_manager.process_user_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_message_error(self, telegram_bot):
        """Test message handling with error."""

        # Mock update
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message
        mock_update.effective_user.id = 123
        mock_update.effective_chat.id = 456
        mock_update.message.text = "What time is it?"

        # Mock context
        mock_context = MagicMock()

        # Mock thinking message
        mock_thinking = MagicMock()
        mock_thinking.edit_text = AsyncMock()
        mock_message.reply_text = AsyncMock(return_value=mock_thinking)

        # Mock tool manager to raise error
        telegram_bot.tool_manager.process_user_request = AsyncMock(
            side_effect=Exception("Test error")
        )

        await telegram_bot._handle_message(mock_update, mock_context)

        # Verify error message was sent
        mock_thinking.edit_text.assert_called_once()
        error_text = mock_thinking.edit_text.call_args[0][0]
        assert "Error:" in error_text

    def test_setup_handlers(self, telegram_bot):
        """Test handler setup."""
        mock_application = MagicMock()
        telegram_bot.application = mock_application

        telegram_bot._setup_handlers()

        # Verify handlers were added (start, help, clear, message)
        assert mock_application.add_handler.call_count == 4
