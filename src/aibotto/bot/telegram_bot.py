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
        update_data = self._get_safe_update_data(update)
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
        if update_data["has_message"] and update and update.message:
            await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _handle_clear(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /clear command."""
        update_data = self._get_safe_update_data(update)
        user_id = update_data["user_id"]
        chat_id = update_data["chat_id"]

        try:
            # Clear conversation history
            await self.db_ops.clear_conversation_history(user_id, chat_id)

            # Send confirmation message
            if update_data["has_message"] and update and update.message:
                await update.message.reply_text(
                    "✅ Conversation history cleared! I've forgotten our "
                    "previous conversation.\n\n"
                    "You can start fresh with any question you'd like to ask."
                )

        except Exception as e:
            if update_data["has_message"] and update and update.message:
                await update.message.reply_text(
                    f"❌ Failed to clear conversation history: {str(e)}"
                )
            logger.error(f"Error clearing conversation history: {e}")

    def _get_safe_update_data(self, update: Update | None) -> dict[str, Any]:
        """Extract safe data from update object."""
        safe_update = update
        return {
            "user_id": safe_update.effective_user.id
            if safe_update and safe_update.effective_user
            else 0,
            "chat_id": safe_update.effective_chat.id
            if safe_update and safe_update.effective_chat
            else 0,
            "message": safe_update.message.text or ""
            if safe_update and safe_update.message
            else "",
            "has_message": bool(safe_update and safe_update.message),
        }

    async def _handle_thinking_indicator(
        self, update: Update
    ) -> Any | None:
        """Send and return thinking indicator message."""
        if update and update.message:
            return await update.message.reply_text(Config.THINKING_MESSAGE)
        return None

    async def _format_text_with_telegramify(self, text: str) -> str:
        """Format text using telegramify-markdown and escape for MarkdownV2."""
        from telegramify_markdown import telegramify

        from ..utils.helpers import escape_markdown_v2

        try:
            # First, convert markdown using telegramify
            telegram_result = await telegramify(text)

            # Extract text from the result, handling different object types
            if hasattr(telegram_result, "__iter__") and not isinstance(
                telegram_result, str
            ):
                formatted_text = ""
                for item in telegram_result:
                    if hasattr(item, 'text') and item.text is not None:  # type: ignore
                        formatted_text += str(item.text)  # type: ignore
                    elif hasattr(item, 'content') and item.content is not None:  # type: ignore
                        formatted_text += str(item.content)  # type: ignore
                    else:
                        formatted_text += str(item)
            else:
                formatted_text = str(telegram_result)

            # Then apply proper MarkdownV2 escaping
            return escape_markdown_v2(formatted_text)
        except Exception as e:
            logger.warning(f"Failed to format text with telegramify: {e}")
            # Fall back to original text with escaping
            return escape_markdown_v2(text)

    async def _send_response_chunks(
        self, chunks: list[str], thinking_message: Any
    ) -> None:
        """Send multiple response chunks with rate limiting."""
        if not thinking_message:
            logger.error("No thinking message available for chunked response")
            return

        # Format chunks with telegramify-markdown for proper MarkdownV2 escaping
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunk = await self._format_text_with_telegramify(chunk)
            formatted_chunks.append(formatted_chunk)

        await thinking_message.delete()
        await MessageSplitter.send_chunks_with_rate_limit(
            formatted_chunks,
            thinking_message.reply_text,
            delay_between_chunks=1.0,
            parse_mode="MarkdownV2"
        )

    async def _send_single_response(
        self, response: str, thinking_message: Any
    ) -> None:
        """Send single response by editing thinking message."""
        # Format response with telegramify-markdown for proper MarkdownV2 escaping
        escaped_response = await self._format_text_with_telegramify(response)
        await thinking_message.edit_text(
            escaped_response, parse_mode="MarkdownV2"
        )

    async def _handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle user messages."""
        # Extract safe data from update
        update_data = self._get_safe_update_data(update)
        user_id = update_data["user_id"]
        chat_id = update_data["chat_id"]
        message = update_data["message"]

        # Send thinking indicator
        thinking_message = await self._handle_thinking_indicator(update)

        try:
            # Process the request
            response = await self.tool_manager.process_user_request(
                user_id, chat_id, message, self.db_ops
            )

            # Split response if it's too long for rate limiting
            # Use improved splitting that accounts for MarkdownV2 escaping
            chunks = MessageSplitter.split_message_for_sending(
                response, reserve_marker_space=len(response) > 4095
            )
            if len(chunks) > 1:
                # Add continuation markers for better readability
                chunks = MessageSplitter.add_continuation_markers(chunks)
                await self._send_response_chunks(chunks, thinking_message)
            else:
                # Edit thinking message with response (single chunk)
                await self._send_single_response(response, thinking_message)

        except Exception as e:
            if thinking_message:
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
