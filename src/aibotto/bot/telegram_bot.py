"""
Telegram bot interface implementation - Refactored version.
"""

import logging
from typing import Any

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..ai.tool_calling import ToolCallingManager
from ..config.settings import Config
from ..db.operations import DatabaseOperations
from .handlers.content_handlers import ContentHandlerFactory
from .services.response_service import ResponseSender
from .services.setup_service import BotSetupService
from .utils.bot_utils import BotError, MessageUtils

logger = logging.getLogger(__name__)


class TelegramBot:
    """Main Telegram bot class - Refactored for better maintainability."""

    def __init__(self) -> None:
        self.db_ops = DatabaseOperations()
        self.tool_manager = ToolCallingManager()
        self.setup_service = BotSetupService()
        self.response_sender: ResponseSender | None = None
        self.content_handler_factory = ContentHandlerFactory()

    def _create_handlers(self) -> dict[str, Any]:
        """Create bot handlers."""
        return {
            'start': CommandHandler("start", self._handle_start),
            'help': CommandHandler("help", self._handle_help),
            'clear': CommandHandler("clear", self._handle_clear),
            'message': MessageHandler(
                filters.TEXT & ~filters.COMMAND, self._handle_message
            ),
        }

    async def _handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        update_data = MessageUtils.safe_update_data(update)
        if not update_data["has_message"]:
            return

        welcome_text = (
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

        if update.message:
            await update.message.reply_text(welcome_text)

    async def _handle_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help command."""
        update_data = MessageUtils.safe_update_data(update)
        if not update_data["has_message"]:
            return

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

        if update.message:
            await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _handle_clear(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /clear command."""
        update_data = MessageUtils.safe_update_data(update)
        if not update_data["has_message"]:
            return

        user_id = update_data["user_id"]
        chat_id = update_data["chat_id"]

        try:
            # Clear conversation history
            await self.db_ops.clear_conversation_history(user_id, chat_id)

            # Send confirmation message
            if update.message:
                await update.message.reply_text(
                    "✅ Conversation history cleared! I've forgotten our "
                    "previous conversation.\n\n"
                "You can start fresh with any question you'd like to ask."
            )

        except Exception as e:
            error_msg = BotError(f"Failed to clear conversation history: {str(e)}")
            if update.message:
                await update.message.reply_text(error_msg.get_fallback_message())
            logger.error(f"Error clearing conversation history: {e}")

    async def _handle_thinking_indicator(
        self, update: Update
    ) -> Any | None:
        """Send and return thinking indicator message."""
        if not MessageUtils.safe_update_data(update)["has_message"]:
            return None
        if update.message:
            return await update.message.reply_text(Config.THINKING_MESSAGE)
        return None

    async def _handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle user messages."""
        update_data = MessageUtils.safe_update_data(update)
        user_id = update_data["user_id"]
        chat_id = update_data["chat_id"]
        message = update_data["message"]

        if not message:
            return

        # Send thinking indicator
        thinking_message = await self._handle_thinking_indicator(update)
        if not thinking_message:
            return

        try:
            # Process the request
            response = await self.tool_manager.process_user_request(
                user_id, chat_id, message, self.db_ops
            )

            # Send response using the response sender
            if self.response_sender:
                await self.response_sender.send_single_response(
                    response, thinking_message
                )

        except Exception as e:
            error_msg = BotError(f"Error: {str(e)}")
            if thinking_message:
                await thinking_message.edit_text(error_msg.get_fallback_message())
            logger.error(f"Error handling message: {e}")

    async def _setup_response_sender(self) -> None:
        """Setup response sender with the application."""
        if self.setup_service.application:
            self.response_sender = ResponseSender(self.setup_service.application)

    def _setup_handlers(self) -> None:
        """Setup bot handlers."""
        handlers = self._create_handlers()
        self.setup_service.setup_handlers(handlers)

    async def _initialize_bot(self) -> None:
        """Initialize the bot application."""
        await self.setup_service.initialize_application(Config.TELEGRAM_TOKEN)
        self._setup_handlers()
        await self._setup_response_sender()

    def run(self) -> None:
        """Run the bot."""
        try:
            import asyncio

            # Create a new event loop for this bot instance
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Initialize the bot within the event loop
                loop.run_until_complete(self._initialize_bot())

                # Start polling (this will block and manage its own event loop)
                if self.setup_service.application:
                    self.setup_service.application.run_polling(drop_pending_updates=True)
                else:
                    logger.error("❌ Failed to initialize bot application")
                    raise RuntimeError("Failed to initialize bot application")

            finally:
                # Clean up the event loop
                loop.close()

        except Exception as e:
            logger.error(f"❌ Failed to run bot: {e}")
            raise
