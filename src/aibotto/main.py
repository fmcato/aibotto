"""
Main entry point for the AIBot application.
"""

import logging

from .bot.telegram_bot import TelegramBot
from .config.settings import Config
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the AIBot application."""
    # Setup logging
    setup_logging()

    # Validate configuration
    if not Config.validate_config():
        logger.error("❌ Configuration validation failed")
        return

    logger.info("🚀 Starting AIBot...")

    try:
        # Create and run the bot
        bot = TelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        raise


if __name__ == "__main__":
    main()
