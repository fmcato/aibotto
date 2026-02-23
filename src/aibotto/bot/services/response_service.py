"""
Response service for handling message formatting and sending.
"""

import logging
from typing import Any

from telegramify_markdown import telegramify
from telegramify_markdown.content import ContentType, File, Photo, Text

from ..handlers.content_handlers import ContentHandlerFactory
from ..utils.bot_utils import MessageUtils, ResponseErrorHandler

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Handles text formatting with telegramify-markdown."""

    @staticmethod
    async def format_text_with_telegramify(text: str) -> str:
        """Format text using telegramify-markdown and escape for MarkdownV2."""

        try:
            # telegramify() returns structured content objects, not raw file objects
            # So we don't need to handle file objects here

            # Use the new telegramify() function to get structured content
            results = await telegramify(text, max_message_length=4096)

            # Process all results and combine them into a single string
            combined_text = ""
            for item in results:
                if isinstance(item, Text) and item.content_type == ContentType.TEXT:
                    # Text content - safely get text attribute
                    if item.text:
                        combined_text += item.text
                elif isinstance(item, File) and item.content_type == ContentType.FILE:
                    # File content - create a markdown representation
                    file_name = item.file_name
                    file_data = item.file_data

                    # Only decode UTF-8 text files, skip binary files
                    try:
                        file_content = file_data.decode('utf-8')
                        # Clean up common encoding artifacts
                        file_content = file_content.replace(
                            '\\n', '\n'
                        ).replace('\\r', '\r')
                        file_content = file_content.replace(
                            'nxe2x94x9c', '│'
                        ).replace('nxe2x94x80', '─')
                        file_content = file_content.replace(
                            'nxe2x94x94', '└'
                        ).replace('nxe2x94x90', '├')
                        combined_text += (
                        f"📄 **File: {file_name}**\n\n```\n"
                        f"{file_content}\n```\n\n"
                    )
                    except UnicodeDecodeError:
                        # Skip binary files that can't be decoded as UTF-8
                        continue
                elif isinstance(item, Photo) and item.content_type == ContentType.PHOTO:
                    # Photo content - just mention them
                    file_name = item.file_name
                    combined_text += f"🖼️ **Image: {file_name}**\n\n"

            return combined_text if combined_text else text
        except Exception as e:
            logger.warning(f"Failed to format text with telegramify: {e}")
            # Fall back to original text with escaping
            from ...utils.helpers import escape_markdown_v2
            return escape_markdown_v2(text)


class ResponseSender:
    """Handles sending formatted responses to Telegram."""

    def __init__(self, application: Any):
        self.application = application
        self.content_handler_factory = ContentHandlerFactory()

    async def send_response_with_telegramify(
        self,
        response: str,
        thinking_message: Any
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
                content_type = getattr(item, 'content_type', None)
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
            if (all_content_sent and
                    MessageUtils.should_delete_thinking_message(thinking_message)):
                await thinking_message.delete()

            return all_content_sent

        except Exception as e:
            logger.error(f"Failed to send response with telegramify: {e}")
            await ResponseErrorHandler.handle_content_error(
                e, thinking_message, "response"
            )
            return False

    async def send_single_response(
        self,
        response: str,
        thinking_message: Any
    ) -> bool:
        """Send single response by editing thinking message."""
        return await self.send_response_with_telegramify(response, thinking_message)
