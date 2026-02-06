#!/bin/bash

# Setup Git hooks for AIBOTTO project
# This script installs the pre-commit hook

set -e

echo "🔧 Setting up Git hooks for AIBOTTO..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

# Create .git/hooks directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/.git/hooks"

# Copy the pre-commit hook
HOOK_SOURCE="$PROJECT_ROOT/.githooks/pre-commit"
HOOK_DEST="$PROJECT_ROOT/.git/hooks/pre-commit"

if [ -f "$HOOK_SOURCE" ]; then
    cp "$HOOK_SOURCE" "$HOOK_DEST"
    chmod +x "$HOOK_DEST"
    echo "✅ Pre-commit hook installed successfully!"
    echo ""
    echo "The hook will now run automatically before every commit."
    echo "It will execute quality checks including:"
    echo "  - Ruff linting"
    echo "  - MyPy type checking"
    echo "  - Bandit security scanning"
    echo "  - Pytest test suite"
    echo "  - Sensitive information detection"
    echo ""
    echo "To test the hook, try staging some changes and committing:"
    echo "  git add some-file"
    echo "  git commit -m 'test commit'"
else
    echo "❌ Hook source not found at $HOOK_SOURCE"
    exit 1
fi

echo ""
echo "🎉 Git hooks setup complete!"