"""Unit tests for delegate tool functionality."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from aibotto.tools.delegate_tool import DelegateExecutor
from aibotto.ai.subagent.registry import SubAgentRegistry
from aibotto.db.operations import DatabaseOperations


class TestDelegateTool:
    """Test cases for delegate tool functionality."""

    @pytest.fixture
    def delegate_executor(self):
        """Create DelegateExecutor instance."""
        return DelegateExecutor()

    

    @pytest.mark.asyncio
    async def test_delegate_to_existing_subagent(self, delegate_executor, temp_database):
        """Test delegating to an existing subagent."""
        # Mock a subagent instance that returns a result
        mock_subagent = MagicMock()
        mock_subagent._instance_id = "mock_instance_id"
        mock_subagent.execute_task = AsyncMock(return_value="Mock result for: what is the weather today")

        # Mock the registry to create our mock subagent
        with patch.object(SubAgentRegistry, 'create', return_value=mock_subagent):
            arguments = json.dumps({
                "subagent_name": "web_research",
                "task_description": "what is the weather today"
            })
            
            result = await delegate_executor.execute(
                arguments, user_id=123, chat_id=456, db_ops=temp_database
            )
            
            assert result == "Mock result for: what is the weather today"

    @pytest.mark.asyncio
    async def test_delegate_to_nonexistent_subagent(self, delegate_executor, temp_database):
        """Test delegating to a non-existent subagent."""
        # Mock the registry to return None
        with patch.object(SubAgentRegistry, 'create', return_value=None):
            arguments = json.dumps({
                "subagent_name": "nonexistent_agent",
                "task_description": "test task"
            })
            
            result = await delegate_executor.execute(
                arguments, user_id=123, chat_id=456, db_ops=temp_database
            )
            
            assert "failed to create" in result.lower()

    @pytest.mark.asyncio
    async def test_delegate_with_missing_arguments(self, delegate_executor, temp_database):
        """Test delegate with missing required arguments."""
        # Test missing subagent_name
        arguments = json.dumps({
            "task_description": "test task"
        })
        
        result = await delegate_executor.execute(
            arguments, user_id=123, chat_id=456, db_ops=temp_database
        )
        
        assert "subagent_name" in result.lower()

        # Test missing task_description
        arguments = json.dumps({
            "subagent_name": "web_research"
        })
        
        result = await delegate_executor.execute(
            arguments, user_id=123, chat_id=456, db_ops=temp_database
        )
        
        assert "task_description" in result.lower()

    @pytest.mark.asyncio
    async def test_delegate_error_handling(self, delegate_executor, temp_database):
        """Test error handling in delegate execution."""
        # Mock a subagent that raises an exception
        mock_subagent = MagicMock()
        mock_subagent._instance_id = "error_instance_id"
        mock_subagent.execute_task = AsyncMock(side_effect=Exception("Subagent failed"))

        with patch.object(SubAgentRegistry, 'create', return_value=mock_subagent):
            arguments = json.dumps({
                "subagent_name": "error_agent",
                "task_description": "test task"
            })
            
            result = await delegate_executor.execute(
                arguments, user_id=123, chat_id=456, db_ops=temp_database
            )
            
            assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_delegate_with_invalid_json(self, delegate_executor, temp_database):
        """Test delegate with invalid JSON arguments."""
        result = await delegate_executor.execute(
            "invalid json", user_id=123, chat_id=456, db_ops=temp_database
        )

        assert "parsing" in result.lower()

    @pytest.mark.asyncio
    async def test_delegate_preserves_user_chat_context(self, delegate_executor, temp_database):
        """Test that delegate preserves user_id and chat_id context."""
        captured_user_id = None
        captured_chat_id = None
        
        async def mock_execute_task(**kwargs):
            nonlocal captured_user_id, captured_chat_id
            captured_user_id = kwargs.get("user_id")
            captured_chat_id = kwargs.get("chat_id")
            return "result"

        mock_subagent = MagicMock()
        mock_subagent._instance_id = "context_instance_id"
        mock_subagent.execute_task = AsyncMock(side_effect=mock_execute_task)

        with patch.object(SubAgentRegistry, 'create', return_value=mock_subagent):
            arguments = json.dumps({
                "subagent_name": "context_agent",
                "task_description": "test task"
            })
            
            await delegate_executor.execute(
                arguments, user_id=999, chat_id=888, db_ops=temp_database
            )
            
            assert captured_user_id == 999
            assert captured_chat_id == 888