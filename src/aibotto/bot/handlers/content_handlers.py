"""
Content handlers for different message types in Telegram bot.
"""

import io
import logging
from abc import ABC, abstractmethod
from typing import Any

from telegram import InputFile
from telegramify_markdown.content import File, Photo, Text

logger = logging.getLogger(__name__)


class ContentHandler(ABC):
    """Abstract base class for content handlers."""

    @abstractmethod
    async def handle_content(
        self,
        item: Any,
        chat_id: int,
        application: Any,
        thinking_message: Any
    ) -> bool:
        """Handle content item and return True if successful.

        Args:
            item: Content item from telegramify
            chat_id: Chat ID to send to
            application: Telegram application
            thinking_message: Thinking message to update/delete

        Returns:
            True if handled successfully, False otherwise
        """
        pass


class TextContentHandler(ContentHandler):
    """Handler for text content."""

    async def handle_content(
        self,
        item: Any,
        chat_id: int,
        application: Any,
        thinking_message: Any
    ) -> bool:
        """Handle text content with entities support."""
        if not isinstance(item, Text):
            return False

        text_content = item.text
        entities = item.entities

        if not text_content:
            return False

        try:
            if entities:
                # Convert entities to dict format for Telegram
                entity_dicts = [entity.to_dict() for entity in entities]
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=text_content,
                    entities=entity_dicts,
                    disable_web_page_preview=True
                )
            else:
                # Send without entities - no parse_mode needed for plain text
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=text_content,
                    disable_web_page_preview=True
                )
            return True
        except Exception as e:
            logger.error(f"Failed to send text message: {e}")
            return False


class FileContentHandler(ContentHandler):
    """Handler for file content."""

    async def handle_content(
        self,
        item: Any,
        chat_id: int,
        application: Any,
        thinking_message: Any
    ) -> bool:
        """Handle file content with caption support."""
        if not isinstance(item, File):
            return False

        file_name = item.file_name
        file_data = item.file_data
        caption_text = item.caption_text
        caption_entities = item.caption_entities

        if not file_data:
            return False

        try:
            # Create a file-like object from the bytes
            file_stream = io.BytesIO(file_data)
            input_file = InputFile(file_stream, filename=file_name)

            # Convert entities to dict format for Telegram
            entity_dicts = (
                [entity.to_dict() for entity in caption_entities]
                if caption_entities else []
            )

            await application.bot.send_document(
                chat_id=chat_id,
                document=input_file,
                caption=caption_text,
                caption_entities=entity_dicts
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send document: {e}")
            return False


class PhotoContentHandler(ContentHandler):
    """Handler for photo content."""

    async def handle_content(
        self,
        item: Any,
        chat_id: int,
        application: Any,
        thinking_message: Any
    ) -> bool:
        """Handle photo content with caption support."""
        if not isinstance(item, Photo):
            return False

        file_name = item.file_name
        file_data = item.file_data
        caption_text = item.caption_text
        caption_entities = item.caption_entities

        if not file_data:
            return False

        try:
            # Create a file-like object from the bytes
            file_stream = io.BytesIO(file_data)
            input_file = InputFile(file_stream, filename=file_name)

            # Convert entities to dict format for Telegram
            entity_dicts = (
                [entity.to_dict() for entity in caption_entities]
                if caption_entities else []
            )

            await application.bot.send_photo(
                chat_id=chat_id,
                photo=input_file,
                caption=caption_text,
                caption_entities=entity_dicts
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            return False


class ContentHandlerFactory:
    """Factory for creating content handlers."""

    _handlers = {
        'TEXT': TextContentHandler,
        'FILE': FileContentHandler,
        'PHOTO': PhotoContentHandler,
    }

    @classmethod
    def get_handler(cls, content_type: str) -> ContentHandler | None:
        """Get appropriate handler for content type."""
        handler_class = cls._handlers.get(content_type.upper())
        return handler_class() if handler_class else None  # type: ignore

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of supported content types."""
        return list(cls._handlers.keys())
