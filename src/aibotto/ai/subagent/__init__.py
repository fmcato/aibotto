"""Subagent system for specialized tasks with isolated LLM contexts."""

from aibotto.ai.subagent.base import SubAgent
from aibotto.ai.subagent.registry import SubAgentRegistry
from aibotto.ai.subagent.subagent_executor import SubAgentConfig, SubAgentExecutor
from aibotto.ai.subagent.web_research_agent import WebResearchAgent


def init_subagents() -> None:
    """Initialize and register all subagents."""
    # Register built-in subagents
    SubAgentRegistry.register("web_research", WebResearchAgent)


__all__ = [
    "SubAgent",
    "SubAgentRegistry",
    "SubAgentConfig",
    "SubAgentExecutor",
    "WebResearchAgent",
    "init_subagents",
]
