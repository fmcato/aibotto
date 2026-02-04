# Testing Guidance - AIBOTTO

## Overview
Testing guidance for the AIBOTTO project, including test infrastructure and best practices.

## Test Infrastructure

### E2E Test Infrastructure
- **Temporary SQLite database setup** for each e2e test
- **Configurable LLM client** with real API communication patterns
- **Test-specific API keys and endpoints** configuration
- **Proper test data seeding and cleanup** in fixtures

**Key Files**:
- `tests/conftest.py` - Comprehensive fixtures for real infrastructure
- `tests/e2e/` - End-to-end tests with real infrastructure

### Database Testing
- **Temporary database fixtures** that create real SQLite files
- **Proper database lifecycle management** (create, use, destroy)
- **Tests for database operations** and error conditions

### LLM Integration Testing
- **Configurable LLM test client** (`TestLLMClient`)
- **Test-specific API key and endpoint** configuration
- **API timeout and error testing** capabilities
- **Tool calling with real API response patterns**

### Test Configuration Management
- **Test configuration management system** in fixtures
- **Test environment variable setup** in `e2e_test_config` fixture
- **Centralized test fixtures and constants** in `conftest.py`

**Available Fixtures**:
- `e2e_test_config` - E2E specific configuration
- `conversation_data` - Sample conversation data
- `tool_calling_data` - Tool calling test data
- `security_test_data` - Security test scenarios

### CLI Command Execution Testing
- **CLI executor test integration** with real executor
- **Real command execution** in safe environment
- **Security blocking mechanisms** verification with real commands

## Test Organization

### Test Structure
```
tests/
├── conftest.py                    # Comprehensive fixtures
├── unit/                          # Unit tests (isolated components)
│   ├── test_cli.py               # CLI module tests
│   ├── test_config.py            # Config module tests
│   ├── test_db.py                # Database module tests
│   ├── test_factual_responses.py  # Factual response system tests
│   └── test_safe_commands.py     # Security validation tests
├── e2e/                          # End-to-end tests with real infrastructure
│   ├── test_basic_tool_interactions.py
│   ├── test_complete_flow.py
│   ├── test_security_fix.py
│   ├── test_tool_calling_visibility.py
│   └── test_parallel_tool_calls.py
└── fixtures/                      # Test fixtures and data
```

### Test Patterns and Conventions
- **Standardized test fixtures** across all files
- **Consistent test naming conventions** maintained
- **Comprehensive error scenario testing**
- **Proper async test handling**

## Testing Best Practices

### Test Categories
- **Unit Tests**: Individual component testing with isolation
- **Integration Tests**: Cross-module interaction testing
- **E2E Tests**: Full workflow testing with real infrastructure
- **Security Tests**: Command validation and blocking
- **API Tests**: OpenAI integration testing

### Testing Principles
1. **Test-Driven Development**: Write tests before implementation
2. **Real Infrastructure**: Use real databases, LLM clients, and CLI execution
3. **Comprehensive Coverage**: Ensure adequate test coverage
4. **Error Scenarios**: Test both happy paths and error conditions

### Quality Assurance Metrics
- **Test Pass Rate**: 100% (45/45 tests)
- **Code Coverage**: 71% with good coverage of core functionality
- **Production-Ready Infrastructure**: Ready for real-world testing

## Running Tests

### Basic Test Execution
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test category
uv run pytest tests/unit/
uv run pytest tests/e2e/

# Run with verbose output
uv run pytest -v
```

### Test Configuration
- **Test Environment**: Uses temporary databases and mock LLM clients
- **Real Infrastructure**: E2E tests use real CLI execution and database operations
- **Safe Command Execution**: All tests use safe, read-only commands

## Dependencies and Tools
- **pytest**: Test framework with async support
- **pytest-asyncio**: Async test support
- **tempfile**: Temporary database management
- **unittest.mock**: Selective mocking
- **Custom fixtures**: Real infrastructure setup in conftest.py