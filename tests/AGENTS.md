# Testing Guidance - AIBOTTO

Quick reference for writing tests in the AIBOTTO project.

## Import Paths

```python
# Tool executors
from src.aibotto.tools.executors.cli_executor import CLIExecutor
from src.aibotto.tools.executors.python_executor import PythonExecutor

# Security managers
from src.aibotto.tools.cli_security_manager import CLISecurityManager
from src.aibotto.tools.python_security_manager import PythonSecurityManager

# AI/LLM
from src.aibotto.ai.llm_client import LLMClient
from src.aibotto.ai.agentic_orchestrator import AgenticOrchestrator
from src.aibotto.ai.prompt_templates import SystemPrompts, ToolDescriptions
from src.aibotto.ai.subagent import SubAgent, init_subagents

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
    result = await mock_cli_executor.execute_command("date")
    assert result == "Mock output"
```

### Testing with Mock CLI Executor

```python
@pytest.fixture
def executor(self):
    with patch('src.aibotto.tools.executors.cli_executor.CLISecurityManager') as mock_security:
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

### Testing Security Validation

```python
@pytest.mark.asyncio
async def test_blocked_command():
    security_manager = CLISecurityManager()
    result = await security_manager.validate_command("rm -rf /")
    assert result["allowed"] is False
    assert "not allowed" in result["message"]
```

### Testing with Database

```python
@pytest.mark.asyncio
async def test_database_operation(temp_database):
    await temp_database.save_message(1, 1, 0, "user", "Hello")
    history = await temp_database.get_conversation_history(1, 1)
    assert len(history) == 1
```

## Mock Patch Paths

Patch at the **usage location**, not the definition:

```python
# CORRECT: Patch where it's imported
with patch('src.aibotto.tools.executors.cli_executor.CLISecurityManager') as mock:
    ...

# WRONG: Patching the original module
with patch('src.aibotto.tools.cli_security_manager.CLISecurityManager') as mock:
    ...
```

## Test File Organization

| What You're Testing | Where to Put It |
|---------------------|-----------------|
| CLI executor | `tests/unit/test_cli.py` |
| Python executor | `tests/unit/test_python_executor.py` |
| Tool calling logic | `tests/unit/test_tool_calling_edge_cases.py` |
| Subagent system | `tests/unit/test_subagent_*.py` |
| Web fetch | `tests/unit/test_web_fetch*.py` |
| Web search | `tests/unit/test_web_search.py` |
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
with patch('src.aibotto.tools.cli_security_manager.CLISecurityManager'):
    ...

# CORRECT - patches where it's used
with patch('src.aibotto.tools.executors.cli_executor.CLISecurityManager'):
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
├── config_helpers.py              # Test configuration helpers
├── unit/                          # Unit tests (32 files)
│   ├── test_backoff_handler.py
│   ├── test_base_security_config.py
│   ├── test_base_security_manager.py
│   ├── test_bot.py
│   ├── test_clear_command.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_db.py
│   ├── test_delegate_tool.py
│   ├── test_env_loader.py
│   ├── test_glm_fix.py
│   ├── test_llm_client.py
│   ├── test_llm_retry.py
│   ├── test_main.py
│   ├── test_prompt_cli.py
│   ├── test_prompt_templates.py
│   ├── test_python_executor.py
│   ├── test_refactored_security_config.py
│   ├── test_refactored_security_manager.py
│   ├── test_safe_commands.py
│   ├── test_setup_service.py
│   ├── test_subagent_datetime.py
│   ├── test_subagent_loader.py
│   ├── test_subagent_web_search.py
│   ├── test_tool_calling_edge_cases.py
│   ├── test_tool_executor_base.py
│   ├── test_user_aspect_executor.py
│   ├── test_web_fetch.py
│   ├── test_web_fetch_brotli_integration.py
│   ├── test_web_fetch_citations.py
│   ├── test_web_fetch_rss.py
│   └── test_web_search.py
└── e2e/                           # End-to-end tests (4 files)
    ├── test_complete_flow.py
    ├── test_parallel_tool_calls.py
    ├── test_tool_calling_visibility.py
    └── test_web_search_real.py
```

## Key Fixtures in conftest.py

### `mock_llm_client_with_responses`
Most important fixture for tool calling tests. Returns different responses based on query content:
- "date"/"day" → triggers `execute_cli_command` with `date`
- "weather" → triggers `execute_cli_command` with curl
- "system"/"uname" → triggers `execute_cli_command` with `uname -a`
- "capital of France" → direct response without tool calls
- "research"/"web research" → triggers `delegate_task` with web_research

### `temp_database`
Creates a real SQLite file, yields `DatabaseOperations` instance, cleans up after test.

### `mock_cli_executor`
Pre-configured mock with `execute_command` returning "Mock output".

## Quality Metrics

- **Test Count**: 335 tests (317 unit + 18 e2e)
- **Coverage**: 77%
- **All tests must pass** before committing
