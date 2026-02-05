# AIBot - AI Telegram Bot with CLI Integration

A Python-based AI bot that communicates through Telegram and uses CLI tools to fulfill user requests.

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

### 5. Docker Deployment (Alternative)

For production deployment, you can use Docker:

```bash
# Build and run with Docker Compose
docker-compose build
docker-compose up -d

# Or run directly with Docker
docker build -t aibot .
docker run -d --env-file .env -v aibot_data:/app/data aibot
```

See [README-Docker.md](README-Docker.md) for detailed Docker deployment instructions.

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

## 🔒 Security Features

- **Command Length Limit**: Prevents excessively long commands
- **Command Blacklist**: Blocks dangerous commands like `rm -rf`, `sudo`, etc.
- **Command Whitelist**: Optional whitelist mode for restricted environments
- **Sandbox Execution**: Commands run in isolated subprocess environments

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

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [python-telegram-bot](https://python-telegram-bot.org/) for the excellent Telegram framework
- [OpenAI](https://openai.com/) for the powerful AI models
- [UV](https://docs.astral.sh/uv/) for fast Python package management