"""Unit tests for subagent registry."""

import pytest

from aibotto.ai.subagent.base import SubAgent
from aibotto.ai.subagent.registry import SubAgentRegistry
from aibotto.ai.subagent.web_research_agent import WebResearchAgent


class MockSubAgent(SubAgent):
    """Mock subagent for testing."""

    async def test_method(self, arg1: str, arg2: int = 0) -> str:
        """Test method for mock agent."""
        return f"Mock: {arg1}, {arg2}"


class TestSubAgentRegistry:
    """Test cases for SubAgentRegistry."""

    def test_register_subagent(self):
        """Test registering a subagent."""
        SubAgentRegistry.register("mock", MockSubAgent)

        assert SubAgentRegistry.has_subagent("mock")
        assert SubAgentRegistry.get("mock") == MockSubAgent

    def test_get_nonexistent_subagent(self):
        """Test getting a non-existent subagent."""
        assert SubAgentRegistry.get("nonexistent") is None

    def test_create_subagent(self):
        """Test creating a subagent instance."""
        SubAgentRegistry.register("mock_create", MockSubAgent)

        instance = SubAgentRegistry.create("mock_create")
        assert instance is not None
        assert isinstance(instance, MockSubAgent)

    def test_create_nonexistent_subagent(self):
        """Test creating a non-existent subagent."""
        instance = SubAgentRegistry.create("nonexistent")
        assert instance is None

    def test_list_subagents(self):
        """Test listing all registered subagents."""
        SubAgentRegistry.register("test_list", MockSubAgent)

        subagents = SubAgentRegistry.list_subagents()
        assert len(subagents) > 0
        assert "test_list" in subagents

    def test_has_subagent(self):
        """Test checking if subagent exists."""
        SubAgentRegistry.register("test_has", MockSubAgent)

        assert SubAgentRegistry.has_subagent("test_has") is True
        assert SubAgentRegistry.has_subagent("nonexistent") is False

    def test_register_invalid_subagent(self):
        """Test that registering non-SubAgent class raises error."""
        with pytest.raises(TypeError):
            SubAgentRegistry.register("invalid", str)  # type: ignore

    def test_web_research_registered(self):
        """Test that WebResearchAgent is registered."""
        assert SubAgentRegistry.has_subagent("web_research")
        assert SubAgentRegistry.get("web_research") == WebResearchAgent
