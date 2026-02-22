"""
Tool registry for managing tool executors.
"""

import logging
from typing import Any, Dict, Optional

from .base import ToolExecutor, ToolExecutorFactory

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing tool executors."""
    
    def __init__(self) -> None:
        self._executors: Dict[str, ToolExecutor] = {}
        self._factories: Dict[str, ToolExecutorFactory] = {}
    
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
    
    def get_executor(self, tool_name: str) -> Optional[ToolExecutor]:
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


# Global registry instance
tool_registry = ToolRegistry()