"""
Base interfaces for tool executors.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol


class ToolExecutor(ABC):
    """Abstract base class for tool executors."""
    
    @abstractmethod
    async def execute(self, arguments: str, user_id: int = 0, db_ops: Any = None, chat_id: int = 0) -> str:
        """Execute the tool with given arguments.
        
        Args:
            arguments: JSON string of arguments
            user_id: User ID for logging
            db_ops: Database operations instance
            chat_id: Chat ID for database operations
            
        Returns:
            Tool execution result as string
        """
        pass


class ToolExecutorFactory(Protocol):
    """Protocol for creating tool executors."""
    
    def get_executor(self, tool_name: str) -> ToolExecutor | None:
        """Get an executor for a specific tool name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool executor instance or None
        """
        pass