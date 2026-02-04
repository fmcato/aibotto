"""
Bot handlers for different types of messages and commands.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from telegram import Update
from telegram.ext import ContextTypes


class BaseHandler(ABC):
    """Base handler class."""

    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the update."""
        pass


class CommandHandler(BaseHandler):
    """Handler for bot commands."""

    def __init__(self, command: str, callback: Callable):
        self.command = command
        self.callback = callback

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle command."""
        await self.callback(update, context)


class MessageHandler(BaseHandler):
    """Handler for text messages."""

    def __init__(self, callback: Callable):
        self.callback = callback

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle message."""
        await self.callback(update, context)
