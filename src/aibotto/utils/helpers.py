"""
Utility functions for the AIBOTTO project.
"""

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def setup_asyncio() -> None:
    """Setup asyncio configuration."""
    # Configure asyncio for better performance
    if os.name == "posix":
        asyncio.get_event_loop().set_debug(False)


def safe_get(d: dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary."""
    try:
        return d.get(key, default)
    except (AttributeError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def escape_markdown_v2(text: str) -> str:
    """Escape MarkdownV2 special characters in text.

    Args:
        text: The text to escape

    Returns:
        Text with all MarkdownV2 special characters properly escaped
    """
    if not text:
        return text

    # MarkdownV2 special characters that need escaping
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')

    return text


def process_file_content(file_obj: Any) -> str:
    """Process file objects and return formatted text content.

    Args:
        file_obj: File object with file_data and file_name attributes

    Returns:
        Formatted string representation of the file content
    """
    if not hasattr(file_obj, 'file_data') or not hasattr(file_obj, 'file_name'):
        return str(file_obj)

    file_name = getattr(file_obj, 'file_name', 'unknown.txt')
    file_data = getattr(file_obj, 'file_data', b'')

    try:
        # Try to decode as UTF-8 first
        decoded_content = file_data.decode('utf-8')
        # Clean up any encoding artifacts
        decoded_content = decoded_content.replace('\\n', '\n').replace('\\r', '\r')
        # Fix UTF-8 box drawing chars
        decoded_content = decoded_content.replace('nxe2x94x9c', '│')
        decoded_content = decoded_content.replace('nxe2x94x80', '─')
        decoded_content = decoded_content.replace('nxe2x94x94', '└')

        # Format as code block with file info
        return f"📄 **File: {file_name}**\n\n```\n{decoded_content}\n```"
    except UnicodeDecodeError:
        # If UTF-8 fails, show as base64 or indicate binary content
        import base64
        encoded = base64.b64encode(file_data[:2000]).decode('ascii')
        # Show first 2000 bytes
        return (
            f"📄 **File: {file_name}**\n\n⚠️ Binary file content "
            f"(first 2000 bytes base64):\n```\n{encoded}\n```\n..."
        )
    except Exception as e:
        logger.warning(f"Error processing file content: {e}")
        return f"📄 **File: {file_name}**\n\n⚠️ Could not process file content: {str(e)}"
