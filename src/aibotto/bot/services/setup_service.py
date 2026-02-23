"""
Bot setup and initialization service.
"""

import logging
from typing import Any

from telegram.ext import Application

logger = logging.getLogger(__name__)


class BotSetupService:
    """Handles bot setup and initialization."""

    def __init__(self) -> None:
        self.application: Any = None

    async def initialize_application(self, token: str) -> Any:
        """Initialize the Telegram application."""
        try:
            self.application = Application.builder().token(token).build()

            # Initialize and clear any existing webhook/conflicts
            await self.application.initialize()

            # Delete any existing webhook to allow polling
            await self.application.bot.delete_webhook(drop_pending_updates=True)

            logger.info("✅ Cleared any existing webhooks and pending updates")
            return self.application

        except Exception as e:
            logger.error(f"❌ Failed to initialize application: {e}")
            raise

    def setup_handlers(self, handlers: dict[str, Any]) -> None:
        """Setup bot handlers."""
        if not self.application:
            logger.error("Application not initialized")
            return

        # Add command handlers
        if 'start' in handlers:
            self.application.add_handler(handlers['start'])
        if 'help' in handlers:
            self.application.add_handler(handlers['help'])
        if 'clear' in handlers:
            self.application.add_handler(handlers['clear'])

        # Add message handler
        if 'message' in handlers:
            self.application.add_handler(handlers['message'])

    def start_polling(self) -> None:
        """Start bot polling."""
        if not self.application:
            logger.error("Application not initialized")
            return

        logger.info("🤖 Bot started. Polling for updates...")
        self.application.run_polling(drop_pending_updates=True)

    def get_application(self) -> Any:
        """Get the initialized application."""
        return self.application
