"""Unit tests for subagent base class."""

import pytest
from unittest.mock import AsyncMock, patch

from src.aibotto.ai.subagent.base import SubAgent


class TestSubAgent:
    """Test cases for SubAgent base class."""

    @pytest.fixture
    def subagent(self):
        """Create a SubAgent instance."""
        return SubAgent(max_iterations=5)

    def test_init(self, subagent):
        """Test subagent initialization."""
        assert subagent.max_iterations == 5
        assert subagent.llm_client is not None

    def test_get_system_prompt(self, subagent):
        """Test default system prompt."""
        prompt = subagent._get_system_prompt()
        assert "helpful assistant" in prompt.lower()

    def test_get_tool_definitions(self, subagent):
        """Test default tool definitions."""
        defs = subagent._get_tool_definitions()
        assert defs == []

    @pytest.mark.asyncio
    async def test_execute_task_success(self, subagent):
        """Test successful task execution."""
        with patch.object(subagent.llm_client, 'chat_completion') as mock_chat:
            mock_chat.return_value = {
                "choices": [{
                    "message": {
                        "content": "Success response",
                        "tool_calls": None
                    }
                }]
            }

            result = await subagent.execute_task("test message")
            assert "Success response" in result
