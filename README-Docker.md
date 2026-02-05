# Docker Deployment

This guide explains how to deploy AIBot using Docker.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Telegram Bot Token
- OpenAI API Key

### 1. Environment Setup

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
# ALLOWED_COMMANDS=date,ls,pwd,whoami,uname,df,free,ps,curl
BLOCKED_COMMANDS="rm -rf,sudo,dd,mkfs,fdisk,format,shutdown,reboot,poweroff,halt"

# Bot Configuration
MAX_HISTORY_LENGTH=20
THINKING_MESSAGE="🤔 Thinking..."
```

### 2. Build and Run

Using Docker Compose (recommended):

```bash
# Build the image
docker-compose build

# Start the bot
docker-compose up -d
```

Using Docker directly:

```bash
# Build the image
docker build -t aibot .

# Run the container
docker run -d \
  --name aibot \
  --env-file .env \
  -v aibot_data:/app/data \
  aibot
```

### 3. Check Status

```bash
# View logs
docker-compose logs -f

# Check container status
docker-compose ps

# Check health status
docker inspect aibot --format='{{.State.Health.Status}}'
```

## Development Workflow

### Running Tests in Docker

```bash
# Run all tests
docker-compose run --rm aibot test

# Run specific test file
docker-compose run --rm aibot uv run pytest tests/unit/test_message_splitter.py -v

# Run with coverage
docker-compose run --rm aibot uv run pytest tests/ --cov=src
```

### Code Quality Checks

```bash
# Linting
docker-compose run --rm aibot lint

# Type checking
docker-compose run --rm aibot type-check

# All checks
docker-compose run --rm aibot lint && docker-compose run --rm aibot type-check
```

### Interactive Development

```bash
# Run a shell in the container
docker-compose run --rm aibot bash

# Run a specific command
docker-compose run --rm aibot uv run python src/aibotto/main.py
```

## Configuration

### Environment Variables

All configuration is done through environment variables. See `.env.example` for all available options.

### Volume Mounting

The Docker setup uses a named volume to persist database data:

```yaml
volumes:
  - aibot_data:/app/data
```

You can also mount a local directory for development:

```bash
docker run -d \
  --name aibot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd):/app \
  aibot
```

### Resource Limits

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

## Production Deployment

### Security Considerations

1. **Use secrets management**: Store sensitive data in Docker secrets or a secrets manager
2. **Network isolation**: Run in a private network with limited exposure
3. **Resource limits**: Keep the resource limits appropriate for your deployment
4. **Health checks**: The container includes health checks for monitoring

### Monitoring

```bash
# View real-time logs
docker-compose logs -f

# Check container health
docker-compose ps

# View resource usage
docker stats aibot
```

### Updating

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup

```bash
# Backup database
docker run --rm \
  -v aibot_data:/app/data \
  -v $(pwd)/backup:/backup \
  alpine \
  tar czf /backup/conversations-$(date +%Y%m%d).tar.gz -C /app data/
```

## Troubleshooting

### Common Issues

1. **Container fails to start**:
   ```bash
   docker-compose logs aibot
   ```

2. **Database connection issues**:
   - Check volume permissions
   - Ensure the data directory exists

3. **Environment variables not set**:
   - Verify `.env` file exists and has correct permissions
   - Check variable names match exactly

### Debug Mode

Run the container in interactive mode for debugging:

```bash
docker-compose run --rm aibot bash
```

### Health Check Failures

If the health check fails:
```bash
# Check health status
docker inspect aibot --format='{{.State.Health}}'

# Run health check manually
docker exec aibot python -c "import sys; sys.exit(0)"
```

## Advanced Usage

### Multi-Stage Builds

The Dockerfile uses multi-stage builds to create a smaller, more secure final image.

### Custom Dockerfile

You can customize the Dockerfile for specific needs:
```dockerfile
# Add custom dependencies
RUN apt-get update && apt-get install -y \
    custom-package \
    && rm -rf /var/lib/apt/lists/*

# Add custom entrypoint
COPY custom-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

### Kubernetes Deployment

For Kubernetes deployment, you can adapt the Docker Compose configuration to Kubernetes manifests.