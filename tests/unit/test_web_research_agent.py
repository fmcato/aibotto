"""Unit tests for web research subagent."""

import pytest
from unittest.mock import patch

from src.aibotto.ai.subagent.web_research_agent import WebResearchAgent


class TestWebResearchAgent:
    """Test cases for WebResearchAgent."""

    @pytest.fixture
    def research_agent(self):
        """Create WebResearchAgent instance."""
        return WebResearchAgent()

    def test_init(self, research_agent):
        """Test initialization."""
        assert research_agent.max_iterations == 5

    def test_system_prompt_content(self, research_agent):
        """Test system prompt contains research-specific content."""
        prompt = research_agent._get_system_prompt()
        assert "research assistant" in prompt.lower()
        assert "search" in prompt.lower()
        assert "citation" in prompt.lower()

    def test_tool_definitions(self, research_agent):
        """Test subagent has access to web tools."""
        defs = research_agent._get_tool_definitions()
        assert len(defs) == 2
        tool_names = [d['function']['name'] for d in defs]
        assert 'search_web' in tool_names
        assert 'fetch_webpage' in tool_names

    @pytest.mark.asyncio
    async def test_execute_research_basic(self, research_agent):
        """Test basic research execution."""
        with patch.object(research_agent, 'execute_task') as mock_execute:
            mock_execute.return_value = "Research complete"

            result = await research_agent.execute_research("test query")
            assert result == "Research complete"
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_research_with_num_results(self, research_agent):
        """Test research with custom num_results."""
        with patch.object(research_agent, 'execute_task') as mock_execute:
            mock_execute.return_value = "Research complete"

            result = await research_agent.execute_research("test", num_results=3)
            assert result == "Research complete"

    @pytest.mark.asyncio
    async def test_execute_research_error_handling(self, research_agent):
        """Test research error handling."""
        with patch.object(research_agent, 'execute_task') as mock_execute:
            mock_execute.side_effect = Exception("Test error")

            result = await research_agent.execute_research("test")
            assert "error" in result.lower()
            assert "Test error" in result
