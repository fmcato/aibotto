# AIBOTTO - AI Telegram Bot with CLI Integration

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



### 5. Docker Deployment (Alternative)

For production deployment, you can use Docker:

#### Quick Start with Docker Compose (Recommended)

```bash
# Build and run with Docker Compose
docker compose build
docker compose up -d
```

#### Quick Start with Docker

```bash
# Build the image
docker build -t aibotto .

# Run the container
docker run -d \
  --name aibotto \
  --env-file .env \
  -v aibot_data:/app/data \
  aibotto
```

#### Detailed Docker Setup

##### Prerequisites
- Docker and Docker Compose installed
- Telegram Bot Token
- OpenAI API Key

##### Environment Setup

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```bash
# Telegram Bot Configuration
TELEGRAM_TOKEN=YOUR_TELEGRAM_TOKEN_HERE

# OpenAI Configuration
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# Database Configuration
DATABASE_PATH=/app/data/conversations.db

# Security Configuration
MAX_COMMAND_LENGTH=1000
# ALLOWED_COMMANDS=date,ls,pwd,whoami,uname,df,cat,head,tail,python3
BLOCKED_COMMANDS="rm -rf,sudo,dd,mkfs,fdisk,format,shutdown,reboot,poweroff,halt"

# Bot Configuration
MAX_HISTORY_LENGTH=20
THINKING_MESSAGE="🤔 Thinking..."
```

##### Configuration

###### Environment Variables

All configuration is done through environment variables. See `.env.example` for all available options.

###### Volume Mounting

The Docker setup uses a named volume to persist database data:

```yaml
volumes:
  - aibot_data:/app/data
```

You can also mount a local directory for development:

```bash
docker run -d \
  --name aibotto \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd):/app \
  aibotto
```

###### Resource Limits

The Docker Compose file includes resource limits to prevent excessive resource usage:

```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

##### Production Deployment

###### Security Considerations

1. **Use secrets management**: Store sensitive data in Docker secrets or a secrets manager
2. **Network isolation**: Run in a private network with limited exposure
3. **Resource limits**: Keep the resource limits appropriate for your deployment
4. **Health checks**: The container includes health checks for monitoring

###### Monitoring

```bash
# View real-time logs
docker compose logs -f

# Check container health
docker compose ps

# View resource usage
docker stats aibotto
```

###### Updating

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d
```

###### Backup

```bash
# Backup database
docker run --rm \
  -v aibot_data:/app/data \
  -v $(pwd)/backup:/backup \
  alpine \
  tar czf /backup/conversations-$(date +%Y%m%d).tar.gz -C /app data/
```

##### Troubleshooting

###### Common Issues

1. **Container fails to start**:
   ```bash
   docker compose logs aibotto
   ```

2. **Database connection issues**:
   - Check volume permissions
   - Ensure the data directory exists

3. **Environment variables not set**:
   - Verify `.env` file exists and has correct permissions
   - Check variable names match exactly

###### Debug Mode

Run the container in interactive mode for debugging:

```bash
docker compose run --rm aibotto bash
```

###### Health Check Failures

If the health check fails:
```bash
# Check health status
docker inspect aibotto --format='{{.State.Health}}'

# Run health check manually
docker exec aibotto python -c "import sys; sys.exit(0)"
```

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

### Web Search
```
User: "What's the weather in London?"
Bot: 🤔 Thinking...
Bot: "The current weather in London is 15°C with light clouds..."
```

### Python Calculations
```
User: "Calculate 2 to the power of 20"
Bot: 🤔 Thinking...
Bot: "2^20 = 1,048,576"
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

## 🔒 Security Features

- **Command Length Limit**: Prevents excessively long commands
- **Command Blacklist**: Blocks dangerous commands like `rm -rf`, `sudo`, etc.
- **Command Whitelist**: Optional whitelist mode for restricted environments
- **Sandbox Execution**: Commands run in isolated subprocess environments



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

This project is open source and available under the GNU General Public License v3.0.

## 🙏 Acknowledgments

- [python-telegram-bot](https://python-telegram-bot.org/) for the excellent Telegram framework
- [OpenAI](https://openai.com/) for the powerful AI models
- [UV](https://docs.astral.sh/uv/) for fast Python package management