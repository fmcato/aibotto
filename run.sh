#!/bin/bash

# AIBot Run Script
# This script starts the AIBot Telegram bot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed. Please install uv first."
    print_error "Visit https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env from .env.example"
        print_warning "Please edit .env file with your configuration before running the bot"
        exit 1
    else
        print_error "Neither .env nor .env.example found"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_status "Setting up virtual environment..."
    uv sync
    print_success "Virtual environment created"
fi

# Install dependencies if needed
print_status "Installing dependencies..."
uv sync --frozen

# Check if required environment variables are set
source .env
missing_vars=()

if [ -z "$TELEGRAM_TOKEN" ]; then
    missing_vars+=("TELEGRAM_TOKEN")
fi

if [ -z "$OPENAI_API_KEY" ]; then
    missing_vars+=("OPENAI_API_KEY")
fi

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        print_error "  - $var"
    done
    print_error "Please check your .env file"
    exit 1
fi

# Start the bot
print_status "Starting AIBot..."
print_status "Press Ctrl+C to stop the bot"

# Run the bot using uv
uv run python -m src.aibotto.main