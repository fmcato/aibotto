"""
Unit tests for enhanced DB module.
"""

import tempfile
import uuid

import pytest
from unittest.mock import patch

from src.aibotto.config.settings import Config
from src.aibotto.db.operations import DatabaseOperations


@pytest.fixture
def db_ops():
    """Create a DatabaseOperations instance with real SQLite database."""
    import sqlite3

    # Use a temporary file instead of :memory: for testing
    # because the context manager creates new connections
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_db_path = temp_file.name

    # Set the database path to the temporary file
    original_db_path = Config.DATABASE_PATH
    Config.DATABASE_PATH = temp_db_path

    # Initialize database operations
    db_ops = DatabaseOperations()

    yield db_ops

    # Cleanup
    try:
        import os

        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
    except Exception:
        pass
    finally:
        Config.DATABASE_PATH = original_db_path


class TestDatabaseOperations:
    """Test cases for enhanced DatabaseOperations class."""

    @pytest.mark.asyncio
    async def test_init_database_creates_tables(self, db_ops):
        """Test database initialization creates all tables."""
        import sqlite3

        # Connect to the same database created by the fixture
        conn = sqlite3.connect(db_ops.db_path)
        cursor = conn.cursor()

        # Get all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # Check each required table
        required_tables = ["conversations", "messages", "tool_calls", "subagents", "delegations"]
        for table in required_tables:
            assert table in tables, f"{table} table not created"

        conn.close()

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_new(self, db_ops):
        """Test creating a new conversation."""
        conversation_id = await db_ops.get_or_create_conversation(123, 456)
        assert conversation_id is not None
        assert isinstance(conversation_id, int)

        # Should return same ID on second call
        conversation_id_2 = await db_ops.get_or_create_conversation(123, 456)
        assert conversation_id == conversation_id_2

    @pytest.mark.asyncio
    async def test_save_message_with_conversation_id(self, db_ops):
        """Test saving a message with conversation ID."""
        conversation_id = await db_ops.get_or_create_conversation(123, 456)

        message_id = await db_ops.save_message(
            conversation_id=conversation_id,
            role="user",
            content="Hello",
            message_type="chat",
            source_agent="main_agent",
        )

        assert message_id is not None
        assert isinstance(message_id, int)

    @pytest.mark.asyncio
    async def test_save_tool_call(self, db_ops):
        """Test saving a tool call."""
        conversation_id = await db_ops.get_or_create_conversation(123, 456)
        message_id = await db_ops.save_message(
            conversation_id=conversation_id, role="assistant", content="", message_type="tool_call"
        )

        tool_call_id = str(uuid.uuid4())
        tool_id = await db_ops.save_tool_call(
            message_id=message_id,
            tool_name="search_web",
            tool_call_id=tool_call_id,
            arguments_json='{"query": "test"}',
            source_agent="main_agent",
            iteration_number=1,
        )

        assert tool_id is not None
        assert isinstance(tool_id, int)

    @pytest.mark.asyncio
    async def test_update_tool_call_result(self, db_ops):
        """Test updating tool call with result."""
        conversation_id = await db_ops.get_or_create_conversation(123, 456)
        message_id = await db_ops.save_message(
            conversation_id=conversation_id, role="assistant", content="", message_type="tool_call"
        )

        tool_call_id = str(uuid.uuid4())
        await db_ops.save_tool_call(
            message_id=message_id,
            tool_name="search_web",
            tool_call_id=tool_call_id,
            arguments_json='{"query": "test"}',
            source_agent="main_agent",
        )

        await db_ops.update_tool_call_result(
            tool_call_id=tool_call_id,
            result_content="Search results",
            status="completed",
        )

    @pytest.mark.asyncio
    async def test_save_subagent(self, db_ops):
        """Test saving a subagent instance."""
        subagent_id = await db_ops.save_subagent(
            subagent_name="web_research",
            instance_id=12345,
            user_id=123,
            chat_id=456,
            max_iterations=5,
            parent_agent="main_agent",
            task_description="Research topic",
        )

        assert subagent_id is not None
        assert isinstance(subagent_id, int)

    @pytest.mark.asyncio
    async def test_update_subagent_completion(self, db_ops):
        """Test updating subagent completion details."""
        subagent_id = await db_ops.save_subagent(
            subagent_name="web_research", instance_id=12345, user_id=123, chat_id=456
        )

        await db_ops.update_subagent_completion(
            db_subagent_id=subagent_id,
            result_summary="Research completed",
            actual_iterations=3,
        )

    @pytest.mark.asyncio
    async def test_save_delegation(self, db_ops):
        """Test saving a delegation event."""
        conversation_id = await db_ops.get_or_create_conversation(123, 456)
        message_id = await db_ops.save_message(
            conversation_id=conversation_id, role="assistant", content="", message_type="delegation"
        )
        subagent_id = await db_ops.save_subagent(
            subagent_name="web_research", instance_id=12345, user_id=123, chat_id=456
        )

        delegation_id = await db_ops.save_delegation(
            message_id=message_id,
            conversation_id=conversation_id,
            parent_agent="main_agent",
            child_agent_name="web_research",
            child_subagent_id=subagent_id,
            task_description="Delegated task",
            method_name="execute_task",
            user_id=123,
            chat_id=456,
            iteration_number=1,
        )

        assert delegation_id is not None
        assert isinstance(delegation_id, int)

    @pytest.mark.asyncio
    async def test_update_delegation_result(self, db_ops):
        """Test updating delegation with result."""
        conversation_id = await db_ops.get_or_create_conversation(123, 456)
        message_id = await db_ops.save_message(
            conversation_id=conversation_id, role="assistant", content="", message_type="delegation"
        )
        subagent_id = await db_ops.save_subagent(
            subagent_name="web_research", instance_id=12345, user_id=123, chat_id=456
        )
        delegation_id = await db_ops.save_delegation(
            message_id=message_id,
            conversation_id=conversation_id,
            parent_agent="main_agent",
            child_agent_name="web_research",
            child_subagent_id=subagent_id,
            task_description="Delegated task",
        )

        await db_ops.update_delegation_result(
            delegation_id=delegation_id,
            result_content="Delegation completed",
            status="completed",
        )

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, db_ops):
        """Test retrieving conversation history."""
        # Use completely unique IDs to avoid cross-test interference
        import time

        chat_id = int(time.time())

        conversation_id = await db_ops.get_or_create_conversation(123, chat_id)

        await db_ops.save_message(
            conversation_id=conversation_id,
            role="user",
            content="Hello",
            message_type="chat",
            source_agent="main_agent",
        )
        await db_ops.save_message(
            conversation_id=conversation_id,
            role="assistant",
            content="Hi there!",
            message_type="chat",
            source_agent="main_agent",
        )

        history = await db_ops.get_conversation_history(123, chat_id)

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there!"

    @pytest.mark.asyncio
    async def test_clear_conversation_history(self, db_ops):
        """Test clearing conversation history."""
        conversation_id = await db_ops.get_or_create_conversation(123, 456)

        await db_ops.save_message(
            conversation_id=conversation_id,
            role="user",
            content="Hello",
            message_type="chat",
            source_agent="main_agent",
        )

        await db_ops.clear_conversation_history(123, 456)

        # Get new conversation ID (old one is ended)
        new_conversation_id = await db_ops.get_or_create_conversation(123, 456)
        assert new_conversation_id != conversation_id

    @pytest.mark.asyncio
    async def test_replace_conversation_with_summary(self, db_ops):
        """Test replacing conversation with summary."""
        conversation_id = await db_ops.get_or_create_conversation(123, 456)

        await db_ops.save_message(
            conversation_id=conversation_id,
            role="user",
            content="Hello",
            message_type="chat",
            source_agent="main_agent",
        )

        await db_ops.replace_conversation_with_summary(123, 456, "Summary of conversation")

        history = await db_ops.get_conversation_history(123, 456)
        assert len(history) == 1
        assert history[0]["role"] == "system"
        assert history[0]["content"] == "Summary of conversation"

    @pytest.mark.asyncio
    async def test_get_tool_call_stats(self, db_ops):
        """Test getting tool call statistics."""
        conversation_id = await db_ops.get_or_create_conversation(123, 456)
        message_id = await db_ops.save_message(
            conversation_id=conversation_id, role="assistant", content="", message_type="tool_call"
        )

        tool_call_id = str(uuid.uuid4())
        tool_id = await db_ops.save_tool_call(
            message_id=message_id,
            tool_name="search_web",
            tool_call_id=tool_call_id,
            arguments_json='{"query": "test"}',
            source_agent="main_agent",
            iteration_number=1,
        )

        await db_ops.update_tool_call_result(
            tool_call_id=tool_call_id, result_content="Results", status="completed"
        )

        stats = await db_ops.get_tool_call_stats(123, 456)
        assert len(stats) >= 1
        assert stats[0]["tool_name"] == "search_web"
        assert stats[0]["count"] == 1

    @pytest.mark.asyncio
    async def test_get_subagent_history(self, db_ops):
        """Test getting subagent history."""
        subagent_id = await db_ops.save_subagent(
            subagent_name="web_research",
            instance_id=12345,
            user_id=123,
            chat_id=456,
            task_description="Research",
        )

        await db_ops.update_subagent_completion(
            db_subagent_id=subagent_id, result_summary="Done", actual_iterations=3
        )

        history = await db_ops.get_subagent_history(123, 456)
        assert len(history) >= 1
        assert history[0]["subagent_name"] == "web_research"
        assert history[0]["actual_iterations"] == 3

    @pytest.mark.asyncio
    async def test_mask_sensitive_data(self, db_ops):
        """Test that sensitive data is masked."""
        from src.aibotto.db.operations import mask_sensitive_data

        # Test API key masking
        content = 'OPENAI_API_KEY="sk-1234567890abcdef1234567890abcdef"'
        masked = mask_sensitive_data(content)
        assert "[REDACTED]" in masked
        assert "sk-1234567890abcdef1234567890abcdef" not in masked

        # Test token masking
        content = 'token: "abc123def456ghi789jkl012mno345"'
        masked = mask_sensitive_data(content)
        assert "[REDACTED]" in masked

        # Test safe content (should not be masked)
        content = "This is normal text without secrets"
        masked = mask_sensitive_data(content)
        assert "[REDACTED]" not in masked
