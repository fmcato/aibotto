"""
Utility functions for API module.
"""

import logging
from typing import Any

from telegramify_markdown import telegramify

from ..bot.handlers.content_handlers import ContentHandlerFactory

logger = logging.getLogger(__name__)


class TelegramMessageSender:
    """Helper class for sending messages via Telegram bot."""

    def __init__(self, application: Any):
        self.application = application
        self.content_handler_factory = ContentHandlerFactory()

    async def send_message(self, chat_id: int | str, text: str) -> bool:
        """Send formatted message to Telegram chat.

        Args:
            chat_id: Telegram chat ID (user, group, or channel)
            text: The text message to send

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            results = await telegramify(text, max_message_length=4096)

            all_sent = True
            for item in results:
                content_type = getattr(item, "content_type", None)
                if content_type:
                    handler = self.content_handler_factory.get_handler(content_type.name)
                    if handler:
                        success = await handler.handle_content(
                            item, chat_id,  # type: ignore[arg-type]
                            self.application, None
                        )
                        if not success:
                            all_sent = False
                            logger.warning(f"Failed to send {content_type.name} content")
                else:
                    all_sent = False
                    logger.warning("Item has no content_type attribute")

            return all_sent

        except Exception as e:
            logger.error(f"Failed to send message to chat {chat_id}: {e}")
            return False
