"""
Unit tests for UserAspectExecutor.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.aibotto.tools.executors.user_aspect_executor import UserAspectExecutor


@pytest.fixture
def user_aspect_executor():
    """Create a UserAspectExecutor instance for testing."""
    return UserAspectExecutor()


@pytest.mark.asyncio
class TestUserAspectExecutor:
    """Test cases for UserAspectExecutor class."""

    async def test_execute_success(self, user_aspect_executor):
        """Test successful execution storing a user aspect."""
        mock_db_ops = MagicMock()
        mock_db_ops.store_user_aspect = AsyncMock(return_value=42)
        mock_db_ops.save_message_compat = AsyncMock()

        result = await user_aspect_executor.execute(
            '{"category": "interests", "aspect": "enjoys Python programming"}',
            user_id=123,
            db_ops=mock_db_ops,
            chat_id=456,
        )

        assert "Stored user aspect" in result
        assert "interests" in result
        mock_db_ops.store_user_aspect.assert_called_once_with(
            123, "interests", "enjoys Python programming", 0.5
        )

    async def test_execute_with_confidence(self, user_aspect_executor):
        """Test execution with confidence parameter."""
        mock_db_ops = MagicMock()
        mock_db_ops.store_user_aspect = AsyncMock(return_value=42)
        mock_db_ops.save_message_compat = AsyncMock()

        result = await user_aspect_executor.execute(
            '{"category": "personality", "aspect": "friendly", "confidence": 0.8}',
            user_id=123,
            db_ops=mock_db_ops,
        )

        assert "Stored user aspect" in result
        mock_db_ops.store_user_aspect.assert_called_once_with(123, "personality", "friendly", 0.8)

    async def test_execute_without_db_ops(self, user_aspect_executor):
        """Test execution without database operations - should still work."""
        result = await user_aspect_executor.execute(
            '{"category": "status", "aspect": "online"}', user_id=123
        )

        assert "stored" in result.lower()

    async def test_execute_missing_category(self, user_aspect_executor):
        """Test execution with missing category field."""
        result = await user_aspect_executor.execute('{"aspect": "likes Python"}')

        assert "required" in result.lower() or "category" in result.lower()

    async def test_execute_missing_aspect(self, user_aspect_executor):
        """Test execution with missing aspect field."""
        result = await user_aspect_executor.execute('{"category": "interests"}')

        assert "required" in result.lower() or "aspect" in result.lower()

    async def test_execute_invalid_json(self, user_aspect_executor):
        """Test execution with invalid JSON arguments."""
        result = await user_aspect_executor.execute("invalid json")

        assert "Error parsing arguments" in result

    async def test_execute_empty_category(self, user_aspect_executor):
        """Test execution with empty category."""
        result = await user_aspect_executor.execute('{"category": "", "aspect": "test"}')

        assert "required" in result.lower() or "category" in result.lower()

    async def test_execute_empty_aspect(self, user_aspect_executor):
        """Test execution with empty aspect."""
        result = await user_aspect_executor.execute('{"category": "interests", "aspect": ""}')

        assert "required" in result.lower() or "aspect" in result.lower()

    async def test_execute_confidence_out_of_range_low(self, user_aspect_executor):
        """Test execution with confidence < 0."""
        mock_db_ops = MagicMock()
        mock_db_ops.save_message_compat = AsyncMock()
        mock_db_ops.store_user_aspect = AsyncMock(return_value=1)

        result = await user_aspect_executor.execute(
            '{"category": "test", "aspect": "test", "confidence": -0.5}', db_ops=mock_db_ops
        )

        assert "between 0 and 1" in result

    async def test_execute_confidence_out_of_range_high(self, user_aspect_executor):
        """Test execution with confidence > 1."""
        mock_db_ops = MagicMock()
        mock_db_ops.save_message_compat = AsyncMock()
        mock_db_ops.store_user_aspect = AsyncMock(return_value=1)

        result = await user_aspect_executor.execute(
            '{"category": "test", "aspect": "test", "confidence": 1.5}', db_ops=mock_db_ops
        )

        assert "between 0 and 1" in result

    async def test_execute_valid_confidence_bounds(self, user_aspect_executor):
        """Test execution with valid confidence at boundaries (0 and 1)."""
        mock_db_ops = MagicMock()
        mock_db_ops.save_message_compat = AsyncMock()
        mock_db_ops.store_user_aspect = AsyncMock(return_value=1)

        await user_aspect_executor.execute(
            '{"category": "test", "aspect": "test1", "confidence": 0.0}', db_ops=mock_db_ops
        )
        await user_aspect_executor.execute(
            '{"category": "test", "aspect": "test2", "confidence": 1.0}', db_ops=mock_db_ops
        )

        assert mock_db_ops.store_user_aspect.call_count == 2

    async def test_execute_db_error(self, user_aspect_executor):
        """Test execution when database operation throws error."""
        mock_db_ops = MagicMock()
        mock_db_ops.save_message_compat = AsyncMock()
        mock_db_ops.store_user_aspect = AsyncMock(side_effect=Exception("DB error"))

        result = await user_aspect_executor.execute(
            '{"category": "test", "aspect": "test"}', db_ops=mock_db_ops
        )

        assert "DB error" in result

    async def test_execute_all_fields_present(self, user_aspect_executor):
        """Test execution with all fields."""
        mock_db_ops = MagicMock()
        mock_db_ops.save_message_compat = AsyncMock()
        mock_db_ops.store_user_aspect = AsyncMock(return_value=10)

        result = await user_aspect_executor.execute(
            '{"category": "profession", "aspect": "software engineer", "confidence": 0.9}',
            user_id=999,
            db_ops=mock_db_ops,
            chat_id=888,
        )

        assert "Stored user aspect" in result
        mock_db_ops.store_user_aspect.assert_called_once_with(999, "profession", "software engineer", 0.9)
