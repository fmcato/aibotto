"""Generic subagent registry for managing all subagents."""

import logging
from typing import Type

from aibotto.ai.subagent.base import SubAgent

logger = logging.getLogger(__name__)


class SubAgentRegistry:
    """Registry for managing subagent types and instantiation."""

    _subagents: dict[str, Type[SubAgent]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        subagent_class: Type[SubAgent],
    ) -> None:
        """Register a subagent class with the registry.

        Args:
            name: Unique name for the subagent (e.g., "web_research")
            subagent_class: SubAgent subclass to register
        """
        if not issubclass(subagent_class, SubAgent):
            raise TypeError(f"{subagent_class} must be a subclass of SubAgent")

        cls._subagents[name] = subagent_class
        logger.info(f"Registered subagent: {name} -> {subagent_class.__name__}")

    @classmethod
    def get(cls, name: str) -> Type[SubAgent] | None:
        """Get a subagent class by name.

        Args:
            name: Subagent name

        Returns:
            SubAgent class or None if not found
        """
        return cls._subagents.get(name)

    @classmethod
    def create(cls, name: str, **kwargs) -> SubAgent | None:
        """Create an instance of a registered subagent.

        Args:
            name: Subagent name
            **kwargs: Additional kwargs to pass to subagent constructor

        Returns:
            SubAgent instance or None if not found
        """
        subagent_class = cls.get(name)
        if subagent_class is None:
            logger.warning(f"Subagent not found: {name}")
            return None

        try:
            return subagent_class(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create subagent {name}: {e}")
            return None

    @classmethod
    def list_subagents(cls) -> list[str]:
        """List all registered subagent names.

        Returns:
            List of subagent names
        """
        return list(cls._subagents.keys())

    @classmethod
    def has_subagent(cls, name: str) -> bool:
        """Check if a subagent is registered.

        Args:
            name: Subagent name

        Returns:
            True if registered, False otherwise
        """
        return name in cls._subagents
