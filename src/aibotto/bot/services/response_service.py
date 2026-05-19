"""
Response service for handling message formatting and sending.
"""

import logging
from typing import Any

from telegramify_markdown import telegramify

from ..handlers.content_handlers import ContentHandlerFactory
from ..utils.bot_utils import MessageUtils, ResponseErrorHandler

logger = logging.getLogger(__name__)


class ResponseSender:
    """Handles sending formatted responses to Telegram."""

    def __init__(self, application: Any):
        self.application = application
        self.content_handler_factory = ContentHandlerFactory()

    async def send_response_with_telegramify(
        self, response: str, thinking_message: Any
    ) -> bool:
        """Send response using telegramify-markdown with proper error handling."""
        if not MessageUtils.has_thinking_message(thinking_message):
            logger.error("No thinking message available for response")
            return False

        try:
            # Process the response with telegramify - this handles
            # all chunking and content splitting
            results = await telegramify(response, max_message_length=4096)
            chat_id = thinking_message.chat_id

            # Track if all content was sent successfully
            all_content_sent = True

            for item in results:
                # ContentType is an enum, not a string
                content_type = getattr(item, "content_type", None)
                if content_type:
                    # Convert enum to string for handler lookup
                    content_type_str = content_type.name
                    handler = self.content_handler_factory.get_handler(content_type_str)

                    if handler:
                        success = await handler.handle_content(
                            item, chat_id, self.application, thinking_message
                        )
                        if not success:
                            all_content_sent = False
                            logger.warning(f"Failed to send {content_type_str} content")
                    else:
                        all_content_sent = False
                        logger.warning(
                            f"No handler for content type: {content_type_str}"
                        )
                else:
                    all_content_sent = False
                    logger.warning("Item has no content_type attribute")

            # Delete thinking message only if all content was sent successfully
            if all_content_sent and MessageUtils.should_delete_thinking_message(
                thinking_message
            ):
                await thinking_message.delete()

            return all_content_sent

        except Exception as e:
            logger.error(f"Failed to send response with telegramify: {e}")
            await ResponseErrorHandler.handle_content_error(
                e, thinking_message, "response"
            )
            return False

    async def send_single_response(self, response: str, thinking_message: Any) -> bool:
        """Send single response by editing thinking message."""
        return await self.send_response_with_telegramify(response, thinking_message)
