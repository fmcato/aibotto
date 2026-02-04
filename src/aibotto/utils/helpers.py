"""
Helper functions for the application.
"""

import asyncio
import os
from typing import Any


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
