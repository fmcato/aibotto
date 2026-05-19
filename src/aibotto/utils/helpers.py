"""
Utility functions for the AIBOTTO project.
"""

import asyncio
import logging
import os

logger = logging.getLogger(__name__)


def setup_asyncio() -> None:
    """Setup asyncio configuration."""
    if os.name == "posix":
        asyncio.get_event_loop().set_debug(False)


def escape_markdown_v2(text: str) -> str:
    """Escape MarkdownV2 special characters in text.

    Args:
        text: The text to escape

    Returns:
        Text with all MarkdownV2 special characters properly escaped
    """
    if not text:
        return text

    escape_chars = r"_*[]()~`>#+-=|{}.!"
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")

    return text
