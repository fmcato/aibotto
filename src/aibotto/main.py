"""
Main entry point for the AIBOTTO application.
"""

import logging
import threading

from aibotto.ai.agentic_orchestrator import AgenticOrchestrator
from aibotto.api.server import start_api_server
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
        # Create orchestration instance (shared with API)
        orchestrator = AgenticOrchestrator()

        # Create and run the bot
        bot = TelegramBot()

        # Start API server in background thread with dependency injection
        api_thread = threading.Thread(
            target=start_api_server,
            kwargs={
                "bot_service": bot.setup_service,
                "orch": orchestrator,
            },
            daemon=True,
            name="api-server",
        )
        api_thread.start()
        logger.info("✅ API server started in background thread")

        # Run the Telegram bot (blocking)
        bot.run()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        raise


if __name__ == "__main__":
    main()
