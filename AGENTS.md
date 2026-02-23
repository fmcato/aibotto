# AIBOTTO - AI Agent with CLI Tool Integration

## Spec
An AI agent that communicates through Telegram and uses CLI tools to fulfill user requests.

### Examples:
- User asks "What day is today?" → Agent uses Linux `date` command to answer
- User asks "What's the weather in London?" → Agent uses web_search tool to find current conditions
- User asks "Calculate 2^20" → Agent runs `python3 -c "print(2**20)"`

## Tech Stack
- **Python 3.12**: Core programming language
- **UV**: Project and dependency management, running tests, code execution
- **OpenAI-compatible LLM**: Configurable provider with tool calling functionality
- **SQLite**: For storing conversation history

## Project Structure

```
src/aibotto/
├── __init__.py
├── main.py                 # Telegram bot entry point
├── prompt_cli.py           # CLI prompt interface (aibotto-cli)
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration management
├── ai/
│   ├── __init__.py
│   ├── llm_client.py       # LLM client integration
│   ├── prompt_templates.py # System prompts and tool descriptions
│   └── tool_calling.py     # Tool calling functionality
├── bot/
│   ├── __init__.py
│   ├── telegram_bot.py     # Telegram bot interface
│   └── handlers.py         # Message handlers
├── db/
│   ├── __init__.py
│   ├── models.py           # Database models
│   └── operations.py       # Database operations
├── tools/                  # All LLM-callable tools
│   ├── __init__.py
│   ├── cli_executor.py     # Shell command execution
│   ├── security.py         # Command security validation
│   └── web_search.py       # Web search (DuckDuckGo)
└── utils/
    ├── __init__.py
    ├── helpers.py          # Utility functions
    ├── logging.py          # Logging setup
    └── message_splitter.py # Telegram message splitting
```

## Import Paths

```python
# Tools (LLM-callable)
from aibotto.tools.cli_executor import CLIExecutor
from aibotto.tools.security import SecurityManager
from aibotto.tools.web_search import WebSearchTool, search_web

# AI/LLM
from aibotto.ai.llm_client import LLMClient
from aibotto.ai.tool_calling import ToolCallingManager
from aibotto.ai.prompt_templates import SystemPrompts, ToolDescriptions

# Other modules
from aibotto.config.settings import Config
from aibotto.db.operations import DatabaseOperations
from aibotto.bot.telegram_bot import TelegramBot
```

## Entry Points

| Command | Module | Description |
|---------|--------|-------------|
| `aibotto` | `aibotto.main:main` | Telegram bot |
| `aibotto-cli` | `aibotto.prompt_cli:main` | Stateless CLI prompt interface |

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Telegram bot token | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_BASE_URL` | OpenAI API base URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |
| `DATABASE_PATH` | SQLite database path | `conversations.db` |
| `MAX_COMMAND_LENGTH` | Maximum command length | `300000` |
| `ALLOWED_COMMANDS` | Whitelist of commands | (empty) |
| `BLOCKED_COMMANDS` | Blacklist of commands | `rm -rf,sudo,dd,mkfs,fdisk,format,shutdown,reboot,poweroff,halt` |
| `MAX_HISTORY_LENGTH` | Maximum conversation history | `20` |
| `THINKING_MESSAGE` | Thinking indicator message | `🤔 Thinking...` |
| `DDGS_TIMEOUT` | DuckDuckGo search timeout (seconds) | `30` |
| `LLM_MAX_TOKENS` | Max tokens for LLM responses (0 = no limit) | `0` |
| `MAX_TOOL_ITERATIONS` | Maximum tool calling iterations | `10` |
| `WEB_FETCH_MAX_RETRIES` | Web fetch retry attempts | `3` |
| `WEB_FETCH_RETRY_DELAY` | Web fetch retry delay (seconds) | `1.0` |
| `WEB_FETCH_STRICT_CONTENT_TYPE` | Strict content type checking | `true` |
| `LLM_MAX_RETRIES` | LLM API retry attempts | `3` |
| `LLM_RETRY_DELAY` | LLM API retry delay (seconds) | `1.0` |

## Development Workflow

### Test-Driven Development (TDD)
Use red/green TDD

**ALWAYS write tests before implementation.** This is required for:
- New features
- Bug fixes
- Refactoring with behavior changes

#### TDD Cycle
1. **Write failing test** - Define expected behavior in a test
2. **Run test** - Confirm it fails (validates test works)
3. **Implement** - Write minimal code to pass the test
4. **Run tests** - All tests must pass
5. **Refactor** - Clean up while keeping tests green
6. **Commit** - Only after all tests pass

#### Example: Adding a New Tool
```bash
# 1. Write test first
# Edit tests/unit/test_my_tool.py

# 2. Run test (should fail)
uv run pytest tests/unit/test_my_tool.py -v

# 3. Implement tool
# Edit src/aibotto/tools/my_tool.py

# 4. Update tool definitions
# Edit src/aibotto/ai/prompt_templates.py  # Add tool description
# Edit src/aibotto/ai/tool_calling.py      # Add tool handler
# Edit src/aibotto/tools/__init__.py       # Export tool

# 5. Run all tests
uv run pytest

# 6. Commit
git add <list of changed files> && git commit
```

### Quality Checks
Pre-commit hooks run automatically via `pre-commit-checks.sh`:
- Ruff linting
- MyPy type checking
- Bandit security scanning
- pytest (all tests must pass)
- TODO/FIXME/HACK detection

### Common Commands

```bash
# Setup
uv sync

# Run Telegram bot
uv run python src/aibotto/main.py

# Run CLI interface
uv run aibotto-cli "what day is today"

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_web_fetch.py -v

# Run tests matching pattern
uv run pytest -k "web_fetch" -v

# Manual quality checks
uv run ruff check src/
uv run mypy src/
```

### Commit Format
```bash
git commit -m "<Brief message>

<Optional description>

Generated by Mistral Vibe.
Co-Authored-By: Mistral Vibe <vibe@mistral.ai>"
```

## Security Rules

- NEVER commit `.env` files or credentials
- NEVER commit API keys, tokens, or sensitive config
- ALWAYS use environment variables for sensitive data
- VERIFY with `git diff --staged` before committing

## Testing

See [tests/AGENTS.md](tests/AGENTS.md) for:
- Test patterns and examples
- Fixture usage guide
- Mock patch paths
- Common pitfalls

## Usage Examples

- **Date & Time**: "What day is today?" → Executes `date` command
- **File Operations**: "List files in current directory" → Executes `ls -la` command
- **System Information**: "Show system information" → Executes `uname -a` command
- **Calculations**: "Calculate 2^20" → Executes `python3 -c "print(2**20)"`
- **Web Search**: "What's the weather in London?" → Uses web_search tool to find current conditions
- **Web Search**: "Search for latest AI news" → Uses DuckDuckGo search tool

### CLI Interface

```bash
# Send a prompt via CLI (stateless, no database)
aibotto-cli "what day is today"

# Multiple words (no quotes needed)
aibotto-cli list files in current directory

# Verbose mode (shows debug output)
aibotto-cli -v "search for latest news about AI"
```
## Troubleshooting

- if you fail twice in a row to use the search_replace tool, switch to overwrite the whole file content instead
