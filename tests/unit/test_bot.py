"""
Unit tests for refactored bot module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aibotto.bot.telegram_bot import TelegramBot


class TestTelegramBot:
    """Test cases for refactored TelegramBot class."""

    @pytest.fixture
    def bot(self):
        """Create a TelegramBot instance for testing."""
        with patch('src.aibotto.bot.telegram_bot.Config.TELEGRAM_TOKEN', 'test_token'):
            with patch('src.aibotto.bot.telegram_bot.DatabaseOperations') as mock_db:
                with patch('src.aibotto.bot.telegram_bot.AgenticOrchestrator') as mock_tool:
                    with patch('src.aibotto.bot.telegram_bot.BotSetupService') as mock_setup:
                        bot = TelegramBot()
                        bot.db_ops = mock_db.return_value
                        bot.tool_manager = mock_tool.return_value
                        bot.setup_service = mock_setup.return_value
                        return bot

    def test_bot_initialization(self, bot):
        """Test that bot initializes with correct components."""
        assert bot.db_ops is not None
        assert bot.tool_manager is not None
        assert bot.setup_service is not None
        assert bot.content_handler_factory is not None

    @pytest.mark.asyncio
    async def test_handle_start_message(self, bot):
        """Test /start command handling."""
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123
        mock_update.effective_chat = MagicMock()
        mock_update.effective_chat.id = 456
        mock_message.text = ""

        mock_message.reply_text = AsyncMock()

        await bot._handle_start(mock_update, None)

        mock_message.reply_text.assert_called_once()
        call_args = mock_message.reply_text.call_args[0][0]
        assert "🤖 Hello! I'm an AI assistant" in call_args
        assert "Type /help for more information" in call_args

    @pytest.mark.asyncio
    async def test_handle_help_message(self, bot):
        """Test /help command handling."""
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123
        mock_update.effective_chat = MagicMock()
        mock_update.effective_chat.id = 456
        mock_message.text = ""

        mock_message.reply_text = AsyncMock()

        await bot._handle_help(mock_update, None)

        mock_message.reply_text.assert_called_once()
        call_args = mock_message.reply_text.call_args[0][0]
        assert "🤖 **AI Bot Help**" in call_args
        assert "Date & Time:" in call_args
        assert "File Operations:" in call_args

    @pytest.mark.asyncio
    async def test_handle_clear_message(self, bot):
        """Test /clear command handling."""
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123
        mock_update.effective_chat = MagicMock()
        mock_update.effective_chat.id = 456
        mock_message.text = ""

        mock_message.reply_text = AsyncMock()
        bot.db_ops.clear_conversation_history = AsyncMock()

        await bot._handle_clear(mock_update, None)

        bot.db_ops.clear_conversation_history.assert_called_once_with(123, 456)
        mock_message.reply_text.assert_called_once()
        call_args = mock_message.reply_text.call_args[0][0]
        assert "✅ Conversation history cleared" in call_args

    @pytest.mark.asyncio
    async def test_handle_clear_error(self, bot):
        """Test /clear command error handling."""
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123
        mock_update.effective_chat = MagicMock()
        mock_update.effective_chat.id = 456
        mock_message.text = ""

        mock_message.reply_text = AsyncMock()
        bot.db_ops.clear_conversation_history = AsyncMock(side_effect=Exception("DB error"))

        await bot._handle_clear(mock_update, None)

        mock_message.reply_text.assert_called_once()
        call_args = mock_message.reply_text.call_args[0][0]
        assert "⚠️ Failed to clear conversation history" in call_args

    @pytest.mark.asyncio
    async def test_handle_thinking_indicator(self, bot):
        """Test thinking indicator message."""
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message
        mock_message.reply_text = AsyncMock()

        result = await bot._handle_thinking_indicator(mock_update)

        mock_message.reply_text.assert_called_once_with("🤔 Thinking...")
        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_message_success(self, bot):
        """Test successful message handling."""
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123
        mock_update.effective_chat = MagicMock()
        mock_update.effective_chat.id = 456
        mock_message.text = "test message"

        mock_message.reply_text = AsyncMock()
        bot.tool_manager.process_user_request = AsyncMock(return_value="test response")
        bot.response_sender = MagicMock()
        bot.response_sender.send_single_response = AsyncMock()

        await bot._handle_message(mock_update, None)

        bot.tool_manager.process_user_request.assert_called_once_with(123, 456, "test message", bot.db_ops)
        bot.response_sender.send_single_response.assert_called_once_with("test response", mock_message.reply_text.return_value)

    @pytest.mark.asyncio
    async def test_handle_message_error(self, bot):
        """Test message handling error."""
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_update.message = mock_message
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123
        mock_update.effective_chat = MagicMock()
        mock_update.effective_chat.id = 456
        mock_message.text = "test message"

        mock_message.reply_text = AsyncMock()
        bot.tool_manager.process_user_request = AsyncMock(side_effect=Exception("Tool error"))
        bot.response_sender = MagicMock()

        await bot._handle_message(mock_update, None)

        # The bot sends thinking indicator first, then edits it with error
        assert mock_message.reply_text.call_count == 1
        # The thinking message should be edited with error
        thinking_message = mock_message.reply_text.return_value
        assert thinking_message.edit_text.called
        error_call = thinking_message.edit_text.call_args[0][0]
        assert "⚠️ Error: Tool error" in error_call

    def test_create_handlers(self, bot):
        """Test that handlers are created correctly."""
        handlers = bot._create_handlers()

        assert 'start' in handlers
        assert 'help' in handlers
        assert 'clear' in handlers
        assert 'message' in handlers

        # Check handler types
        from telegram.ext import CommandHandler, MessageHandler
        assert isinstance(handlers['start'], CommandHandler)
        assert isinstance(handlers['help'], CommandHandler)
        assert isinstance(handlers['clear'], CommandHandler)
        assert isinstance(handlers['message'], MessageHandler)
