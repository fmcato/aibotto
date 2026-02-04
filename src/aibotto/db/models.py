"""
Database models for the application.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Conversation:
    """Model for conversation messages."""

    id: int | None = None
    user_id: int = 0
    chat_id: int = 0
    message_id: int = 0
    role: str = ""
    content: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
