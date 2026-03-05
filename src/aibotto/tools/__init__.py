"""
Tools module - All external tool integrations for the AI assistant.

This module contains all tools that the LLM can call:
- CLI command execution with security
- Web search functionality
- Web page content fetching
- Task delegation to specialized subagents
"""

from .executors.cli_executor import CLIExecutor
from .executors.python_executor import PythonExecutor
from .security import SecurityManager
from .cli_security_manager import CLISecurityManager
from .python_security_manager import PythonSecurityManager
from .web_fetch import WebFetchTool, fetch_webpage
from .web_search import WebSearchTool, search_web
from .delegate_tool import DelegateExecutor, delegate_task

__all__ = [
    "CLIExecutor",
    "PythonExecutor",
    "SecurityManager",
    "CLISecurityManager",
    "PythonSecurityManager",
    "WebFetchTool",
    "fetch_webpage",
    "WebSearchTool",
    "search_web",
    "DelegateExecutor",
    "delegate_task",
]
