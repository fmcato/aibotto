"""
Main entry point for the AIBOTTO application.
"""

import logging
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aibotto.bot.telegram_bot import TelegramBot
from aibotto.config.settings import Config
from aibotto.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the AIBOTTO application."""
    # Setup logging
    setup_logging()

    # Validate configuration
    if not Config.validate_config():
        logger.error("❌ Configuration validation failed")
        return

    logger.info("🚀 Starting AIBOTTO...")

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
