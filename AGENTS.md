# AIBOTTO - AI Agent with CLI Tool Integration

AI agent communicating via Telegram and using CLI tools.

## Build & Quality Commands

### Development Setup
```bash
uv sync                                # Install all dependencies
uv sync --dev                          # Install dev dependencies
```

### Testing Commands
```bash
uv run pytest                         # Run all tests
uv run pytest tests/unit/test_cli.py  # Run specific test file
uv run pytest tests/unit/test_cli.py::TestCLIExecutor::test_execute_command_success  # Single test
uv run pytest tests/unit/ --ignore=tests/e2e/  # Unit tests only
uv run pytest -k "web_fetch" -v       # Tests matching pattern
uv run pytest --cov=src --cov-report=html  # Coverage report
```

### Linting & Code Quality
```bash
uv run ruff check src/                 # Linting
uv run ruff check --fix src/           # Auto-fix linting
uv run ruff format src/                # Format code
uv run mypy src/                       # Type checking
uv run bandit -r src/                  # Security scan
```

### Pre-commit Quality Checks
```bash
# First stage your changes
git add <files>

# Run quality checks (requires staged changes)
./pre-commit-checks.sh

# If checks pass, commit:
git commit -m 'your commit message'
```

**Check order:**
1. Ruff linting
2. MyPy type checking  
3. Bandit security scanning
4. pytest (all tests must pass)
5. TODO comment check in production code

## Subagent System

### Architecture
The system uses subagents for specialized tasks with isolated LLM contexts to prevent main context bloat.

### Main Agent Tools
- `execute_command` - CLI operations (date, system info, Python code execution)
- `search_web` - Quick web search using DuckDuckGo
- `fetch_webpage` - Fetch known URLs (user-provided URLs)
- `delegate_task` - Generic tool for delegating to any registered subagent

### Available Subagents

#### Config-Driven Subagent System
Subagents are defined using YAML configuration files with full flexibility for LLM providers, models, system prompts, and tools.

**Configuration Location:** `src/aibotto/config/subagents.yaml`

**Available Subagents:**
- `web_research` - Comprehensive web research with search, fetch, and synthesis capabilities

**Access:**
- `delegate_task` with `subagent_name="web_research"`

**Capabilities:**
- Config-driven behavior via YAML
- Per-agent LLM provider and model selection
- Dynamic tool lists
- Configurable iteration limits
- Source credibility evaluation (.gov, .edu, established news)
- Multi-source synthesis
- Inline citations [Title](URL)

**Flow:**
1. Main agent calls `delegate_task(subagent_name="web_research", task_description="query")`
2. Config-driven subagent created from YAML definition
3. Agent searches, fetches, synthesizes internally
4. Returns summary with citations to main agent
5. Main agent receives only final result (context stays clean)

### Benefits
- **Context Efficiency**: Main context contains only synthesized results, not every intermediate operation
- **Specialization**: Each subagent has specialized prompts for its domain
- **Isolation**: Subagent failures don't pollute main context
- **Extensibility**: Easy to add more subagent types via `delegate_task` tool
- **Flexibility**: Generic `delegate_task` means no need to update main agent tools for new subagents

## Code Style Guidelines

### Imports & Formatting
- Line length: 88 chars max (Ruff)
- Type hints: Always use for params and returns
- Imports: stdlib → third-party → local
- Quotes: Double quotes unless single avoids escaping
- Trailing commas: In multi-line structures

```python
import asyncio
import logging
from typing import Any

from aibotto.config.settings import Config

async def execute_command(command: str, timeout: float = 30.0) -> str:
    ...
```

### Naming Conventions
- Classes: `PascalCase` (e.g., `LLMClient`)
- Functions/methods: `snake_case` (e.g., `execute_command`)
- Variables: `snake_case` (e.g., `command_output`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_COMMAND_LENGTH`)
- Private: Leading underscore (e.g., `_rate_limit_reset_time`)
- Use `Optional[T]` not `T | None` for consistency

### Error Handling
- Catch specific exceptions, not generic `Exception`
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Provide clear, actionable error messages
- Always use try/except around async operations

```python
try:
    result = await asyncio.wait_for(subprocess.communicate(), timeout=timeout)
except asyncio.TimeoutError:
    logger.warning(f"Command timed out after {timeout}s: {command}")
    raise CommandTimeoutError(f"Command timed out: {command}")
```

### Logging & Security
- Use `logger = logging.getLogger(__name__)` at module level
- Never log passwords, API keys, or personal information
- Use environment variables for sensitive configuration
- Validate all external inputs

### Test-Driven Development (Mandatory)
TDD IS REQUIRED - This is not optional. All code changes must follow the test-driven development workflow:

**TDD Workflow (Always Follow This Order):**
1. **RED**: Write a failing test that defines the desired behavior
2. **GREEN**: Write the minimal implementation to make the test pass
3. **REFACTOR**: Improve the code while keeping tests passing
4. **REPEAT**: Continue until feature is complete

**TDD Requirements:**
- NEVER write production code without a failing test first
- Write tests that describe expected behavior, not implementation details
- Keep tests small, focused, and independent
- Mock external dependencies (APIs, databases, file I/O)
- Run tests frequently during development (after each small change)
- If you cannot write a test, reconsider if the code should be written

**Why TDD Is Mandated:**
- Prevents bugs from being introduced
- Serves as living documentation
- Enables confident refactoring
- Catches integration issues early
- Reduces debugging time

### Testing Guidelines
- Unit tests go in `tests/unit/`, E2E tests in `tests/e2e/`
- Use `@pytest.mark.asyncio` for async tests
- Follow patterns in `tests/AGENTS.md` for fixtures and mocking
- **All tests must pass** before committing

## Tool Calling Architecture

Tool calling requires assistant `tool_calls` before `tool` results:
```python
Iteration 1:
- LLM: {"role": "assistant", "tool_calls": [...]}
- Add: {"role": "assistant", "tool_calls": [...]}
- Add: {"role": "tool", "tool_call_id": "...", "content": "..."}

Iteration 2: LLM sees complete interchange, no duplicates
```

## Import Paths

```python
# Core tools
from aibotto.tools.web_fetch import fetch_webpage
from aibotto.tools.web_search import search_web
from aibotto.tools.security import SecurityManager
from aibotto.tools.toolset import get_toolset

# Tool executors
from aibotto.tools.executors.python_executor import PythonExecutor

# Security managers (separate validators for CLI and Python)
from aibotto.tools.cli_security_manager import CLISecurityManager
from aibotto.tools.python_security_manager import PythonSecurityManager

# Security configuration
from aibotto.config.cli_security_config import CLISecurityConfig
from aibotto.config.python_security_config import PythonSecurityConfig

# AI components
from aibotto.ai.agentic_orchestrator import AgenticOrchestrator
from aibotto.ai.llm_client import LLMClient
from aibotto.ai.prompt_templates import SystemPrompts
from aibotto.ai.subagent import SubAgent, init_subagents

# Database models and operations
from aibotto.db import Conversation, Message, ToolCall, SubAgent, Delegation
from aibotto.db.operations import DatabaseOperations
```

## Configuration

| Variable | Required | Default |
|----------|----------|---------|
| `TELEGRAM_TOKEN` | Yes | - |
| `OPENAI_API_KEY` | Yes | - |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | No | `gpt-3.5-turbo` |
| `MAX_TOOL_ITERATIONS` | No | `10` |

## Security Rules

- NEVER commit `.env`, API keys, or tokens
- ALWAYS use environment variables for sensitive data
- VERIFY with `git diff --staged` before committing
- Commands validated against `BLOCKED_COMMANDS`

## Troubleshooting

- E2E tests hang: `uv run pytest tests/unit/ --ignore=tests/e2e/`
- Failed search_replace twice: Use write tool to overwrite entire file
- Tool message issues: Ensure assistant messages include `tool_calls` before `tool` results

## Testing Reference

For comprehensive testing patterns, fixtures, and examples, see `tests/AGENTS.md`.

