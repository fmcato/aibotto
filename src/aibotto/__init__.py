"""
AIBot - AI Bot that communicates through Telegram and uses CLI tools to fulfill user requests.

This package provides a modular and extensible AI bot with the following components:
- Bot: Telegram bot interface
- AI: LLM integration and tool calling
- CLI: Command execution with security features
- DB: Database operations for conversation history
- Config: Configuration management
- Utils: Utility functions
"""

__version__ = "0.1.0"
__author__ = "AIBot Team"
__email__ = "support@aibotto.com"

from .main import main

__all__ = ["main"]
