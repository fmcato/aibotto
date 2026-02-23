"""
Bot utilities for error handling, availability checking, and common operations.
"""

import logging
from typing import Any

from telegram import Bot

logger = logging.getLogger(__name__)


class BotError:
    """Represents a bot-related error with fallback handling."""

    def __init__(self, message: str, original_exception: Exception | None = None):
        self.message = message
        self.original_exception = original_exception

    def get_fallback_message(self) -> str:
        """Get a safe fallback message for display."""
        return f"⚠️ {self.message}"


class BotAvailabilityChecker:
    """Handles bot availability checking and fallbacks."""

    @staticmethod
    def is_bot_available(application: Any) -> bool:
        """Check if bot application is available."""
        return (
            application is not None and
            hasattr(application, 'bot') and
            application.bot is not None
        )

    @staticmethod
    async def send_with_fallback(
        bot: Bot,
        chat_id: int,
        content: str,
        fallback_message: str,
        **kwargs: Any
    ) -> bool:
        """Send message with fallback handling."""
        try:
            await bot.send_message(chat_id=chat_id, text=content, **kwargs)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    @staticmethod
    async def edit_with_fallback(
        message: Any,
        content: str,
        fallback_message: str
    ) -> bool:
        """Edit message with fallback handling."""
        try:
            await message.edit_text(content)
            return True
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            return False


class ResponseErrorHandler:
    """Handles errors in response processing."""

    @staticmethod
    def handle_response_error(
        error: Exception,
        thinking_message: Any | None,
        context: str = "processing response"
    ) -> str:
        """Handle response errors gracefully."""
        error_msg = BotError(
            f"Error {context}: {str(error)}",
            error
        ).get_fallback_message()

        if thinking_message:
            # This would be called asynchronously in the actual handler
            pass

        return error_msg

    @staticmethod
    async def handle_content_error(
        error: Exception,
        thinking_message: Any,
        content_type: str
    ) -> None:
        """Handle content-specific errors."""
        logger.error(f"Failed to send {content_type}: {error}")

        # Update thinking message with sanitized error
        try:
            error_msg = BotError(
                f"Failed to send {content_type} content: {str(error)[:100]}"
            ).get_fallback_message()
            await thinking_message.edit_text(error_msg)
        except Exception as e:
            logger.error(f"Failed to update thinking message: {e}")


class MessageUtils:
    """Utility methods for message handling."""

    @staticmethod
    def safe_update_data(update: Any) -> dict[str, Any]:
        """Extract safe data from update object with null safety."""
        if not update:
            return {
                "user_id": 0,
                "chat_id": 0,
                "message": "",
                "has_message": False,
            }

        return {
            "user_id": getattr(update.effective_user, 'id', 0),
            "chat_id": getattr(update.effective_chat, 'id', 0),
            "message": getattr(update.message, 'text', '') if update.message else '',
            "has_message": bool(update and update.message),
        }

    @staticmethod
    def has_thinking_message(thinking_message: Any | None) -> bool:
        """Check if thinking message exists."""
        return thinking_message is not None and hasattr(thinking_message, 'chat_id')

    @staticmethod
    def should_delete_thinking_message(thinking_message: Any | None) -> bool:
        """Check if thinking message should be deleted."""
        if not thinking_message:
            return False

        # Always delete thinking message if we got this far without errors
        # The error handling above will have updated the message if there was an issue
        return True
