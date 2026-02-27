# AIBOTTO - AI Agent with CLI Tool Integration

AI agent communicating via Telegram and using CLI tools.

## Build & Quality Commands

```bash
uv sync                                # Install deps
uv run pytest                         # Run all tests
uv run pytest tests/unit/test_cli.py  # Run single file
uv run pytest tests/unit/test_cli.py::TestCLIExecutor::test_execute_command_success
uv run pytest tests/unit/ --ignore=tests/e2e/
uv run pytest -k "web_fetch" -v

uv run ruff check src/                 # Linting
uv run ruff check --fix src/           # Auto-fix
uv run mypy src/                       # Type checking
uv run bandit -r src/                  # Security scan
```

### Pre-commit Hooks
- Ruff linting
- MyPy type checking
- Bandit security scanning
- pytest (all tests must pass)


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

### Test-Driven Development
ALWAYS write tests before implementation

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
from aibotto.tools.web_fetch import fetch_webpage
from aibotto.tools.web_search import search_web
from aibotto.tools.security import SecurityManager
from aibotto.ai.agentic_orchestrator import AgenticOrchestrator
from aibotto.ai.llm_client import LLMClient
from aibotto.ai.prompt_templates import SystemPrompts
from aibotto.config.settings import Config
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

