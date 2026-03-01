"""Unit tests for generic subagent executor."""

import pytest
from unittest.mock import AsyncMock, patch

from aibotto.ai.subagent.subagent_executor import SubAgentConfig, SubAgentExecutor
from aibotto.ai.subagent.registry import SubAgentRegistry
from aibotto.ai.subagent.base import SubAgent
from aibotto.ai.subagent.web_research_agent import WebResearchAgent


class TestSubAgentExecutor:
    """Test cases for SubAgentExecutor."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Ensure web_research is registered."""
        SubAgentRegistry.register("web_research", WebResearchAgent)

    def test_init_with_config(self):
        """Test executor initialization with config."""
        config = SubAgentConfig(
            subagent_name="web_research",
            method="execute_research",
            method_kwargs={"query": "test", "num_results": 3}
        )
        executor = SubAgentExecutor(config)
        assert executor.config == config

    @pytest.mark.asyncio
    async def test_run_successful(self):
        """Test successful subagent execution."""
        config = SubAgentConfig(
            subagent_name="web_research",
            method="execute_research",
            method_kwargs={"query": "test", "num_results": 2}
        )

        with patch.object(WebResearchAgent, 'execute_research', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = "Research result"

            executor = SubAgentExecutor(config)
            result = await executor.run()

            assert result == "Research result"
            mock_method.assert_called_once_with(query="test", num_results=2, user_id=0, chat_id=0)

    @pytest.mark.asyncio
    async def test_run_subagent_not_found(self):
        """Test error when subagent not found."""
        config = SubAgentConfig(
            subagent_name="nonexistent",
            method="test_method",
            method_kwargs={}
        )

        executor = SubAgentExecutor(config)
        with pytest.raises(RuntimeError, match="Subagent 'nonexistent' not found"):
            await executor.run()

    @pytest.mark.asyncio
    async def test_run_method_not_found(self):
        """Test error when method not found on subagent."""
        config = SubAgentConfig(
            subagent_name="web_research",
            method="nonexistent_method",
            method_kwargs={}
        )

        executor = SubAgentExecutor(config)
        with pytest.raises(RuntimeError, match="Method 'nonexistent_method' not found"):
            await executor.run()

    @pytest.mark.asyncio
    async def test_run_method_exception(self):
        """Test error handling when method raises exception."""
        config = SubAgentConfig(
            subagent_name="web_research",
            method="execute_research",
            method_kwargs={"query": "test"}
        )

        with patch.object(WebResearchAgent, 'execute_research', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = ValueError("Test error")

            executor = SubAgentExecutor(config)
            with pytest.raises(RuntimeError, match="Error executing web_research.execute_research"):
                await executor.run()

    def test_config_defaults(self):
        """Test SubAgentConfig default values."""
        config = SubAgentConfig(
            subagent_name="test",
            method="test_method"
        )
        assert config.method_kwargs == {}
        assert config.user_id == 0
        assert config.chat_id == 0
