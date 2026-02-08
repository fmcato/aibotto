# Testing Guidance - AIBOTTO

Quick reference for writing tests in the AIBOTTO project.

## Import Paths

```python
# Tools (LLM-callable)
from src.aibotto.tools.cli_executor import CLIExecutor
from src.aibotto.tools.security import SecurityManager
from src.aibotto.tools.web_search import WebSearchTool, search_web

# AI/LLM
from src.aibotto.ai.llm_client import LLMClient
from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.ai.prompt_templates import SystemPrompts, ToolDescriptions

# Other modules
from src.aibotto.config.settings import Config
from src.aibotto.db.operations import DatabaseOperations
from src.aibotto.bot.telegram_bot import TelegramBot
from src.aibotto.prompt_cli import parse_args, run_prompt, main
```

## Test Naming Convention

```
test_<method>_<scenario>
test_<method>_<error_condition>
```

Examples:
- `test_execute_command_success`
- `test_execute_command_blocked`
- `test_validate_command_too_long`

## Fixture Selection Guide

| Fixture | Use When | Type |
|---------|----------|------|
| `mock_cli_executor` | Unit tests needing CLI | Mock (returns "Mock output") |
| `real_cli_executor` | E2E tests | Real execution |
| `mock_llm_client` | Simple LLM tests | Mock with basic responses |
| `mock_llm_client_with_responses` | Tool calling tests | Mock with tool call logic |
| `mock_llm_client_direct_response` | Non-tool responses | Mock without tool calls |
| `temp_database` | DB integration tests | Real SQLite file |
| `mock_config` | Unit tests needing config | Sets test values |
| `e2e_test_config` | E2E tests | Full test configuration |

## Common Test Patterns

### Async Test Pattern

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_async_operation(mock_cli_executor):
    """Test description."""
    result = await mock_cli_executor.execute_command("date")
    assert result == "Mock output"
```

### Testing with Mock CLI Executor

```python
from src.aibotto.tools.cli_executor import CLIExecutor

@pytest.fixture
def executor(self):
    """Create a CLIExecutor instance for testing."""
    with patch('src.aibotto.tools.cli_executor.SecurityManager') as mock_security:
        executor = CLIExecutor()
        executor.security_manager = MagicMock()
        return executor

@pytest.mark.asyncio
async def test_execute_command_success(self, executor):
    executor.security_manager.validate_command = AsyncMock(
        return_value={"allowed": True}
    )
    
    with patch('asyncio.create_subprocess_shell') as mock_subprocess:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
        mock_subprocess.return_value = mock_process
        
        result = await executor.execute_command("echo hello")
        assert result == "Success"
```

### Testing Tool Calling

```python
from src.aibotto.ai.tool_calling import ToolCallingManager

def test_tool_calling(self, mock_llm_client_with_responses, mock_cli_executor):
    """Test tool calling with mocked dependencies."""
    manager = ToolCallingManager()
    manager.llm_client = mock_llm_client_with_responses
    manager.cli_executor = mock_cli_executor
    return manager
```

### Testing Security Validation

```python
from src.aibotto.tools.security import SecurityManager

@pytest.mark.asyncio
async def test_blocked_command():
    security_manager = SecurityManager()
    result = await security_manager.validate_command("rm -rf /")
    
    assert result["allowed"] is False
    assert "not allowed" in result["message"]
```

### Testing with Database

```python
@pytest.mark.asyncio
async def test_database_operation(temp_database):
    """Test using real temporary database."""
    await temp_database.save_message(1, 1, 0, "user", "Hello")
    history = await temp_database.get_conversation_history(1, 1)
    assert len(history) == 1
```

## Mock Patch Paths

Patch at the **usage location**, not the definition:

```python
# CORRECT: Patch where it's imported
with patch('src.aibotto.tools.cli_executor.SecurityManager') as mock:
    ...

# WRONG: Patching the original module
with patch('src.aibotto.tools.security.SecurityManager') as mock:
    ...
```

## Test File Organization

| What You're Testing | Where to Put It |
|---------------------|-----------------|
| Tool (CLI, web search) | `tests/unit/test_cli.py` or `tests/unit/test_web_search.py` |
| Tool calling logic | `tests/unit/test_tool_calling_edge_cases.py` |
| Telegram bot | `tests/unit/test_bot.py` |
| CLI prompt interface | `tests/unit/test_prompt_cli.py` |
| Database operations | `tests/unit/test_db.py` |
| Security validation | `tests/unit/test_safe_commands.py` |
| Full workflow | `tests/e2e/test_*.py` |

## Common Pitfalls

### 1. Missing async decorator
```python
# WRONG
async def test_something():
    ...

# CORRECT
@pytest.mark.asyncio
async def test_something():
    ...
```

### 2. Wrong mock return value for async
```python
# WRONG
mock_obj.async_method = MagicMock(return_value="result")

# CORRECT
mock_obj.async_method = AsyncMock(return_value="result")
```

### 3. Patching wrong path
```python
# WRONG - patches the class definition
with patch('src.aibotto.tools.security.SecurityManager'):
    ...

# CORRECT - patches where it's used
with patch('src.aibotto.tools.cli_executor.SecurityManager'):
    ...
```

### 4. Using real API keys in tests
```python
# WRONG
Config.OPENAI_API_KEY = "sk-real-key-..."

# CORRECT - use mock_config fixture or test values
Config.OPENAI_API_KEY = "test_key"
```

### 5. Not cleaning up database
```python
# WRONG - leaves test database
def test_something():
    db = DatabaseOperations()
    ...

# CORRECT - use temp_database fixture
def test_something(temp_database):
    db = temp_database
    ...
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_cli.py

# Run specific test
uv run pytest tests/unit/test_cli.py::TestCLIExecutor::test_execute_command_success

# Run with verbose output
uv run pytest -v

# Run only unit tests
uv run pytest tests/unit/

# Run only e2e tests
uv run pytest tests/e2e/
```

## Test Structure

```
tests/
├── conftest.py                    # Fixtures (DO NOT MODIFY without review)
├── unit/                          # Unit tests (mocked dependencies)
│   ├── test_bot.py               # Telegram bot tests
│   ├── test_clear_command.py     # /clear command tests
│   ├── test_cli.py               # CLI executor tests
│   ├── test_config.py            # Config module tests
│   ├── test_db.py                # Database module tests
│   ├── test_factual_responses.py # Factual response system tests
│   ├── test_llm_client.py        # LLM client tests
│   ├── test_main.py              # Main entry point tests
│   ├── test_message_splitter.py  # Message splitting tests
│   ├── test_prompt_cli.py        # CLI prompt interface tests
│   ├── test_safe_commands.py     # Security validation tests
│   ├── test_tool_calling_edge_cases.py  # Tool calling edge cases
│   └── test_web_search.py        # Web search unit tests
├── e2e/                          # End-to-end tests (real infrastructure)
│   ├── test_basic_tool_interactions.py
│   ├── test_complete_flow.py
│   ├── test_parallel_tool_calls.py
│   ├── test_tool_calling_visibility.py
│   └── test_web_search_real.py
└── fixtures/                      # Test fixtures and data
```

## Key Fixtures in conftest.py

### `mock_llm_client_with_responses`
The most important fixture for tool calling tests. Returns different responses based on query content:
- "date"/"day" queries → triggers `execute_cli_command` with `date`
- "weather" queries → triggers `execute_cli_command` with curl
- "system"/"uname" queries → triggers `execute_cli_command` with `uname -a`
- "capital of France" → direct response without tool calls

### `temp_database`
Creates a real SQLite file, yields `DatabaseOperations` instance, cleans up after test.

### `mock_cli_executor`
Pre-configured mock with `execute_command` returning "Mock output".

## Quality Metrics

- **Test Count**: 121 tests
- **Coverage**: 83%
- **All tests must pass** before committing
