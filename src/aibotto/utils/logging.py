"""
Logging setup and utilities.
"""

import logging
import os
import sys


def setup_logging(level: str | None = None) -> None:
    """Setup logging configuration."""
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    # Configure logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, level.upper()),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("aibotto.log"),
        ],
    )

    # Set specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
