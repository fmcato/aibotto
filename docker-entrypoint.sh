#!/bin/bash

# Docker entrypoint script for AIBOTTO

# Set default values for environment variables if not set
export TELEGRAM_TOKEN=${TELEGRAM_TOKEN:-""}
export OPENAI_API_KEY=${OPENAI_API_KEY:-""}
export OPENAI_BASE_URL=${OPENAI_BASE_URL:-"https://api.openai.com/v1"}
export OPENAI_MODEL=${OPENAI_MODEL:-"gpt-3.5-turbo"}
export DATABASE_PATH=${DATABASE_PATH:-"/app/data/conversations.db"}
export MAX_COMMAND_LENGTH=${MAX_COMMAND_LENGTH:-"1000"}
export BLOCKED_COMMANDS=${BLOCKED_COMMANDS:-"rm -rf,sudo,dd,mkfs,fdisk,format,shutdown,reboot,poweroff,halt"}
export MAX_HISTORY_LENGTH=${MAX_HISTORY_LENGTH:-"20"}
export THINKING_MESSAGE=${THINKING_MESSAGE:-"🤔 Thinking..."}

# Create data directory if it doesn't exist
mkdir -p "$(dirname "$DATABASE_PATH")"

# Validate required environment variables
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "❌ ERROR: TELEGRAM_TOKEN is required"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY is required"
    exit 1
fi



# Default: run the bot
echo "🚀 Starting AIBOTTO..."
echo "📊 Configuration:"
echo "   - Telegram Token: ${TELEGRAM_TOKEN:0:10}..."
echo "   - OpenAI Base URL: $OPENAI_BASE_URL"
echo "   - OpenAI Model: $OPENAI_MODEL"
echo "   - Database Path: $DATABASE_PATH"
echo "   - Max Command Length: $MAX_COMMAND_LENGTH"
echo "   - Max History Length: $MAX_HISTORY_LENGTH"

# Set PYTHONPATH for the bot
export PYTHONPATH=/app/src

exec uv run python src/aibotto/main.py