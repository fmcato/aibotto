"""
Subagent-specific toolset for isolated tool access.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SubAgentToolset:
    """Toolset for managing tool executors available to subagents."""

    def __init__(self, instance_id: int) -> None:
        self._instance_id = instance_id
        self._executors: Dict[str, Any] = {}
        logger.info(f"Created SubAgentToolset for instance {instance_id}")

    def register_tool(self, tool_name: str, executor: Any) -> None:
        """Register a tool executor for this subagent.

        Args:
            tool_name: Name of the tool
            executor: Tool executor instance
        """
        self._executors[tool_name] = executor
        logger.info(f"SubAgent {self._instance_id}: Registered tool: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a tool executor for this subagent.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool executor instance or None
        """
        return self._executors.get(tool_name)

    def get_executor(self, tool_name: str) -> Optional[Any]:
        """Get a tool executor for this subagent.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool executor instance or None
        """
        return self._executors.get(tool_name)

    def get_registered_tools(self) -> List[str]:
        """Get list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._executors.keys())

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is available, False otherwise
        """
        return tool_name in self._executors
