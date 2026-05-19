# AIBOTTO - AI Telegram Bot with CLI Integration

A Python-based AI bot that communicates through Telegram and uses CLI tools, web search, and Python code execution to fulfill user requests.

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- `TELEGRAM_TOKEN` (from @BotFather)
- `OPENAI_API_KEY` (from OpenAI or compatible provider)

### 3. Run

```bash
aibotto              # Start Telegram bot + API server
aibotto-cli          # CLI mode for sending prompts from terminal
```

Or directly:
```bash
uv run python src/aibotto/main.py
```

## Features

- **Telegram Bot** - Conversational AI via Telegram with thinking indicators
- **CLI Tool Execution** - Run system commands, Python code, and file operations
- **Web Research** - DuckDuckGo search and webpage fetching with source evaluation
- **Subagent System** - Isolated LLM contexts for complex tasks (e.g., `web_research`)
- **FastAPI Server** - REST API at `POST /api/send` and `GET /api/health`
- **SQLite Persistence** - Conversation history and tool call tracking
- **Security** - Command blacklisting, input validation, audit logging

## Subagent System

Subagents run in isolated LLM contexts to prevent main context bloat.

- **Config**: `src/aibotto/config/subagents/<name>/config.yaml` + `prompt.md`
- **Available**: `web_research` (multi-source search with citations)
- **Usage**: `delegate_task(subagent_name="web_research", task_description="...")`

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_TOKEN` | Required | Telegram bot token |
| `OPENAI_API_KEY` | Required | OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API base URL |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | LLM model |
| `DATABASE_PATH` | `conversations.db` | SQLite path |
| `MAX_COMMAND_LENGTH` | `300000` | Max command length |
| `BLOCKED_COMMANDS` | `rm -rf,sudo,dd,...` | Blacklisted commands |
| `MAX_TOOL_ITERATIONS` | `10` | Max tool-calling turns |
| `LLM_MAX_RETRIES` | `3` | LLM API retries |
| `WEB_FETCH_MAX_RETRIES` | `3` | Web fetch retries |

See `.env.example` for all options.

## Development

```bash
uv run pytest                          # All tests (335 total)
uv run pytest tests/unit/              # Unit tests only
uv run pytest tests/unit/test_cli.py   # Single test file
uv run ruff check src/                 # Lint
uv run ruff check --fix src/           # Auto-fix lint
uv run mypy src/                       # Type check
./pre-commit-checks.sh                 # Pre-commit (requires staged changes)
```

Pre-commit order: Ruff → MyPy → Bandit → pytest → TODO check.

## Docker

```bash
# Quick start
docker compose build && docker compose up -d

# Build and run manually
docker build -t aibotto .
docker run -d --name aibotto --env-file .env -v aibot_data:/app/data aibotto
```

Database persists in the `aibot_data` volume. See `docker-compose.yml` for resource limits.

## Security

- Commands validated against `BLOCKED_COMMANDS`
- Optional `ALLOWED_COMMANDS` whitelist mode
- Isolated subprocess execution
- Never commit `.env`, API keys, or tokens

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Module not found | Run `uv sync` |
| Telegram token error | Check `.env` for correct token |
| OpenAI API error | Verify API key and `OPENAI_BASE_URL` |
| E2E tests hang | Run `uv run pytest tests/unit/` instead |
| Database error | Check write permissions in project directory |

Logs: `aibotto.log`

## License

GNU General Public License v3.0

## Acknowledgments

- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram framework
- [OpenAI](https://openai.com/) - AI models
- [UV](https://docs.astral.sh/uv/) - Python package management
- [DuckDuckGo](https://duckduckgo.com/) - Web search
