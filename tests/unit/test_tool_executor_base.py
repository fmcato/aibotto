"""
Unit tests for base ToolExecutor class refactoring.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.aibotto.tools.base import ToolExecutor
from src.aibotto.tools.base import ToolExecutionError


class DummyExecutor(ToolExecutor):
    """Concrete executor for testing base class."""

    def __init__(self, execute_result: str = "test_result") -> None:
        super().__init__()
        self.execute_result = execute_result
        self.do_execute_called = False
        self.do_execute_args = None
        self.do_execute_user_id = None
        self.do_execute_chat_id = None

    async def _do_execute(self, args: dict, user_id: int, chat_id: int = 0) -> str:
        self.do_execute_called = True
        self.do_execute_args = args
        self.do_execute_user_id = user_id
        self.do_execute_chat_id = chat_id
        return self.execute_result


@pytest.fixture
def executor():
    """Create a dummy executor for testing."""
    return DummyExecutor(execute_result="test_result")


@pytest.fixture
def mock_db_ops():
    """Create mock database operations."""
    mock_db = MagicMock()
    mock_db.save_message_compat = AsyncMock()
    return mock_db


@pytest.mark.asyncio
class TestToolExecutorBase:
    """Test cases for ToolExecutor base class refactored methods."""

    async def test_execute_basic_flow(self, executor):
        """Test basic execute flow dispatches to _do_execute."""
        args = '{"key": "value"}'
        result = await executor.execute(args, user_id=123)

        assert result == "test_result"
        assert executor.do_execute_called is True
        assert executor.do_execute_args == {"key": "value"}
        assert executor.do_execute_user_id == 123

    async def test_execute_with_db_ops_saves_result(self, executor, mock_db_ops):
        """Test execute saves result when db_ops provided."""
        args = '{"key": "value"}'
        result = await executor.execute(args, user_id=123, db_ops=mock_db_ops, chat_id=456)

        assert result == "test_result"
        mock_db_ops.save_message_compat.assert_called_once_with(
            user_id=123, chat_id=456, role="system", content="test_result"
        )

    async def test_execute_without_db_ops_skips_save(self, executor):
        """Test execute without db_ops doesn't attempt save."""
        args = '{"key": "value"}'
        result = await executor.execute(args, user_id=123, db_ops=None, chat_id=456)

        assert result == "test_result"

    async def test_parse_arguments_valid_json(self, executor):
        """Test parsing valid JSON arguments."""
        args = '{"command": "echo hello", "timeout": 30}'
        result = executor._parse_arguments(args)

        assert result == {"command": "echo hello", "timeout": 30}

    def test_parse_arguments_invalid_json_raises_error(self, executor):
        """Test parsing invalid JSON raises ToolExecutionError."""
        invalid_json = "not valid json"

        with pytest.raises(ToolExecutionError) as exc_info:
            executor._parse_arguments(invalid_json)

        assert "Error parsing arguments" in str(exc_info.value)

    def test_parse_arguments_empty_json_object(self, executor):
        """Test parsing empty JSON object."""
        args = "{}"
        result = executor._parse_arguments(args)

        assert result == {}

    async def test_save_if_needed_with_db_ops(self, executor, mock_db_ops):
        """Test _save_if_needed saves when db_ops provided."""
        content = "test output"

        await executor._save_if_needed(mock_db_ops, user_id=123, chat_id=456, content=content)

        mock_db_ops.save_message_compat.assert_called_once_with(
            user_id=123, chat_id=456, role="system", content=content
        )

    async def test_save_if_needed_without_db_ops(self, executor):
        """Test _save_if_needed skips when db_ops is None."""
        content = "test output"

        await executor._save_if_needed(None, user_id=123, chat_id=456, content=content)

    async def test_execute_invalid_json_returns_error(self, executor):
        """Test execute with invalid JSON returns error message."""
        invalid_json = "not valid json"
        result = await executor.execute(invalid_json, user_id=123, db_ops=None, chat_id=456)

        assert "Error parsing arguments" in result

    async def test_execute_invalid_json_saves_to_db(self, executor, mock_db_ops):
        """Test execute with invalid JSON saves error to database."""
        invalid_json = "not valid json"
        result = await executor.execute(invalid_json, user_id=123, db_ops=mock_db_ops, chat_id=456)

        assert "Error parsing arguments" in result
        mock_db_ops.save_message_compat.assert_called_once()
        assert "Error parsing arguments" in mock_db_ops.save_message_compat.call_args[1]["content"]

    async def test_execute_exception_in_do_execute(self, executor):
        """Test execute handles exception in _do_execute."""
        class FailingExecutor(ToolExecutor):
            async def _do_execute(self, args: dict, user_id: int, chat_id: int = 0) -> str:
                raise ValueError("Something went wrong")

        failing_executor = FailingExecutor()
        result = await failing_executor.execute('{"test": "data"}', user_id=123)

        assert "Something went wrong" in result

    async def test_execute_exception_saves_to_db(self, mock_db_ops):
        """Test execute saves exception message to database."""
        class FailingExecutor(ToolExecutor):
            async def _do_execute(self, args: dict, user_id: int, chat_id: int = 0) -> str:
                raise ValueError("Something went wrong")

        failing_executor = FailingExecutor()
        result = await failing_executor.execute('{"test": "data"}', user_id=123, db_ops=mock_db_ops, chat_id=456)

        assert "Something went wrong" in result
        mock_db_ops.save_message_compat.assert_called_once()
        assert "Something went wrong" in mock_db_ops.save_message_compat.call_args[1]["content"]


class TestToolExecutionError:
    """Test cases for ToolExecutionError exception."""

    def test_tool_execution_error_creation(self):
        """Test ToolExecutionError can be created."""
        error = ToolExecutionError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
