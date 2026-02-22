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
# Reserve space for continuation markers (header/footer/continuation text)
MARKER_OVERHEAD = 100
# Safety margin for text expansion after MarkdownV2 escaping
ESCAPE_EXPANSION_SAFETY_MARGIN = 100


class MessageSplitter:
    """Smart message splitter for rate limiting."""

    @staticmethod
    def split_message_for_rate_limiting(
        message: str, reserve_marker_space: bool = False
    ) -> list[str]:
        """
        Split a message into chunks that respect Telegram's 4095
        characters per second rate limit.

        Args:
            message: The message to split
            reserve_marker_space: If True, reserve space for continuation markers

        Returns:
            List of message chunks that can be sent within rate limits
        """
        # Use smaller limit if we need to reserve space for markers
        max_length = (
            TELEGRAM_MAX_LENGTH_PER_SECOND - MARKER_OVERHEAD
            if reserve_marker_space
            else TELEGRAM_MAX_LENGTH_PER_SECOND
        )

        if len(message) <= max_length:
            return [message]

        chunks = []
        current_chunk = ""

        # First, try to split by natural boundaries
        for paragraph in message.split('\n\n'):
            if (len(current_chunk) + len(paragraph) + 2
                <= max_length):
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
                if len(paragraph) > max_length:
                    # Try to split by sentences first
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)

                    for sentence in sentences:
                        if (len(current_chunk) + len(sentence) + 1
                            <= max_length):
                            if current_chunk:
                                current_chunk += ' '
                            current_chunk += sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                                current_chunk = ""

                            # If sentence is too long, split by words
                            if len(sentence) > max_length:
                                words = sentence.split(' ')

                                for word in words:
                                    if (len(current_chunk) + len(word) + 1
                                        <= max_length):
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
            if len(chunk) <= max_length:
                final_chunks.append(chunk)
            else:
                # Split by character limit as last resort
                for i in range(0, len(chunk), max_length):
                    final_chunks.append(chunk[i:i + max_length])

        logger.info(f"Split message into {len(final_chunks)} chunks for rate limiting")
        return final_chunks

    @staticmethod
    def split_message_for_sending(
        message: str | object, reserve_marker_space: bool = False
    ) -> list[str]:
        """
        Split a message into chunks that will be safe after MarkdownV2 escaping.
        Accounts for potential character expansion during escaping and handles File objects.

        Args:
            message: The message to split (str or File object)
            reserve_marker_space: If True, reserve space for continuation markers

        Returns:
            List of message chunks that will be safe to send after escaping
        """
        # Handle File objects
        if hasattr(message, 'file_data') and hasattr(message, 'file_name'):
            # For files, we want to keep them as single chunks to preserve structure
            file_name = getattr(message, 'file_name', 'unknown.txt')
            file_data = getattr(message, 'file_data', b'')
            
            try:
                # Try to decode as UTF-8
                decoded_content = file_data.decode('utf-8')
                # Clean up encoding artifacts and format as code block
                content = f"📄 **File: {file_name}**\n\n```\n{decoded_content}\n```"
            except UnicodeDecodeError:
                # If UTF-8 fails, show as base64
                import base64
                encoded = base64.b64encode(file_data[:2000]).decode('ascii')  # Show first 2000 bytes
                content = f"📄 **File: {file_name}**\n\n⚠️ Binary file content (first 2000 bytes base64):\n```\n{encoded}\n```\n..."
            
            # For files, we don't split to preserve the structure
            return [content]
        
        # Handle regular text messages
        if not isinstance(message, str):
            message = str(message)
        
        # Be very conservative - split message into chunks that are safe even
        # if every character gets escaped (2x expansion)
        conservative_max = TELEGRAM_MAX_LENGTH_PER_SECOND // 2
        
        # Additional space for continuation markers if needed
        if reserve_marker_space:
            conservative_max -= ESCAPE_EXPANSION_SAFETY_MARGIN
        
        if len(message) <= conservative_max:
            return [message]

        chunks = []
        for i in range(0, len(message), conservative_max):
            chunk = message[i:i + conservative_max]
            chunks.append(chunk)
        
        logger.info(f"Split message into {len(chunks)} conservative chunks for escaping safety")
        return chunks

    @staticmethod
    async def send_chunks_with_rate_limit(
        chunks: list[str],
        send_func: Callable[[str, str | None], Any],
        delay_between_chunks: float = 1.0,
        parse_mode: str | None = None
    ) -> None:
        """
        Send message chunks with proper rate limiting.

        Args:
            chunks: List of message chunks to send
            send_func: Async function to call for sending each chunk
            delay_between_chunks: Delay in seconds between chunks (default: 1.0)
            parse_mode: Parse mode for message formatting (default: None)
        """
        if not chunks:
            return

        for i, chunk in enumerate(chunks):
            try:
                # Send the chunk with parse_mode
                await send_func(chunk, parse_mode)

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
        Ensures marked chunks don't exceed Telegram's character limit.

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
                marked_chunk = header + chunk
            elif i == len(chunks) - 1:
                # Last chunk - add footer
                footer = "\n\n---\n✅ **End of message**"
                marked_chunk = chunk + footer
            else:
                # Middle chunks - add continuation marker
                continuation = (
                    f"\n\n---\n📄 **Continuation (Part {i + 1} of {len(chunks)}):**\n\n"
                )
                marked_chunk = chunk + continuation

            # Safety check: truncate if still exceeds limit (shouldn't happen
            # if reserve_marker_space was used during splitting)
            if len(marked_chunk) > TELEGRAM_MAX_LENGTH_PER_SECOND:
                excess = len(marked_chunk) - TELEGRAM_MAX_LENGTH_PER_SECOND
                marked_chunk = marked_chunk[:-(excess + 3)] + "..."

            marked_chunks.append(marked_chunk)

        return marked_chunks
