"""
Pytest configuration and fixtures.
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, Mock

import pytest

from src.aibotto.ai.llm_client import LLMClient
from src.aibotto.cli.executor import CLIExecutor
from src.aibotto.config.settings import Config
from src.aibotto.db.operations import DatabaseOperations


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_database():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        temp_db_path = temp_file.name

    # Set the database path to the temporary file
    original_db_path = Config.DATABASE_PATH
    Config.DATABASE_PATH = temp_db_path

    # Initialize database operations
    db_ops = DatabaseOperations()

    yield db_ops

    # Cleanup
    try:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
    except Exception:
        pass  # Ignore cleanup errors
    finally:
        # Restore original database path
        Config.DATABASE_PATH = original_db_path


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
    Config.OPENAI_BASE_URL = "https://api.openai.com/v1"
    Config.OPENAI_MODEL = "gpt-3.5-turbo"
    Config.DATABASE_PATH = ":memory:"  # In-memory database for unit tests
    Config.MAX_COMMAND_LENGTH = 1000
    Config.BLOCKED_COMMANDS = ["rm -rf", "sudo"]
    Config.MAX_HISTORY_LENGTH = 20
    Config.THINKING_MESSAGE = "🤔 Thinking..."

    yield Config

    # Restore original values
    for key, value in original_config.items():
        setattr(Config, key, value)


@pytest.fixture
def real_db_ops(mock_config, temp_database):
    """Real database operations for e2e tests."""
    return temp_database


@pytest.fixture
def mock_cli_executor():
    """Mock CLI executor for unit tests."""
    executor = CLIExecutor()
    executor.execute_command = AsyncMock(return_value="Mock output")
    return executor


@pytest.fixture
def real_cli_executor():
    """Real CLI executor for e2e tests."""
    executor = CLIExecutor()
    return executor


class TestLLMClient(LLMClient):
    """Test LLM client that uses configurable test values."""

    def __init__(self, api_key="test_key", base_url="https://api.openai.com/v1", model="gpt-3.5-turbo"):
        # Initialize with test values
        self.test_api_key = api_key
        self.test_base_url = base_url
        self.test_model = model
        self.chat_completion = AsyncMock()

        # Set up mock responses
        self.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from the mock LLM."
                }
            }]
        }

    async def test_chat_completion(self, messages, **kwargs):
        """Test method that returns predictable responses."""
        # Return different responses based on the query
        user_message = messages[-1]["content"] if messages else ""

        if "date" in user_message.lower():
            response = "The current date is Monday, February 3, 2026."
        elif "time" in user_message.lower():
            response = "The current time is 2:30 PM."
        elif "weather" in user_message.lower():
            response = "The weather is 15°C and sunny."
        elif "system" in user_message.lower() or "uname" in user_message.lower():
            response = "Linux Ubuntu 5.15.0-88-generic x86_64"
        else:
            response = "This is a test response from the mock LLM."

        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response
                }
            }]
        }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for unit tests."""
    return TestLLMClient()


@pytest.fixture
def real_llm_client():
    """Configurable LLM client for e2e tests."""
    return TestLLMClient(
        api_key="test_openai_key",
        base_url="https://api.openai.com/v1",
        model="gpt-3.5-turbo"
    )


@pytest.fixture
def e2e_test_config():
    """Configuration specifically for e2e tests."""
    original_config = {}
    for key in dir(Config):
        if not key.startswith('_'):
            original_config[key] = getattr(Config, key)

    # Override with e2e test values
    Config.TELEGRAM_TOKEN = "test_e2e_token"
    Config.OPENAI_API_KEY = "test_e2e_key"
    Config.OPENAI_BASE_URL = "https://api.openai.com/v1"
    Config.OPENAI_MODEL = "gpt-3.5-turbo"
    Config.DATABASE_PATH = ":memory:"  # Will be overridden by temp_database fixture
    Config.MAX_COMMAND_LENGTH = 1000
    Config.BLOCKED_COMMANDS = ["rm -rf", "sudo", "dd", "mkfs", "fdisk", "format", "shutdown", "reboot", "poweroff", "halt"]
    Config.MAX_HISTORY_LENGTH = 20
    Config.THINKING_MESSAGE = "🤔 Thinking..."

    yield Config

    # Restore original values
    for key, value in original_config.items():
        setattr(Config, key, value)


@pytest.fixture
def conversation_data():
    """Sample conversation data for testing."""
    return [
        {"role": "user", "content": "What day is today?"},
        {"role": "assistant", "content": "Today is Monday, February 3, 2026."},
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "The weather is 15°C and sunny."},
    ]


@pytest.fixture
def tool_calling_data():
    """Sample tool calling data for testing."""
    return {
        "type": "function",
        "function": {
            "name": "execute_cli_command",
            "arguments": '{"command": "date"}'
        }
    }


@pytest.fixture
def command_result():
    """Sample command execution result."""
    return {
        "command": "date",
        "output": "Mon Feb  3 14:30:45 UTC 2026",
        "error": None,
        "success": True
    }


@pytest.fixture
def security_test_data():
    """Security test data."""
    return {
        "safe_commands": [
            "date",
            "ls -la",
            "pwd",
            "uname -a",
            "echo 'hello'",
            "curl -A 'Mozilla/5.0' wttr.in?format=3"
        ],
        "blocked_commands": [
            "rm -rf /",
            "sudo rm -rf",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs /dev/sda",
            "shutdown -h now",
            "reboot"
        ]
    }


class MockToolCall:
    """Mock tool call object."""
    def __init__(self, function_name, arguments):
        self.function = MockFunction(function_name, arguments)
        self.id = "test_tool_call"
        self.type = "function"


class MockFunction:
    """Mock function object."""
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class MockMessage:
    """Mock message object."""
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class MockChoice:
    """Mock choice object."""
    def __init__(self, message_content, tool_calls=None):
        self.message = MockMessage(message_content, tool_calls)


class MockResponse:
    """Mock response object."""
    def __init__(self, choices):
        self.choices = choices


@pytest.fixture
def mock_llm_client_with_responses():
    """Mock LLM client with predictable responses for tool calling tests."""
    client = TestLLMClient()
    
    # Set up different responses based on the query and message history
    async def mock_chat_completion(messages, **kwargs):
        # Find the original user message (not tool results)
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg["content"]
                break
        
        # Check if tools parameter is provided (indicating tool calling mode)
        tools = kwargs.get('tools', [])
        
        # Check if we have tool results in the messages
        tool_results = [msg for msg in messages if msg.get("role") == "tool"]
        
        # Check if we have error results in the messages
        error_results = [msg for msg in messages if msg.get("role") == "tool" and "error" in msg.get("content", "").lower()]
        
        if tools and not tool_results:
            # First call with tools - return tool calls
            if "day" in user_message.lower() or "date" in user_message.lower():
                return MockResponse([MockChoice(
                    "I need to get the current date.",
                    [MockToolCall("execute_cli_command", '{"command": "date"}')]
                )])
            elif "weather" in user_message.lower():
                return MockResponse([MockChoice(
                    "I need to get the weather information.",
                    [MockToolCall("execute_cli_command", '{"command": "curl wttr.in/London?format=3"}')]
                )])
            elif "system" in user_message.lower() or "uname" in user_message.lower():
                return MockResponse([MockChoice(
                    "I need to get system information.",
                    [MockToolCall("execute_cli_command", '{"command": "uname -a"}')]
                )])
            elif "files" in user_message.lower() or "ls" in user_message.lower():
                return MockResponse([MockChoice(
                    "I need to list the files in the current directory.",
                    [MockToolCall("execute_cli_command", '{"command": "ls -la"}')]
                )])
            elif "capital" in user_message.lower() and "france" in user_message.lower():
                return MockResponse([MockChoice("Paris is the capital of France.")])
            elif "stock price" in user_message.lower():
                return MockResponse([MockChoice("I don't have access to real-time stock data to predict future prices.")])
            else:
                return MockResponse([MockChoice("This is a direct response without tool calls.")])
        
        elif tools and error_results:
            # Handle error case - return error response
            return MockResponse([MockChoice("Error executing command: Command not found")])
        
        elif tools and tool_results:
            # Second call with tools and tool results - return final response
            if "date" in user_message.lower() and "time" in user_message.lower():
                return MockResponse([MockChoice("Today is Monday, February 3, 2025, and the current time is 14:30:45.")])
            elif "day" in user_message.lower() or "date" in user_message.lower():
                return MockResponse([MockChoice("Today is Monday, February 3, 2025.")])
            elif "weather" in user_message.lower():
                return MockResponse([MockChoice("The weather in London is partly cloudy with a temperature of 15°C.")])
            elif "system" in user_message.lower() or "uname" in user_message.lower():
                return MockResponse([MockChoice("Linux Ubuntu 5.15.0-88-generic x86_64")])
            elif "files" in user_message.lower() or "ls" in user_message.lower():
                return MockResponse([MockChoice("total 16\ndrwxr-xr-x 2 user user 4096 Feb  3 10:00 .\ndrwxr-xr-x 5 user user 4096 Feb  3 10:00 ..\n-rw-r--r-- 1 user user 123 Feb  3 10:00 test.txt")])
            else:
                return MockResponse([MockChoice("This is a response after tool execution.")])
        
        else:
            # Non-tool calling mode - return direct responses
            if "hello" in user_message.lower():
                return MockResponse([MockChoice("Hello! How can I help you today?")])
            elif "capital" in user_message.lower() and "france" in user_message.lower():
                return MockResponse([MockChoice("Paris is the capital of France.")])
            elif "stock price" in user_message.lower():
                return MockResponse([MockChoice("I don't have access to real-time stock data to predict future prices.")])
            else:
                return MockResponse([MockChoice("This is a direct response without tool calls.")])
    
    client.chat_completion = mock_chat_completion
    return client


@pytest.fixture
def mock_llm_client_direct_response():
    """Mock LLM client that returns direct responses without tool calls."""
    client = TestLLMClient()
    
    async def mock_chat_completion(messages, **kwargs):
        user_message = messages[-1]["content"] if messages else ""
        
        if "hello" in user_message.lower():
            return MockResponse([MockChoice("Hello! How can I help you today?")])
        else:
            return MockResponse([MockChoice("I don't have access to real-time data for that question.")])
    
    client.chat_completion = mock_chat_completion
    return client


@pytest.fixture
def mock_llm_client_with_error():
    """Mock LLM client that returns error responses."""
    client = TestLLMClient()
    
    async def mock_chat_completion(messages, **kwargs):
        user_message = messages[-1]["content"] if messages else ""
        
        if "error" in user_message.lower():
            raise Exception("Test error from LLM client")
        
        return MockResponse([MockChoice("This is a normal response.")])
    
    client.chat_completion = mock_chat_completion
    return client