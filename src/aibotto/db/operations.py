"""
Enhanced database operations for agentic framework.
"""

import contextlib
import json
import logging
import re
from collections.abc import Iterator

from ..config.settings import Config

logger = logging.getLogger(__name__)


# Sensitive data patterns for masking
SENSITIVE_PATTERNS = [
    (r"--?[A-Za-z]+['\"]?\s*=\s*['\"]?[A-Za-z0-9_\-]{20,}['\"]?", "[REDACTED]"),
    (
        r"(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=]{15,}['\"]?",
        "[REDACTED]",
    ),
    (r"(TELEGRAM_TOKEN|OPENAI_API_KEY)\s*=\s*['\"]?[^'\"]{10,}['\"]?", "[REDACTED]"),
]


def mask_sensitive_data(content: str) -> str:
    """Mask sensitive data in content before storing.

    Args:
        content: Content to mask

    Returns:
        Content with sensitive data masked
    """
    if not content:
        return content

    masked = content
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
    return masked


@contextlib.contextmanager
def _get_db_connection() -> Iterator:
    """Context manager for database connections."""
    conn = None
    try:
        import sqlite3

        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        if conn:
            conn.close()


class DatabaseOperations:
    """Enhanced operations for agentic database management."""

    def __init__(self) -> None:
        self.db_path = Config.DATABASE_PATH
        self.init_database()

    def init_database(self) -> None:
        """Initialize comprehensive SQLite database for agentic framework."""
        try:
            import sqlite3

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ended_at DATETIME,
                    summary TEXT,
                    metadata JSON
                )
            """)

            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
                    role TEXT NOT NULL,
                    content TEXT,
                    message_type TEXT DEFAULT 'chat',
                    source_agent TEXT,
                    subagent_instance_id INTEGER,
                    iteration_number INTEGER,
                    tool_call_id TEXT,
                    telegram_message_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON,
                    FOREIGN KEY (subagent_instance_id) REFERENCES subagents(id)
                )
            """)

            # Create tool_calls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL REFERENCES messages(id),
                    tool_name TEXT NOT NULL,
                    tool_call_id TEXT NOT NULL,
                    arguments_json TEXT NOT NULL,
                    result_content TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    duration_ms DECIMAL(10, 2),
                    source_agent TEXT NOT NULL,
                    subagent_instance_id INTEGER,
                    iteration_number INTEGER,
                    FOREIGN KEY (subagent_instance_id) REFERENCES subagents(id)
                )
            """)

            # Create subagents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subagents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subagent_name TEXT NOT NULL,
                    instance_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    started_at DATETIME,
                    completed_at DATETIME,
                    status TEXT DEFAULT 'idle',
                    max_iterations INTEGER,
                    actual_iterations INTEGER DEFAULT 0,
                    parent_agent TEXT,
                    conversation_id INTEGER,
                    user_id INTEGER,
                    chat_id INTEGER,
                    task_description TEXT,
                    result_summary TEXT,
                    error_message TEXT,
                    metadata JSON,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                    UNIQUE(subagent_name, instance_id)
                )
            """)

            # Create delegations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS delegations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL REFERENCES messages(id),
                    parent_agent TEXT NOT NULL,
                    parent_subagent_id INTEGER,
                    child_agent_name TEXT NOT NULL,
                    child_subagent_id INTEGER NOT NULL REFERENCES subagents(id),
                    method_name TEXT,
                    task_description TEXT NOT NULL,
                    delegated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    status TEXT DEFAULT 'pending',
                    result_content TEXT,
                    error_message TEXT,
                    conversation_id INTEGER NOT NULL,
                    user_id INTEGER,
                    chat_id INTEGER,
                    iteration_number INTEGER,
                    FOREIGN KEY (parent_subagent_id) REFERENCES subagents(id),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)

            # Create indexes for performance
            indexes = [
                ("idx_conversations_user_chat", "conversations(user_id, chat_id)"),
                ("idx_conversations_started", "conversations(started_at)"),
                ("idx_messages_conversation", "messages(conversation_id)"),
                ("idx_messages_timestamps", "messages(conversation_id, timestamp)"),
                ("idx_messages_source_agent", "messages(source_agent)"),
                ("idx_messages_subagent", "messages(subagent_instance_id)"),
                ("idx_messages_tool_call_id", "messages(tool_call_id)"),
                ("idx_tool_calls_message", "tool_calls(message_id)"),
                ("idx_tool_calls_tool_name", "tool_calls(tool_name)"),
                ("idx_tool_calls_status", "tool_calls(status)"),
                ("idx_tool_calls_source_agent", "tool_calls(source_agent)"),
                ("idx_tool_calls_duration", "tool_calls(duration_ms)"),
                ("idx_subagents_name_id", "subagents(subagent_name, instance_id)"),
                ("idx_subagents_status", "subagents(status)"),
                ("idx_subagents_conversation", "subagents(conversation_id)"),
                ("idx_subagents_created", "subagents(created_at)"),
                ("idx_delegations_parent", "delegations(parent_agent)"),
                ("idx_delegations_child", "delegations(child_subagent_id)"),
                ("idx_delegations_message", "delegations(message_id)"),
                ("idx_delegations_status", "delegations(status)"),
                ("idx_delegations_conversation", "delegations(conversation_id)"),
            ]

            for index_name, index_sql in indexes:
                try:
                    cursor.execute(
                        f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_sql}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to create index {index_name}: {e}")

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully with agentic schema")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def get_or_create_conversation(self, user_id: int, chat_id: int) -> int:
        """Get existing conversation or create new one.

        Args:
            user_id: User ID
            chat_id: Chat ID

        Returns:
            Conversation ID
        """
        try:
            with _get_db_connection() as cursor:
                # Try to get existing active conversation
                cursor.execute(
                    """
                    SELECT id FROM conversations
                    WHERE user_id = ? AND chat_id = ? AND ended_at IS NULL
                    LIMIT 1
                """,
                    (user_id, chat_id),
                )
                row = cursor.fetchone()

                if row:
                    return row[0]

                # Create new conversation
                cursor.execute(
                    """
                    INSERT INTO conversations (user_id, chat_id)
                    VALUES (?, ?)
                """,
                    (user_id, chat_id),
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to get or create conversation: {e}")
            raise

    async def save_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        message_type: str = "chat",
        source_agent: str | None = None,
        subagent_instance_id: int | None = None,
        iteration_number: int | None = None,
        tool_call_id: str | None = None,
        telegram_message_id: int | None = None,
        metadata: dict | None = None,
    ) -> int:
        """Save a message to database.

        Args:
            conversation_id: Conversation ID
            role: Message role (user, assistant, system, tool)
            content: Message content
            message_type: Type of message (chat, tool_call, tool_result, delegation)
            source_agent: Agent that generated the message
            subagent_instance_id: Subagent instance ID
            iteration_number: Iteration number
            tool_call_id: Tool call ID (for tool role messages)
            telegram_message_id: Telegram message ID
            metadata: Additional metadata as dict

        Returns:
            Message ID
        """
        try:
            with _get_db_connection() as cursor:
                metadata_json = json.dumps(metadata) if metadata else None
                cursor.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, role, content, message_type,
                        source_agent, subagent_instance_id, iteration_number,
                        tool_call_id, telegram_message_id, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        conversation_id,
                        role,
                        content,
                        message_type,
                        source_agent,
                        subagent_instance_id,
                        iteration_number,
                        tool_call_id,
                        telegram_message_id,
                        metadata_json,
                    ),
                )
                msg_id = cursor.lastrowid
                logger.debug(
                    f"Saved message {msg_id}: {role} in conversation {conversation_id}"
                )
                return msg_id
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            raise

    async def save_message_compat(
        self,
        user_id: int,
        chat_id: int,
        role: str,
        content: str,
        message_type: str = "chat",
        source_agent: str | None = None,
        iteration_number: int | None = None,
        tool_call_id: str | None = None,
    ) -> int:
        """Compatibility wrapper for legacy save_message calls.

        Args:
            user_id: User ID
            chat_id: Chat ID
            role: Message role
            content: Message content
            message_type: Type of message
            source_agent: Agent that generated the message
            iteration_number: Iteration number
            tool_call_id: Tool call ID

        Returns:
            Message ID
        """
        conversation_id = await self.get_or_create_conversation(user_id, chat_id)
        return await self.save_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            source_agent=source_agent,
            iteration_number=iteration_number,
            tool_call_id=tool_call_id,
        )

    async def save_tool_call(
        self,
        message_id: int,
        tool_name: str,
        tool_call_id: str,
        arguments_json: str,
        source_agent: str,
        subagent_instance_id: int | None = None,
        iteration_number: int | None = None,
    ) -> int:
        """Save a tool call with pending status.

        Args:
            message_id: Message ID containing the tool call
            tool_name: Name of the tool
            tool_call_id: Tool call ID
            arguments_json: Tool arguments as JSON string (will be masked)
            source_agent: Agent making the call
            subagent_instance_id: Subagent instance ID
            iteration_number: Iteration number

        Returns:
            Tool call ID
        """
        try:
            masked_args = mask_sensitive_data(arguments_json)
            with _get_db_connection() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tool_calls (
                        message_id, tool_name, tool_call_id, arguments_json,
                        status, source_agent, subagent_instance_id, iteration_number
                    ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                    (
                        message_id,
                        tool_name,
                        tool_call_id,
                        masked_args,
                        source_agent,
                        subagent_instance_id,
                        iteration_number,
                    ),
                )
                tool_call_id_pkey = cursor.lastrowid
                logger.debug(
                    f"Saved tool call {tool_call_id_pkey}: {tool_name} for message {message_id}"
                )
                return tool_call_id_pkey
        except Exception as e:
            logger.error(f"Failed to save tool call: {e}")
            raise

    async def update_tool_call_result(
        self,
        tool_call_id: str,
        result_content: str,
        status: str = "completed",
        error_message: str | None = None,
    ) -> None:
        """Update tool call with result.

        Args:
            tool_call_id: Tool call ID
            result_content: Result content (will be masked)
            status: Status (completed, failed)
            error_message: Error message if failed
        """
        try:
            masked_result = mask_sensitive_data(result_content)
            with _get_db_connection() as cursor:
                # Get started_at to calculate duration
                cursor.execute(
                    "SELECT started_at FROM tool_calls WHERE tool_call_id = ?",
                    (tool_call_id,),
                )
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"Tool call {tool_call_id} not found")
                    return

                _ = row[0]  # Keep for future use
                cursor.execute(
                    """
                    UPDATE tool_calls
                    SET result_content = ?, status = ?, error_message = ?,
                        completed_at = CURRENT_TIMESTAMP,
                        duration_ms = CASE
                            WHEN started_at IS NOT NULL
                            THEN (julianday('now') - julianday(started_at)) * 86400000.0
                            ELSE NULL
                        END
                    WHERE tool_call_id = ?
                """,
                    (masked_result, status, error_message, tool_call_id),
                )
                logger.debug(f"Updated tool call {tool_call_id} with status {status}")
        except Exception as e:
            logger.error(f"Failed to update tool call result: {e}")
            raise

    async def save_subagent(
        self,
        subagent_name: str,
        instance_id: int,
        user_id: int = 0,
        chat_id: int = 0,
        max_iterations: int = 5,
        parent_agent: str | None = None,
        task_description: str | None = None,
        conversation_id: int | None = None,
    ) -> int:
        """Save a subagent instance.

        Args:
            subagent_name: Name of subagent
            instance_id: Instance ID
            user_id: User ID
            chat_id: Chat ID
            max_iterations: Max iterations
            parent_agent: Parent agent name
            task_description: Task description
            conversation_id: Conversation ID

        Returns:
            Subagent record ID
        """
        try:
            with _get_db_connection() as cursor:
                cursor.execute(
                    """
                    INSERT INTO subagents (
                        subagent_name, instance_id, user_id, chat_id,
                        max_iterations, parent_agent, task_description,
                        conversation_id, started_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'active')
                """,
                    (
                        subagent_name,
                        instance_id,
                        user_id,
                        chat_id,
                        max_iterations,
                        parent_agent,
                        task_description,
                        conversation_id,
                    ),
                )
                subagent_id = cursor.lastrowid
                logger.info(
                    f"Saved subagent {subagent_name} (instance {instance_id}) with ID {subagent_id}"
                )
                return subagent_id
        except Exception as e:
            logger.error(f"Failed to save subagent: {e}")
            raise

    async def update_subagent_completion(
        self,
        db_subagent_id: int,
        result_summary: str | None = None,
        error_message: str | None = None,
        actual_iterations: int | None = None,
    ) -> None:
        """Update subagent with completion details.

        Args:
            db_subagent_id: Subagent record ID
            result_summary: Result summary
            error_message: Error message if failed
            actual_iterations: Actual iterations used
        """
        try:
            with _get_db_connection() as cursor:
                cursor.execute(
                    """
                    UPDATE subagents
                    SET result_summary = ?, error_message = ?,
                        actual_iterations = COALESCE(?, actual_iterations),
                        completed_at = CURRENT_TIMESTAMP,
                        status = CASE WHEN ? IS NOT NULL THEN 'error' ELSE 'completed' END
                    WHERE id = ?
                """,
                    (
                        result_summary,
                        error_message,
                        actual_iterations,
                        error_message,
                        db_subagent_id,
                    ),
                )
                logger.debug(f"Updated subagent {db_subagent_id} completion details")
        except Exception as e:
            logger.error(f"Failed to update subagent completion: {e}")
            raise

    async def save_delegation(
        self,
        message_id: int,
        conversation_id: int,
        parent_agent: str,
        child_agent_name: str,
        child_subagent_id: int,
        task_description: str,
        method_name: str | None = None,
        parent_subagent_id: int | None = None,
        user_id: int = 0,
        chat_id: int = 0,
        iteration_number: int | None = None,
    ) -> int:
        """Save a delegation event.

        Args:
            message_id: Message ID
            conversation_id: Conversation ID
            parent_agent: Parent agent name
            child_agent_name: Child agent name
            child_subagent_id: Child subagent record ID
            task_description: Task description
            method_name: Method called
            parent_subagent_id: Parent subagent ID
            user_id: User ID
            chat_id: Chat ID
            iteration_number: Iteration number

        Returns:
            Delegation ID
        """
        try:
            with _get_db_connection() as cursor:
                cursor.execute(
                    """
                    INSERT INTO delegations (
                        message_id, conversation_id, parent_agent, child_agent_name,
                        child_subagent_id, task_description, method_name,
                        parent_subagent_id, user_id, chat_id, iteration_number
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        message_id,
                        conversation_id,
                        parent_agent,
                        child_agent_name,
                        child_subagent_id,
                        task_description,
                        method_name,
                        parent_subagent_id,
                        user_id,
                        chat_id,
                        iteration_number,
                    ),
                )
                delegation_id = cursor.lastrowid
                logger.debug(
                    f"Saved delegation {delegation_id}: {parent_agent} -> {child_agent_name}"
                )
                return delegation_id
        except Exception as e:
            logger.error(f"Failed to save delegation: {e}")
            raise

    async def update_delegation_result(
        self,
        delegation_id: int,
        result_content: str,
        status: str = "completed",
        error_message: str | None = None,
    ) -> None:
        """Update delegation with result.

        Args:
            delegation_id: Delegation ID
            result_content: Result content
            status: Status
            error_message: Error message if failed
        """
        try:
            with _get_db_connection() as cursor:
                cursor.execute(
                    """
                    UPDATE delegations
                    SET result_content = ?, status = ?, error_message = ?,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (result_content, status, error_message, delegation_id),
                )
                logger.debug(f"Updated delegation {delegation_id} with status {status}")
        except Exception as e:
            logger.error(f"Failed to update delegation result: {e}")
            raise

    async def get_conversation_history(
        self, user_id: int, chat_id: int, limit: int = Config.MAX_HISTORY_LENGTH
    ) -> list[dict[str, str | None]]:
        """Get conversation history from database.

        Args:
            user_id: User ID
            chat_id: Chat ID
            limit: Max messages to return

        Returns:
            List of message dictionaries
        """
        try:
            with _get_db_connection() as cursor:
                cursor.execute(
                    """
                    SELECT m.role, m.content, m.message_type, m.source_agent,
                           m.tool_call_id, m.iteration_number
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = ? AND c.chat_id = ? AND c.ended_at IS NULL
                    ORDER BY m.id ASC
                    LIMIT ?
                """,
                    (user_id, chat_id, limit),
                )
                messages = []
                for row in cursor.fetchall():
                    messages.append(
                        {
                            "role": row["role"],
                            "content": row["content"],
                            "message_type": row["message_type"],
                            "source_agent": row["source_agent"],
                            "tool_call_id": row["tool_call_id"],
                            "iteration_number": row["iteration_number"],
                        }
                    )
                return messages  # Already in chronological order
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise

    async def clear_conversation_history(self, user_id: int, chat_id: int) -> None:
        """Clear conversation history for a specific user and chat.

        Args:
            user_id: User ID
            chat_id: Chat ID
        """
        try:
            with _get_db_connection() as cursor:
                # Mark any active conversations as ended
                cursor.execute(
                    """
                    UPDATE conversations
                    SET ended_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND chat_id = ? AND ended_at IS NULL
                """,
                    (user_id, chat_id),
                )
                # Get the affected conversation ID
                cursor.execute(
                    """
                    SELECT id FROM conversations
                    WHERE user_id = ? AND chat_id = ? AND ended_at = CURRENT_TIMESTAMP
                    LIMIT 1
                """,
                    (user_id, chat_id),
                )
                result = cursor.fetchone()
                if result:
                    logger.info(
                        f"Cleared conversation {result[0]} for user {user_id}, chat {chat_id}"
                    )
                else:
                    logger.info(
                        f"No active conversation found for user {user_id}, chat {chat_id}"
                    )
        except Exception as e:
            logger.error(f"Failed to clear conversation history: {e}")
            raise

    async def replace_conversation_with_summary(
        self, user_id: int, chat_id: int, summary: str
    ) -> None:
        """Replace conversation history with a summary message.

        Args:
            user_id: User ID
            chat_id: Chat ID
            summary: Summary text
        """
        try:
            conversation_id = await self.get_or_create_conversation(user_id, chat_id)

            with _get_db_connection() as cursor:
                # Delete all existing messages for this conversation
                cursor.execute(
                    "DELETE FROM messages WHERE conversation_id = ?", (conversation_id,)
                )

                # Add summary as a system message
                cursor.execute(
                    """
                    INSERT INTO messages (conversation_id, role, content, message_type)
                    VALUES (?, 'system', ?, 'chat')
                """,
                    (conversation_id, summary),
                )

            logger.info(
                f"Replaced conversation with summary for user {user_id}, chat {chat_id}"
            )
        except Exception as e:
            logger.error(f"Failed to replace conversation with summary: {e}")
            raise

    async def get_tool_call_stats(
        self, user_id: int, chat_id: int | None = None
    ) -> list[dict]:
        """Get tool call statistics for debugging.

        Args:
            user_id: User ID
            chat_id: Chat ID (optional)

        Returns:
            List of tool call statistics
        """
        try:
            with _get_db_connection() as cursor:
                if chat_id:
                    cursor.execute(
                        """
                        SELECT tc.tool_name, COUNT(*) as count,
                               AVG(tc.duration_ms) as avg_duration,
                               tc.source_agent,
                               COUNT(CASE WHEN tc.status = 'failed' THEN 1 END) as failures
                        FROM tool_calls tc
                        JOIN messages m ON tc.message_id = m.id
                        JOIN conversations c ON m.conversation_id = c.id
                        WHERE c.user_id = ? AND c.chat_id = ?
                        GROUP BY tc.tool_name, tc.source_agent
                        ORDER BY count DESC
                    """,
                        (user_id, chat_id),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT tc.tool_name, COUNT(*) as count,
                               AVG(tc.duration_ms) as avg_duration,
                               tc.source_agent,
                               COUNT(CASE WHEN tc.status = 'failed' THEN 1 END) as failures
                        FROM tool_calls tc
                        JOIN messages m ON tc.message_id = m.id
                        JOIN conversations c ON m.conversation_id = c.id
                        WHERE c.user_id = ?
                        GROUP BY tc.tool_name, tc.source_agent
                        ORDER BY count DESC
                    """,
                        (user_id,),
                    )

                stats = []
                for row in cursor.fetchall():
                    stats.append(
                        {
                            "tool_name": row["tool_name"],
                            "count": row["count"],
                            "avg_duration": row["avg_duration"],
                            "source_agent": row["source_agent"],
                            "failures": row["failures"],
                        }
                    )
                return stats
        except Exception as e:
            logger.error(f"Failed to get tool call stats: {e}")
            raise

    async def get_subagent_history(
        self, user_id: int, chat_id: int | None = None
    ) -> list[dict]:
        """Get subagent execution history.

        Args:
            user_id: User ID
            chat_id: Chat ID (optional)

        Returns:
            List of subagent records
        """
        try:
            with _get_db_connection() as cursor:
                if chat_id:
                    cursor.execute(
                        """
                        SELECT subagent_name, instance_id, status, created_at,
                               started_at, completed_at, actual_iterations, max_iterations,
                               parent_agent, task_description, result_summary, error_message
                        FROM subagents
                        WHERE user_id = ? AND chat_id = ?
                        ORDER BY created_at DESC
                    """,
                        (user_id, chat_id),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT subagent_name, instance_id, status, created_at,
                               started_at, completed_at, actual_iterations, max_iterations,
                               parent_agent, task_description, result_summary, error_message
                        FROM subagents
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                    """,
                        (user_id,),
                    )

                history = []
                for row in cursor.fetchall():
                    history.append(dict(row))
                return history
        except Exception as e:
            logger.error(f"Failed to get subagent history: {e}")
            raise
