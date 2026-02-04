"""
Tests for the /clear command functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.bot.telegram_bot import TelegramBot
from src.aibotto.db.operations import DatabaseOperations


class TestClearCommand:
    """Test the /clear command functionality."""

    @pytest.fixture
    def telegram_bot(self):
        """Create a Telegram bot instance for testing."""
        bot = TelegramBot()
        bot.db_ops = MagicMock(spec=DatabaseOperations)
        return bot

    @pytest.fixture
    def mock_update(self):
        """Create a mock Update object."""
        update = MagicMock()
        update.effective_user.id = 12345
        update.effective_chat.id = 67890
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create a mock Context object."""
        context = MagicMock()
        return context

    @pytest.mark.asyncio
    async def test_handle_clear_success(self, telegram_bot, mock_update, mock_context):
        """Test successful clearing of conversation history."""
        # Mock the database operation
        telegram_bot.db_ops.clear_conversation_history = AsyncMock()

        # Call the handler
        await telegram_bot._handle_clear(mock_update, mock_context)

        # Verify database operation was called with correct parameters
        telegram_bot.db_ops.clear_conversation_history.assert_called_once_with(
            12345, 67890
        )

        # Verify success message was sent
        mock_update.message.reply_text.assert_called_once_with(
            "✅ Conversation history cleared! I've forgotten our previous conversation.\n\n"
            "You can start fresh with any question you'd like to ask."
        )

    @pytest.mark.asyncio
    async def test_handle_clear_database_error(self, telegram_bot, mock_update, mock_context):
        """Test handling of database errors during clear operation."""
        # Mock the database operation to raise an exception
        telegram_bot.db_ops.clear_conversation_history = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Call the handler
        await telegram_bot._handle_clear(mock_update, mock_context)

        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once_with(
            "❌ Failed to clear conversation history: Database connection failed"
        )

    def test_setup_handlers_includes_clear(self, telegram_bot):
        """Test that the clear command handler is properly set up."""
        mock_application = MagicMock()
        telegram_bot.application = mock_application

        telegram_bot._setup_handlers()

        # Verify that the clear command handler was added
        handler_calls = mock_application.add_handler.call_args_list
        command_handlers = [
            call for call in handler_calls 
            if call[0][0].__class__.__name__ == 'CommandHandler'
        ]
        
        # Should have 3 command handlers: start, help, clear
        assert len(command_handlers) == 3
        
        # Check that clear command is included
        command_names = [list(call[0][0].commands)[0] for call in command_handlers]
        assert 'clear' in command_names