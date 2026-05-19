# AIBOTTO - AI Agent with CLI Tool Integration

AI agent communicating via Telegram, using CLI tools and web research to fulfill user requests.

## Quick Commands

```bash
uv sync                                # Install dependencies
./pre-commit-checks.sh                 # Pre-commit checks (requires staged changes)
uv run pytest                          # All tests (335 total)
uv run pytest tests/unit/              # Unit tests only (faster)
uv run pytest tests/unit/test_cli.py   # Single test file
uv run ruff check src/                 # Lint
uv run ruff check --fix src/           # Auto-fix lint
uv run mypy src/                       # Type check
```

**Pre-commit order** (enforced by `./pre-commit-checks.sh`): Ruff → MyPy → Bandit → pytest → TODO check.

## Architecture

```
src/aibotto/
├── main.py              # Entry point: starts Telegram bot + FastAPI server
├── prompt_cli.py        # CLI entry point (aibotto-cli)
├── bot/                 # Telegram bot (handlers, services, utils)
├── ai/                  # LLM client, agentic orchestrator, subagent system
├── tools/               # Tool executors (CLI, Python, web fetch/search, delegation)
├── config/              # Settings, security configs, YAML subagent definitions
├── db/                  # SQLite models and operations
├── api/                 # FastAPI server (POST /api/send, GET /api/health)
└── utils/               # Logging, helpers
```

**Key classes**: `AgenticOrchestrator`, `LLMClient`, `ToolExecutionOrchestrator`, `ToolRegistrySingleton`, `DatabaseOperations`, `TelegramBot`, `ResponseSender`.

**Tool registry**: Singleton pattern via `get_toolset()`. Tools are registered once at startup. Do not instantiate `ToolRegistry` (removed).

## Subagent System

Subagents run in isolated LLM contexts to prevent main context bloat.

**Config location**: `src/aibotto/config/subagents/<name>/config.yaml` + `prompt.md`

**Available subagents**: `web_research` (comprehensive web search with source evaluation and citations)

**Usage**: Main agent calls `delegate_task(subagent_name="web_research", task_description="...")`. Subagent returns synthesized summary with inline citations `[Title](URL)`.

**Init flow**: `init_subagents()` in `ai/subagent/__init__.py` loads YAML configs from `src/aibotto/config/subagents/` and registers them via `SubAgentRegistry`.

## Import Paths

```python
from aibotto.tools.toolset import get_toolset
from aibotto.tools.cli_security_manager import CLISecurityManager
from aibotto.tools.python_security_manager import PythonSecurityManager
from aibotto.ai.agentic_orchestrator import AgenticOrchestrator
from aibotto.ai.llm_client import LLMClient
from aibotto.ai.prompt_templates import SystemPrompts, ToolDescriptions
from aibotto.ai.subagent import SubAgent, init_subagents
from aibotto.ai.tool_executor import ToolExecutionOrchestrator
from aibotto.db.operations import DatabaseOperations
```

**Note**: `aibotto.tools.security` was removed. Use `CLISecurityManager` / `PythonSecurityManager` instead.

## Configuration

| Variable | Required | Default |
|----------|----------|---------|
| `TELEGRAM_TOKEN` | Yes | - |
| `OPENAI_API_KEY` | Yes | - |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | No | `gpt-3.5-turbo` |
| `MAX_TOOL_ITERATIONS` | No | `10` |

## Code Conventions

- Line length: 88 chars (Ruff)
- Type hints required for all params and returns
- Use `Optional[T]` not `T | None`
- Double quotes unless single avoids escaping
- `logger = logging.getLogger(__name__)` at module level

## Testing

- Unit tests: `tests/unit/`, E2E: `tests/e2e/`
- `asyncio_mode = "auto"` in pytest config (no need for `@pytest.mark.asyncio` on async functions)
- See `tests/AGENTS.md` for fixtures and mocking patterns
- **All tests must pass** before committing

## Security

- NEVER commit `.env`, API keys, or tokens
- Commands validated against `BLOCKED_COMMANDS` in config
- Use `git diff --staged` before committing

## Troubleshooting

- E2E tests hang: run `uv run pytest tests/unit/` instead
- Tool message issues: assistant messages must include `tool_calls` before `tool` results
