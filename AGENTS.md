# AIBOTTO - AI Agent with CLI Tool Integration

## Spec
An AI agent that communicates through Telegram and uses CLI tools to fulfill user requests.

### Examples:
- User asks "What day is today?" → Agent uses Linux `date` command to answer
- User asks "What's the weather in London?" → Agent uses curl command against weather API to get forecast in JSON and answers appropriately

## Tech Stack
- **Python 3**: Core programming language
- **UV**: Project and dependency management, running tests, code execution
- **OpenAI-compatible LLM**: Configurable provider with tool calling functionality
- **SQLite**: For storing conversation history

## Development & Contributing
- Apply YAGNI (You Ain't Gonna Need It) principle for simplicity and maintainability
- **MUST use TDD approach**: Write tests before implementation for new features and bugfixes
- Maintain comprehensive test suite to prevent regressions
- **IMPORTANT**: Always commit changes after completing tasks and passing all quality checks
- **CRITICAL SECURITY**: Never commit credentials, tokens, API keys, or sensitive information

## Implementation Status ✅ COMPLETED

### Project Structure
```
src/aibotto/
├── __init__.py
├── main.py                 # Main entry point
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration management
├── ai/
│   ├── __init__.py
│   ├── llm_client.py       # LLM client integration
│   └── tool_calling.py     # Tool calling functionality
├── bot/
│   ├── __init__.py
│   ├── telegram_bot.py     # Telegram bot interface
│   └── handlers.py         # Message handlers
├── cli/
│   ├── __init__.py
│   ├── executor.py         # CLI command executor
│   └── security.py         # Security manager
├── db/
│   ├── __init__.py
│   ├── models.py           # Database models
│   └── operations.py       # Database operations
└── utils/
    ├── __init__.py
    ├── helpers.py          # Utility functions
    └── logging.py          # Logging setup
```

### Core Features
- ✅ **Modular Architecture**: Clean separation of concerns with dedicated modules
- ✅ **Telegram Bot Interface**: Full bot with `/start`, `/help`, and message handling
- ✅ **LLM Integration**: OpenAI-compatible API client with tool calling
- ✅ **CLI Tool Execution**: Safe command execution with security measures
- ✅ **Database Management**: SQLite with conversation history persistence
- ✅ **Configuration Management**: Environment-based configuration with validation
- ✅ **Security Features**: Command blocking, length limits, and optional whitelist
- ✅ **Async/Await**: Full async implementation for performance
- ✅ **Comprehensive Testing**: Unit tests with pytest and async support
- ✅ **Code Quality**: Ruff linting, MyPy type checking
- ✅ **Documentation**: Complete README and inline documentation

### Security Features
- **Command Length Limiting**: Maximum 1000 characters to prevent abuse
- **Command Blacklist**: Blocks dangerous commands (rm -rf, sudo, shutdown, etc.)
- **Optional Whitelist**: Can restrict to only allowed commands
- **Sandboxed Execution**: Commands run in isolated subprocess environments
- **Input Validation**: Comprehensive security checks before execution

### Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Telegram bot token | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_BASE_URL` | OpenAI API base URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |
| `DATABASE_PATH` | SQLite database path | `conversations.db` |
| `MAX_COMMAND_LENGTH` | Maximum command length | `1000` |
| `ALLOWED_COMMANDS` | Whitelist of commands | (empty) |
| `BLOCKED_COMMANDS` | Blacklist of commands | `rm -rf,sudo,dd,mkfs,fdisk,format,shutdown,reboot,poweroff,halt` |
| `MAX_HISTORY_LENGTH` | Maximum conversation history | `20` |
| `THINKING_MESSAGE` | Thinking indicator message | `🤔 Thinking...` |

### Usage Examples
- **Date & Time**: "What day is today?" → Executes `date` command
- **File Operations**: "List files in current directory" → Executes `ls -la` command
- **System Information**: "Show system information" → Executes `uname -a` command
- **Weather API**: "What's the weather in London?" → Executes curl command to weather API

### Development Tools
- **Package Management**: UV for fast dependency management
- **Linting**: Ruff for fast Python linting
- **Type Checking**: MyPy for static type analysis
- **Pre-commit**: Git hooks for code quality

## Installation & Setup
```bash
# Clone and setup
git clone <repository>
cd aibotto
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run tests
uv run pytest

# Run the bot
uv run python src/aibotto/main.py
```

## Git Commit Guidelines

### Quality Checks (Required)
```bash
uv run pytest    # Run tests
uv run ruff check src/  # Lint code
uv run mypy src/  # Type checking
```

### Pre-Commit Checklist
1. Check README.md for documentation updates
2. Verify no credentials/secrets in staged changes
3. Ensure all quality checks pass
4. Review changes with `git diff --staged`

### Security Rules
- NEVER commit `.env` files or credentials
- NEVER commit API keys, tokens, or sensitive config
- ALWAYS use environment variables for sensitive data
- VERIFY with `git diff --staged` before committing

### Commit Format
```bash
git commit -m "<Brief message>

<Description>

Generated by Mistral Vibe.
Co-Authored-By: Mistral Vibe <vibe@mistral.ai>"
```

### Important Reminder
Always commit changes after completing tasks and passing quality checks. Failure to commit means work will be lost.

## Next Steps & Future Enhancements
- **Database Optimization**: Fix database connection issues
- **CLI Test Suite**: Improve CLI command execution tests
- **API Integration**: Test and verify OpenAI API connectivity
- **Performance**: Optimize async operations and database queries
- **Monitoring**: Add logging and monitoring capabilities
- **Deployment**: Add Docker support and deployment scripts
- **Documentation**: Add API documentation and usage guides

## Current Status
**Beta** - Core functionality implemented. Main architecture is solid, but some tests are failing. Security features work well, and tool calling is operational.