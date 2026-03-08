"""
Tool registry for managing tool executors.
"""

import logging

from .base import ToolExecutor, ToolExecutorFactory

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing tool executors."""

    def __init__(self) -> None:
        self._executors: dict[str, ToolExecutor] = {}
        self._factories: dict[str, ToolExecutorFactory] = {}

    def register_executor(self, tool_name: str, executor: ToolExecutor) -> None:
        """Register a tool executor.

        Args:
            tool_name: Name of the tool
            executor: Tool executor instance
        """
        self._executors[tool_name] = executor
        logger.info(f"Registered executor for tool: {tool_name}")

    def register_factory(self, tool_name: str, factory: ToolExecutorFactory) -> None:
        """Register a tool executor factory.

        Args:
            tool_name: Name of the tool
            factory: Tool executor factory
        """
        self._factories[tool_name] = factory
        logger.info(f"Registered factory for tool: {tool_name}")

    def get_executor(self, tool_name: str) -> ToolExecutor | None:
        """Get a tool executor.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool executor instance or None
        """
        # First check direct executors
        if tool_name in self._executors:
            return self._executors[tool_name]

        # Then check factories
        if tool_name in self._factories:
            return self._factories[tool_name].get_executor(tool_name)

        return None

    def get_registered_tools(self) -> list[str]:
        """Get list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._executors.keys()) + list(self._factories.keys())

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is registered, False otherwise
        """
        return tool_name in self._executors or tool_name in self._factories


class ToolRegistrySingleton:
    """Singleton registry for managing tool executors."""

    _instance = None
    _initialized = False
    _executors: dict[str, ToolExecutor] = {}
    _factories: dict[str, ToolExecutorFactory] = {}

    def __new__(cls) -> "ToolRegistrySingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize_once(self) -> None:
        """Initialize all tools once - safe to call multiple times."""
        if self._initialized:
            return

        from ..tools.executors.cli_executor import CLIExecutor
        from ..tools.executors.python_executor import PythonExecutor
        from ..tools.executors.web_fetch_executor import WebFetchExecutor
        from ..tools.executors.web_search_executor import WebSearchExecutor
        from ..tools.delegate_tool import DelegateExecutor
        from ..tools.executors.user_aspect_executor import UserAspectExecutor
        from ..ai.subagent import init_subagents

        # Create executors once (they're stateless)
        self._executors["execute_cli_command"] = CLIExecutor()
        self._executors["execute_python_code"] = PythonExecutor()
        self._executors["search_web"] = WebSearchExecutor()
        self._executors["fetch_webpage"] = WebFetchExecutor()
        self._executors["delegate_task"] = DelegateExecutor()
        user_aspect_executor = UserAspectExecutor()
        self._executors["store_user_aspect"] = user_aspect_executor

        # Initialize subagents once
        init_subagents()

        self._initialized = True
        logger.info("Initialized singleton tool registry")

    def register_executor(self, tool_name: str, executor: ToolExecutor) -> None:
        """Register a tool executor.

        Args:
            tool_name: Name of the tool
            executor: Tool executor instance
        """
        if not self._initialized:
            self.initialize_once()

        self._executors[tool_name] = executor
        logger.info(f"Registered executor for tool: {tool_name}")

    def register_factory(self, tool_name: str, factory: ToolExecutorFactory) -> None:
        """Register a tool executor factory.

        Args:
            tool_name: Name of the tool
            factory: Tool executor factory
        """
        if not self._initialized:
            self.initialize_once()

        self._factories[tool_name] = factory
        logger.info(f"Registered factory for tool: {tool_name}")

    def get_executor(self, tool_name: str) -> ToolExecutor | None:
        """Get a tool executor.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool executor instance or None
        """
        if not self._initialized:
            self.initialize_once()

        # First check direct executors
        if tool_name in self._executors:
            return self._executors[tool_name]

        # Then check factories
        if tool_name in self._factories:
            return self._factories[tool_name].get_executor(tool_name)

        return None

    def get_registered_tools(self) -> list[str]:
        """Get list of all registered tool names.

        Returns:
            List of tool names
        """
        if not self._initialized:
            self.initialize_once()

        return list(self._executors.keys()) + list(self._factories.keys())

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is registered, False otherwise
        """
        if not self._initialized:
            self.initialize_once()

        return tool_name in self._executors or tool_name in self._factories

    def is_initialized(self) -> bool:
        """Check if the registry has been initialized."""
        return self._initialized


# Global toolset instance (singleton)
toolset = ToolRegistrySingleton()


def get_toolset() -> ToolRegistrySingleton:
    """Get the global toolset singleton instance."""
    return toolset
