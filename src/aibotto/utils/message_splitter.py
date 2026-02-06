"""
Smart message splitting utilities for Telegram's rate limiting.
"""

import asyncio
import logging
import re
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

TELEGRAM_MAX_LENGTH_PER_SECOND = 4095


class MessageSplitter:
    """Smart message splitter for rate limiting."""

    @staticmethod
    def split_message_for_rate_limiting(message: str) -> list[str]:
        """
        Split a message into chunks that respect Telegram's 4095
        characters per second rate limit.

        Args:
            message: The message to split

        Returns:
            List of message chunks that can be sent within rate limits
        """
        if len(message) <= TELEGRAM_MAX_LENGTH_PER_SECOND:
            return [message]

        chunks = []
        current_chunk = ""

        # First, try to split by natural boundaries
        for paragraph in message.split('\n\n'):
            if (len(current_chunk) + len(paragraph) + 2
                <= TELEGRAM_MAX_LENGTH_PER_SECOND):
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += '\n\n'
                current_chunk += paragraph
            else:
                # Current chunk is full, save it
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""

                # If paragraph itself is too long, split it further
                if len(paragraph) > TELEGRAM_MAX_LENGTH_PER_SECOND:
                    # Try to split by sentences first
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)

                    for sentence in sentences:
                        if (len(current_chunk) + len(sentence) + 1
                            <= TELEGRAM_MAX_LENGTH_PER_SECOND):
                            if current_chunk:
                                current_chunk += ' '
                            current_chunk += sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                                current_chunk = ""

                            # If sentence is too long, split by words
                            if len(sentence) > TELEGRAM_MAX_LENGTH_PER_SECOND:
                                words = sentence.split(' ')

                                for word in words:
                                    if (len(current_chunk) + len(word) + 1
                                        <= TELEGRAM_MAX_LENGTH_PER_SECOND):
                                        if current_chunk:
                                            current_chunk += ' '
                                        current_chunk += word
                                    else:
                                        if current_chunk:
                                            chunks.append(current_chunk)
                                            current_chunk = ""
                                        current_chunk = word

                                if current_chunk:
                                    chunks.append(current_chunk)
                                    current_chunk = ""
                            else:
                                current_chunk = sentence

                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = ""
                else:
                    current_chunk = paragraph

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)

        # If we still have very long chunks (fallback), split by character limit
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= TELEGRAM_MAX_LENGTH_PER_SECOND:
                final_chunks.append(chunk)
            else:
                # Split by character limit as last resort
                for i in range(0, len(chunk), TELEGRAM_MAX_LENGTH_PER_SECOND):
                    final_chunks.append(chunk[i:i + TELEGRAM_MAX_LENGTH_PER_SECOND])

        logger.info(f"Split message into {len(final_chunks)} chunks for rate limiting")
        return final_chunks

    @staticmethod
    async def send_chunks_with_rate_limit(
        chunks: list[str],
        send_func: Callable[[str], Any],
        delay_between_chunks: float = 1.0
    ) -> None:
        """
        Send message chunks with proper rate limiting.

        Args:
            chunks: List of message chunks to send
            send_func: Async function to call for sending each chunk
            delay_between_chunks: Delay in seconds between chunks (default: 1.0)
        """
        if not chunks:
            return

        for i, chunk in enumerate(chunks):
            try:
                # Send the chunk
                await send_func(chunk)

                # If this is not the last chunk, wait before sending next
                if i < len(chunks) - 1:
                    logger.info(
                        f"Waiting {delay_between_chunks}s before sending next chunk..."
                    )
                    await asyncio.sleep(delay_between_chunks)

            except Exception as e:
                logger.error(f"Error sending chunk {i+1}/{len(chunks)}: {e}")
                raise

    @staticmethod
    def add_continuation_markers(chunks: list[str]) -> list[str]:
        """
        Add continuation markers to message chunks for better readability.

        Args:
            chunks: List of message chunks

        Returns:
            List of chunks with continuation markers
        """
        if len(chunks) <= 1:
            return chunks

        marked_chunks = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk - add header
                header = f"📄 **Message (Part 1 of {len(chunks)}):**\n\n"
                marked_chunks.append(header + chunk)
            elif i == len(chunks) - 1:
                # Last chunk - add footer
                footer = "\n\n---\n✅ **End of message**"
                marked_chunks.append(chunk + footer)
            else:
                # Middle chunks - add continuation marker
                continuation = (
                    f"\n\n---\n📄 **Continuation (Part {i + 1} of {len(chunks)}):**\n\n"
                )
                marked_chunks.append(chunk + continuation)

        return marked_chunks
