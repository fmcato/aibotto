# AIBot - AI Telegram Bot with CLI Integration

A Python-based AI bot that communicates through Telegram and uses CLI tools to fulfill user requests.

## 🚀 Project Status

**Status**: Beta - Core functionality implemented, some tests need attention

**Test Results**: 3/6 tests passing (50% success rate)
- ✅ **Passing**: Dangerous Command Blocking, Tool Calling, Conversation Flow
- ❌ **Failing**: Database Connection, CLI Command Execution, OpenAI API Connection

## 📁 Project Structure

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

## ✨ Features

- 🤖 **Telegram Bot Interface**: Interactive bot with `/start` and `/help` commands
- 🛠️ **CLI Tool Integration**: Execute safe CLI commands through AI
- 🧠 **AI-Powered**: Uses OpenAI's GPT models with tool calling capabilities
- 💾 **Conversation History**: SQLite database for storing conversation context
- 🔒 **Security**: Built-in safety measures to prevent dangerous commands
- ⚡ **Async**: Asynchronous implementation for better performance
- 🧪 **Testing**: Comprehensive test suite with pytest and coverage
- 📝 **Code Quality**: Ruff linting, MyPy type checking

## 🛠️ Tech Stack

- **Python 3.12+**
- **python-telegram-bot**: Telegram bot framework
- **openai**: OpenAI API client
- **sqlite3**: Database for conversation history
- **uv**: Package and dependency management
- **pytest**: Testing framework
- **ruff**: Fast Python linter
- **mypy**: Static type checking

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your:
- `TELEGRAM_TOKEN` (from @BotFather)
- `OPENAI_API_KEY` (from OpenAI or compatible provider)

### 3. Run the Bot

```bash
uv run python src/aibotto/main.py
```

### 4. Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/unit/test_cli.py
```

## ⚙️ Configuration

### Environment Variables

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

### Security Features

- **Command Length Limit**: Prevents excessively long commands
- **Command Blacklist**: Blocks dangerous commands like `rm -rf`, `sudo`, etc.
- **Command Whitelist**: Optional whitelist mode for restricted environments
- **Sandbox Execution**: Commands run in isolated subprocess environments

## 💡 Usage Examples

### Date & Time
```
User: "What day is today?"
Bot: 🤔 Thinking...
Bot: "Today is Monday, February 2, 2026"
```

### File Operations
```
User: "List files in current directory"
Bot: 🤔 Thinking...
Bot: "Here are the files in the current directory:\n- main.py\n- config.py\n- README.md\n..."
```

### System Information
```
User: "Show system information"
Bot: 🤔 Thinking...
Bot: "System Information:\n- OS: Linux Ubuntu 24.04\n- Kernel: 6.14.0\n- User: ubuntu\n..."
```

### Weather (with API)
```
User: "What's the weather in London?"
Bot: 🤔 Thinking...
Bot: "The current weather in London is 15°C with light clouds..."
```

## 🧪 Testing

The project includes comprehensive tests:

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run tests with verbose output
uv run pytest -v

# Run specific test categories
uv run pytest tests/unit/
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Full bot functionality testing
- **Security Tests**: Command validation and blocking
- **API Tests**: OpenAI integration testing

## 🔧 Development

### Code Quality Tools

Before committing any changes, you MUST run the following code quality checks:

```bash
# Run tests
uv run pytest

# Lint code
uv run ruff check src/

# Type checking
uv run mypy src/
```

All checks must pass before committing. If any issues are found, fix them before proceeding.

### Git Hooks

The project includes pre-commit hooks for code quality:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run pre-commit manually
uv run pre-commit run --all-files
```

## 📊 Architecture

### Core Components

1. **AIBot Class**: Main AI logic with LLM integration
2. **TelegramBot Class**: Telegram bot interface and handlers
3. **Config Class**: Configuration management
4. **Database Operations**: Conversation history storage
5. **CLI Executor**: Safe command execution
6. **Security Manager**: Command validation and blocking

### Flow

1. User sends message to Telegram bot
2. Bot saves message to database
3. Bot calls OpenAI API with conversation context
4. LLM decides whether to use CLI tools or respond directly
5. If tools are needed, bot executes safe CLI commands
6. Bot combines results and sends response back to user

## 🐛 Troubleshooting

### Common Issues

1. **Module Not Found**: Run `uv sync` to install dependencies
2. **Telegram Token Error**: Check your `.env` file for correct token
3. **OpenAI API Error**: Verify your API key and network connection
4. **Database Error**: Ensure write permissions in the project directory
5. **Test Failures**: Check the specific test output for details

### Getting Help

- Check the [OpenAI API documentation](https://platform.openai.com/docs)
- Refer to [python-telegram-bot](https://python-telegram-bot.org/) docs
- Review test results in `test_results.json`
- Check logs in `aibotto.log`

## 📈 Performance

- **Async/Await**: Non-blocking operations for better performance
- **Database Indexing**: Optimized SQLite queries
- **Command Caching**: Avoid duplicate command execution
- **Memory Management**: Efficient conversation history management

## 🔒 Security

The bot includes multiple security layers:

1. **Input Validation**: All commands are validated before execution
2. **Command Blacklist**: Dangerous commands are blocked
3. **Length Limits**: Prevents command injection attacks
4. **Sandbox Execution**: Commands run in isolated environments
5. **Rate Limiting**: Prevents abuse (future enhancement)

## 🚀 Future Enhancements

- **Database Optimization**: Fix current database connection issues
- **CLI Test Suite**: Improve CLI command execution tests
- **API Integration**: Test and verify OpenAI API connectivity
- **Performance**: Optimize async operations and database queries
- **Monitoring**: Add logging and monitoring capabilities
- **Deployment**: Add Docker support and deployment scripts
- **Documentation**: Add API documentation and usage guides

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run quality checks: `uv run pytest && uv run ruff check src/ && uv run mypy src/`
6. **DO NOT FORGET TO COMMIT CHANGES** after completing tasks and passing all quality checks
7. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [python-telegram-bot](https://python-telegram-bot.org/) for the excellent Telegram framework
- [OpenAI](https://openai.com/) for the powerful AI models
- [UV](https://docs.astral.sh/uv/) for fast Python package management