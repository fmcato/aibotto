"""Subagent system for specialized tasks with isolated LLM contexts."""

from aibotto.ai.subagent.base import SubAgent as ConfigDrivenSubAgent
from aibotto.ai.subagent.loader import load_subagents_from_config
from aibotto.ai.subagent.registry import SubAgentRegistry
from aibotto.ai.subagent.subagent_executor import SubAgentConfig, SubAgentExecutor


def init_subagents() -> None:
    """Initialize and register all subagents from config."""
    load_subagents_from_config()


__all__ = [
    "SubAgentRegistry",
    "SubAgentConfig",
    "SubAgentExecutor",
    "init_subagents",
    "load_subagents_from_config",
    "ConfigDrivenSubAgent",
]
