"""
Telegram bot interface implementation.
"""

import logging
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ExtBot,
    JobQueue,
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

    def __init__(self) -> None:
        self.application: Application[
            ExtBot[None], ContextTypes.DEFAULT_TYPE, dict[Any, Any],
            dict[Any, Any], dict[Any, Any],
            JobQueue[ContextTypes.DEFAULT_TYPE]
        ] | None = None
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
        if update and update.message:
            if update and update.message:
                await update.message.reply_text(
                    "🤖 Hello! I'm an AI assistant that provides factual "
                    "information.\n\n"
                    "I can help you with:\n"
                    "• Current date and time\n"
                    "• Weather information\n"
                    "• File system details\n"
                    "• System information\n"
                    "• Network information\n\n"
                    "Just ask me any question and I'll get you the factual "
                    "answer!\n\n"
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
        if update and update.message:
            await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _handle_clear(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /clear command."""
        if update and update.effective_user:
            user_id = update.effective_user.id
        if update and update.effective_chat:
            chat_id = update.effective_chat.id

        try:
            # Clear conversation history
            await self.db_ops.clear_conversation_history(user_id, chat_id)

            # Send confirmation message
            if update and update.message:
                await update.message.reply_text(
                    "✅ Conversation history cleared! I've forgotten our "
                    "previous conversation.\n\n"
                    "You can start fresh with any question you'd like to ask."
                )

        except Exception as e:
            if update and update.message:
                await update.message.reply_text(
                    f"❌ Failed to clear conversation history: {str(e)}"
                )
            logger.error(f"Error clearing conversation history: {e}")

    async def _handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle user messages."""
        if update and update.effective_user:
            user_id = update.effective_user.id
        if update and update.effective_chat:
            chat_id = update.effective_chat.id
        if update and update.message:
            message = update.message.text or ""
        else:
            message = ""

        # Send thinking indicator
        if update and update.message:
            thinking_message = await update.message.reply_text(Config.THINKING_MESSAGE)

        try:
            # Process the request
            response = await self.tool_manager.process_user_request(
                user_id, chat_id, message, self.db_ops
            )

            # Split response if it's too long for rate limiting
            # Reserve space for continuation markers when we'll have multiple chunks
            chunks = MessageSplitter.split_message_for_rate_limiting(
                response, reserve_marker_space=len(response) > 4095
            )
            if len(chunks) > 1:
                # Add continuation markers for better readability
                chunks = MessageSplitter.add_continuation_markers(chunks)

                # Delete thinking message and send chunks with rate limiting
                await thinking_message.delete()
                # Format chunks with telegramify-markdown for proper MarkdownV2 escaping
                from telegramify_markdown import telegramify
                formatted_chunks = []
                for chunk in chunks:
                    try:
                        telegram_result = await telegramify(chunk)
                        # Extract text from the result, handling different object types
                        chunk_text = ""
                        if hasattr(telegram_result, '__iter__') and not isinstance(telegram_result, str):
                            for item in telegram_result:
                                if hasattr(item, 'text'):
                                    chunk_text += item.text
                                elif hasattr(item, 'content'):
                                    chunk_text += str(item.content)
                                else:
                                    chunk_text += str(item)
                        else:
                            chunk_text = str(telegram_result)
                        formatted_chunks.append(chunk_text)
                    except Exception as e:
                        logger.warning(f"Failed to format chunk with telegramify: {e}")
                        # Fall back to original chunk
                        formatted_chunks.append(chunk)
                await MessageSplitter.send_chunks_with_rate_limit(
                    formatted_chunks,
                    thinking_message.reply_text,
                    delay_between_chunks=1.0,
                    parse_mode="MarkdownV2"
                )
            else:
                # Edit thinking message with response (single chunk)
                # Format response with telegramify-markdown for proper MarkdownV2 escaping
                from telegramify_markdown import telegramify
                try:
                    telegram_result = await telegramify(response)
                    # Extract text from the result, handling different object types
                    formatted_response = ""
                    if hasattr(telegram_result, '__iter__') and not isinstance(telegram_result, str):
                        for item in telegram_result:
                            if hasattr(item, 'text'):
                                formatted_response += item.text
                            elif hasattr(item, 'content'):
                                formatted_response += str(item.content)
                            else:
                                formatted_response += str(item)
                    else:
                        formatted_response = str(telegram_result)
                except Exception as e:
                    logger.warning(f"Failed to format response with telegramify: {e}")
                    # Fall back to original response
                    formatted_response = response
                await thinking_message.edit_text(formatted_response, parse_mode="MarkdownV2")

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

            # Initialize and clear any existing webhook/conflicts
            # This prevents "terminated by other getUpdates request" errors
            import asyncio

            async def setup_bot() -> None:
                if self.application:
                    await self.application.initialize()
                    # Delete any existing webhook to allow polling
                    await self.application.bot.delete_webhook(drop_pending_updates=True)
                    logger.info("✅ Cleared any existing webhooks and pending updates")

            # Run setup synchronously
            asyncio.get_event_loop().run_until_complete(setup_bot())

            # Start polling
            logger.info("🤖 Bot started. Polling for updates...")
            self.application.run_polling(drop_pending_updates=True)

        except Exception as e:
            logger.error(f"❌ Failed to run bot: {e}")
            raise
