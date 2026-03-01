"""Unit tests for research tool."""

import pytest
from unittest.mock import AsyncMock, patch

from src.aibotto.tools.research_tool import ResearchExecutor, research_topic
from aibotto.ai.subagent.registry import SubAgentRegistry
from aibotto.ai.subagent.web_research_agent import WebResearchAgent


class TestResearchTool:
    """Test cases for research tool."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Register web_research subagent for tests."""
        SubAgentRegistry.register("web_research", WebResearchAgent)

    @pytest.fixture
    def research_executor(self):
        """Create ResearchExecutor instance."""
        return ResearchExecutor()

    def test_executor_init(self, research_executor):
        """Test executor initialization."""
        assert research_executor is not None

    @pytest.mark.asyncio
    async def test_execute_valid_query(self, research_executor):
        """Test execution with valid query."""
        from unittest.mock import MagicMock
        
        mock_agent_class = MagicMock()
        mock_agent_instance = mock_agent_class.return_value
        mock_agent_instance.execute_research = AsyncMock(return_value="Research results")
        mock_agent_instance._instance_id = "test_instance"

        with patch('aibotto.ai.subagent.registry.SubAgentRegistry.get', return_value=mock_agent_class):
            result = await research_executor.execute(
                '{"query": "test topic", "num_results": 3}'
            )
            assert result == "Research results"
            mock_agent_instance.execute_research.assert_called_once_with(query="test topic", num_results=3, user_id=0, chat_id=0)

    @pytest.mark.asyncio
    async def test_execute_empty_query(self, research_executor):
        """Test execution with empty query."""
        result = await research_executor.execute('{"query": ""}')
        assert "cannot be empty" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_invalid_json(self, research_executor):
        """Test execution with invalid JSON."""
        result = await research_executor.execute('invalid json')
        assert "Invalid arguments format" in result

    @pytest.mark.asyncio
    async def test_execute_default_num_results(self, research_executor):
        """Test execution with default num_results."""
        from unittest.mock import MagicMock
        
        mock_agent_class = MagicMock()
        mock_agent_instance = mock_agent_class.return_value
        mock_agent_instance.execute_research = AsyncMock(return_value="Research results")
        mock_agent_instance._instance_id = "test_instance"

        with patch('aibotto.ai.subagent.registry.SubAgentRegistry.get', return_value=mock_agent_class):
            result = await research_executor.execute('{"query": "test"}')
            mock_agent_instance.execute_research.assert_called_once_with(query="test", num_results=5, user_id=0, chat_id=0)

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, research_executor):
        """Test error handling in execute."""
        from unittest.mock import MagicMock
        
        mock_agent_class = MagicMock()
        mock_agent_instance = mock_agent_class.return_value
        mock_agent_instance.execute_research = AsyncMock(side_effect=Exception("Agent error"))
        mock_agent_instance._instance_id = "test_instance"

        with patch('aibotto.ai.subagent.registry.SubAgentRegistry.get', return_value=mock_agent_class):
            result = await research_executor.execute('{"query": "test"}')
            assert "Error executing research" in result

    @pytest.mark.asyncio
    async def test_research_topic_function(self):
        """Test research_topic standalone function."""
        from unittest.mock import MagicMock
        
        mock_agent_class = MagicMock()
        mock_agent_instance = mock_agent_class.return_value
        mock_agent_instance.execute_research = AsyncMock(return_value="Results")
        mock_agent_instance._instance_id = "test_instance"

        with patch('aibotto.ai.subagent.registry.SubAgentRegistry.get', return_value=mock_agent_class):
            result = await research_topic("query", 10)
            assert result == "Results"
