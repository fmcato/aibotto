"""
Database operations for conversation history.
"""

import logging
import sqlite3

from ..config.settings import Config

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """Operations for database management."""

    def __init__(self) -> None:
        self.db_path = Config.DATABASE_PATH
        self.init_database()

    def init_database(self) -> None:
        """Initialize SQLite database for conversation history."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    message_id INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def save_message(
        self, user_id: int, chat_id: int, message_id: int, role: str, content: str
    ) -> None:
        """Save message to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversations (user_id, chat_id, message_id, role, content)
                VALUES (?, ?, ?, ?, ?)
            """,
                (user_id, chat_id, message_id, role, content),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            raise

    async def get_conversation_history(
        self, user_id: int, chat_id: int, limit: int = Config.MAX_HISTORY_LENGTH
    ) -> list[dict[str, str]]:
        """Get conversation history from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role, content FROM conversations
                WHERE user_id = ? AND chat_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (user_id, chat_id, limit),
            )
            messages = [
                {"role": row[0], "content": row[1]} for row in cursor.fetchall()
            ]
            conn.close()
            return messages[::-1]  # Reverse to get chronological order
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise

    async def clear_conversation_history(self, user_id: int, chat_id: int) -> None:
        """Clear conversation history for a specific user and chat."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM conversations
                WHERE user_id = ? AND chat_id = ?
            """,
                (user_id, chat_id),
            )
            conn.commit()
            conn.close()
            logger.info(
                f"Cleared conversation history for user {user_id}, chat {chat_id}"
            )
        except Exception as e:
            logger.error(f"Failed to clear conversation history: {e}")
            raise

    async def replace_conversation_with_summary(
        self, user_id: int, chat_id: int, summary: str
    ) -> None:
        """Replace conversation history with a summary message."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Clear existing conversation
            cursor.execute(
                """
                DELETE FROM conversations
                WHERE user_id = ? AND chat_id = ?
            """,
                (user_id, chat_id),
            )

            # Add summary as a system message
            cursor.execute(
                """
                INSERT INTO conversations (user_id, chat_id, message_id, role, content)
                VALUES (?, ?, ?, ?, ?)
            """,
                (user_id, chat_id, 0, "system", summary),
            )

            conn.commit()
            conn.close()
            logger.info(
                "Replaced conversation history with summary "
                f"for user {user_id}, chat {chat_id}"
            )
        except Exception as e:
            logger.error(f"Failed to replace conversation with summary: {e}")
            raise
