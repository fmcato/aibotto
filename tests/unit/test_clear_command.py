"""
Tests for the /clear command functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.db.operations import DatabaseOperations


class TestClearCommand:
    """Test the /clear command functionality."""

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
    async def test_clear_conversation_history_success(self, mock_update, mock_context):
        """Test successful clearing of conversation history."""
        # Create a mock database operations
        db_ops = MagicMock(spec=DatabaseOperations)
        db_ops.clear_conversation_history = AsyncMock()

        # Import the actual handler function
        from src.aibotto.bot.telegram_bot import TelegramBot
        
        # Create a bot instance but mock the database initialization
        with patch.object(DatabaseOperations, '__init__', return_value=None):
            with patch.object(DatabaseOperations, 'init_database', return_value=None):
                bot = TelegramBot()
                bot.db_ops = db_ops

                # Call the handler
                await bot._handle_clear(mock_update, mock_context)

        # Verify database operation was called with correct parameters
        db_ops.clear_conversation_history.assert_called_once_with(
            12345, 67890
        )

        # Verify success message was sent
        mock_update.message.reply_text.assert_called_once_with(
            "✅ Conversation history cleared! I've forgotten our previous conversation.\n\n"
            "You can start fresh with any question you'd like to ask."
        )

    @pytest.mark.asyncio
    async def test_clear_conversation_history_database_error(self, mock_update, mock_context):
        """Test handling of database errors during clear operation."""
        # Create a mock database operations
        db_ops = MagicMock(spec=DatabaseOperations)
        db_ops.clear_conversation_history = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Import the actual handler function
        from src.aibotto.bot.telegram_bot import TelegramBot
        
        # Create a bot instance but mock the database initialization
        with patch.object(DatabaseOperations, '__init__', return_value=None):
            with patch.object(DatabaseOperations, 'init_database', return_value=None):
                bot = TelegramBot()
                bot.db_ops = db_ops

                # Call the handler
                await bot._handle_clear(mock_update, mock_context)

        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once_with(
            "❌ Failed to clear conversation history: Database connection failed"
        )

    def test_telegram_bot_has_clear_handler(self):
        """Test that TelegramBot has the _handle_clear method."""
        from src.aibotto.bot.telegram_bot import TelegramBot
        
        # Check that the method exists
        assert hasattr(TelegramBot, '_handle_clear')
        
        # Check that it's an async method
        import inspect
        assert inspect.iscoroutinefunction(TelegramBot._handle_clear)