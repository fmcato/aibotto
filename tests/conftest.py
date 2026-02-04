"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.aibotto.config.settings import Config
from src.aibotto.db.operations import DatabaseOperations
from src.aibotto.cli.executor import CLIExecutor
from src.aibotto.ai.llm_client import LLMClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    original_config = {}
    for key in dir(Config):
        if not key.startswith('_'):
            original_config[key] = getattr(Config, key)
    
    # Override with test values
    Config.TELEGRAM_TOKEN = "test_token"
    Config.OPENAI_API_KEY = "test_key"
    Config.DATABASE_PATH = ":memory:"  # In-memory database for testing
    Config.MAX_COMMAND_LENGTH = 1000
    Config.BLOCKED_COMMANDS = ["rm -rf", "sudo"]
    
    yield Config
    
    # Restore original values
    for key, value in original_config.items():
        setattr(Config, key, value)


@pytest.fixture
def mock_db_ops(mock_config):
    """Mock database operations."""
    return DatabaseOperations()


@pytest.fixture
def mock_cli_executor():
    """Mock CLI executor."""
    executor = CLIExecutor()
    executor.execute_command = AsyncMock(return_value="Mock output")
    return executor


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = LLMClient()
    client.chat_completion = AsyncMock()
    return client