"""
Tools module - All external tool integrations for the AI assistant.

This module contains all tools that the LLM can call:
- CLI command execution with security
- Web search functionality
- Web page content fetching
"""

from .cli_executor import CLIExecutor
from .security import SecurityManager
from .web_fetch import WebFetchTool, fetch_webpage
from .web_search import WebSearchTool, search_web

__all__ = [
    "CLIExecutor",
    "SecurityManager",
    "WebFetchTool",
    "fetch_webpage",
    "WebSearchTool",
    "search_web",
]
