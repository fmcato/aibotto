#!/bin/bash

# Pre-commit Quality Checks Script
# Run this before committing to ensure code quality

set -e

echo "🔍 Running pre-commit quality checks..."

# Function to print colored output
print_success() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[0;31m❌ $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

print_info() {
    echo -e "\033[0;34mℹ️  $1\033[0m"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Check if there are staged changes to commit
if ! git diff --cached --quiet; then
    print_info "Found staged changes, running quality checks..."
else
    print_warning "No staged changes found. Stage your changes first with 'git add'."
    exit 1
fi

# Run Ruff linting
print_info "Running Ruff linting..."
if uv run ruff check src/; then
    print_success "Ruff linting passed"
else
    print_error "Ruff linting failed. Please fix the issues above."
    exit 1
fi

# Run MyPy type checking
print_info "Running MyPy type checking..."
if uv run mypy src/; then
    print_success "MyPy type checking passed"
else
    print_error "MyPy type checking failed. Please fix the type errors above."
    exit 1
fi

# Run Bandit security scanning
print_info "Running Bandit security scanning..."
if uv run bandit -r src/ -f json -o bandit-report.json; then
    print_success "Bandit security scanning passed"
else
    print_warning "Bandit found security issues. Check bandit-report.json for details."
    # Continue with other checks but warn about security issues
fi

# Run pytest
print_info "Running pytest..."
if uv run pytest --tb=short; then
    print_success "All tests passed"
else
    print_error "Tests failed. Please fix the failing tests before committing."
    exit 1
fi

# Check for sensitive information in staged changes
print_info "Checking for sensitive information in staged changes..."
if git diff --cached --name-only | grep -E '\.(py|md|yml|yaml|sh|toml)$' | xargs grep -l -i 'password\|secret\|token\|key' | grep -v '__pycache__' | grep -v '.venv'; then
    print_warning "Potential sensitive information found in staged files:"
    git diff --cached --name-only | grep -E '\.(py|md|yml|yaml|sh|toml)$' | xargs grep -l -i 'password\|secret\|token\|key' | grep -v '__pycache__' | grep -v '.venv' | while read file; do
        echo "  - $file"
    done
    print_error "Please review and remove any sensitive information before committing."
    exit 1
else
    print_success "No sensitive information found in staged changes"
fi

# Check for TODO comments in production code
print_info "Checking for TODO comments in production code..."
if git diff --cached --name-only | grep -E '\.py$' | xargs grep -n 'TODO\|FIXME\|HACK' | grep -v '__pycache__' | grep -v '.venv'; then
    print_warning "TODO/FIXME/HACK comments found in production code:"
    git diff --cached --name-only | grep -E '\.py$' | xargs grep -n 'TODO\|FIXME\|HACK' | grep -v '__pycache__' | grep -v '.venv'
    print_error "Please address TODO comments before committing or remove them if they're intentional."
    exit 1
else
    print_success "No TODO comments found in production code"
fi

print_success "🎉 All quality checks passed! You're ready to commit."
echo ""
echo "Next steps:"
echo "  1. Review your changes: git diff --cached"
echo "  2. Commit your changes: git commit -m 'your commit message'"