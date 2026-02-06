"""
Telegram bot interface implementation.
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ..ai.tool_calling import ToolCallingManager
from ..config.settings import Config
from ..db.operations import DatabaseOperations
from ..utils import MessageSplitter

logger = logging.getLogger(__name__)


class TelegramBot:
    """Main Telegram bot class."""

    def __init__(self):
        self.application: Application | None = None
        self.db_ops = DatabaseOperations()
        self.tool_manager = ToolCallingManager()

    def _setup_handlers(self) -> None:
        """Setup bot handlers."""
        if not self.application:
            return

        # Add command handlers using proper Telegram handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("clear", self._handle_clear))

        # Add message handler using proper Telegram handler
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )

    async def _handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        await update.message.reply_text(
            "🤖 Hello! I'm an AI assistant that provides factual information.\n\n"
            "I can help you with:\n"
            "• Current date and time\n"
            "• Weather information\n"
            "• File system details\n"
            "• System information\n"
            "• Network information\n\n"
            "Just ask me any question and I'll get you the factual answer!\n\n"
            "Type /help for more information.\n"
            "Type /clear to reset our conversation."
        )

    async def _handle_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help command."""
        help_text = """
🤖 **AI Bot Help**

I provide factual information using safe system tools. Here's what I can help with:

**Date & Time:**
- "What day is today?"
- "What time is it now?"

**File Operations:**
- "List files in current directory"
- "Show current working directory"
- "Check disk usage"

**System Info:**
- "Show system information"
- "Check memory usage"
- "Show CPU information"

**Weather:**
- "What's the weather in London?"
- "Weather forecast for New York"

**Network:**
- "Show my IP address"
- "Check network connectivity"

**Commands:**
- `/start` - Start the bot and see welcome message
- `/help` - Show this help message
- `/clear` - Clear conversation history and start fresh

💡 **Tip:** Just ask me any factual question and I'll get you the accurate information!

⚠️ **Security Note:** I only execute safe, pre-approved commands for your security.
        """
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _handle_clear(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /clear command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        try:
            # Clear conversation history
            await self.db_ops.clear_conversation_history(user_id, chat_id)

            # Send confirmation message
            await update.message.reply_text(
                "✅ Conversation history cleared! I've forgotten our "
                "previous conversation.\n\n"
                "You can start fresh with any question you'd like to ask."
            )

        except Exception as e:
            await update.message.reply_text(
                f"❌ Failed to clear conversation history: {str(e)}"
            )
            logger.error(f"Error clearing conversation history: {e}")

    async def _handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle user messages."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message = update.message.text

        # Send thinking indicator
        thinking_message = await update.message.reply_text(Config.THINKING_MESSAGE)

        try:
            # Process the request
            response = await self.tool_manager.process_user_request(
                user_id, chat_id, message, self.db_ops
            )

            # Split response if it's too long for rate limiting
            chunks = MessageSplitter.split_message_for_rate_limiting(response)
            if len(chunks) > 1:
                # Add continuation markers for better readability
                chunks = MessageSplitter.add_continuation_markers(chunks)

                # Delete thinking message and send chunks with rate limiting
                await thinking_message.delete()
                await MessageSplitter.send_chunks_with_rate_limit(
                    chunks,
                    thinking_message.reply_text,
                    delay_between_chunks=1.0
                )
            else:
                # Edit thinking message with response (single chunk)
                await thinking_message.edit_text(response)

        except Exception as e:
            await thinking_message.edit_text(f"❌ Error: {str(e)}")
            logger.error(f"Error handling message: {e}")

    def run(self) -> None:
        """Run the bot."""
        try:
            # Create application
            self.application = (
                Application.builder().token(Config.TELEGRAM_TOKEN).build()
            )

            # Setup handlers
            self.application.add_handler(CommandHandler("start", self._handle_start))
            self.application.add_handler(CommandHandler("help", self._handle_help))
            self.application.add_handler(CommandHandler("clear", self._handle_clear))
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
            )

            # Start polling
            logger.info("🤖 Bot started. Polling for updates...")
            self.application.run_polling()

        except Exception as e:
            logger.error(f"❌ Failed to run bot: {e}")
            raise
