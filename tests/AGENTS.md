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
│   ├── test_bot.py               # Telegram bot tests
│   ├── test_clear_command.py     # /clear command tests
│   ├── test_cli.py               # CLI executor tests
│   ├── test_config.py            # Config module tests
│   ├── test_db.py                # Database module tests
│   ├── test_factual_responses.py # Factual response system tests
│   ├── test_llm_client.py        # LLM client tests
│   ├── test_main.py              # Main entry point tests
│   ├── test_message_splitter.py  # Message splitting tests
│   ├── test_prompt_cli.py        # CLI prompt interface tests
│   ├── test_safe_commands.py     # Security validation tests
│   ├── test_tool_calling_edge_cases.py  # Tool calling edge cases
│   └── test_web_search.py        # Web search unit tests
├── e2e/                          # End-to-end tests with real infrastructure
│   ├── test_basic_tool_interactions.py
│   ├── test_complete_flow.py
│   ├── test_parallel_tool_calls.py
│   ├── test_tool_calling_visibility.py
│   └── test_web_search_real.py  # Real web search tests
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
- **Test Pass Rate**: 100% (121 tests)
- **Code Coverage**: 83% with good coverage of core functionality
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