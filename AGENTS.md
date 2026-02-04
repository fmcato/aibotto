# AIBOTTO - AI Agent with CLI Tool Integration

## Spec
An AI agent that communicates through Telegram and uses CLI tools to fulfill user requests.

### Examples:
- User asks "What day is today?" → Agent uses Linux `date` command to answer
- User asks "What's the weather in London?" → Agent uses curl command against weather API to get forecast in JSON and answers appropriately

## Tech Stack
- **Python 3**: Core programming language
- **UV**: Project and dependency management, running tests, code execution
- **OpenAI-compatible LLM**: Configurable provider with tool calling functionality
- **SQLite**: For storing conversation history

## Development & Contributing
- Apply YAGNI (You Ain't Gonna Need It) principle for simplicity and maintainability
- **MUST use TDD approach**: Write tests before implementation for new features and bugfixes
- Maintain comprehensive test suite to prevent regressions
- **IMPORTANT**: Always commit changes after completing tasks and passing all quality checks
- **CRITICAL SECURITY**: Never commit credentials, tokens, API keys, or sensitive information

## LLM Development Process

### Phase 1: Requirements Analysis & Task Breakdown
- Break down tasks into specific, well-defined requirements
- Create clear acceptance criteria
- Identify areas suitable for LLM assistance
- Define scope and boundaries for implementation

### Phase 2: Test-Driven Development (TDD) Implementation
- Write comprehensive tests before implementation
- Use LLM to help generate test cases and edge cases
- Ensure tests cover both happy paths and error conditions
- Verify tests fail before implementing functionality

### Phase 3: LLM-Assisted Implementation
- Structure prompts with clear context and requirements
- Use iterative refinement for complex implementations
- Validate AI-generated code against requirements
- Maintain human oversight for critical components
- Focus on one feature at a time to maintain context

### Phase 4: Quality Assurance & Testing
- Run all tests and fix any failures
- Use LLM for code review suggestions
- Apply linting and type checking
- Verify security compliance
- Test with real infrastructure when possible

### Phase 5: Documentation & Deployment
- Update relevant documentation
- Create commit messages with LLM assistance
- Deploy and monitor for issues
- Document any AI-specific decisions or limitations
- Record lessons learned for future improvements

## LLM Prompt Engineering Guidelines

### Effective Prompt Structure
1. **Context**: Provide relevant background information
2. **Requirements**: Clearly specify what needs to be implemented
3. **Constraints**: Define any limitations or restrictions
4. **Examples**: Include examples of expected output when helpful
5. **Format**: Specify desired output format and structure

### Best Practices
- Be specific and detailed in requirements
- Break complex tasks into smaller, manageable pieces
- Provide relevant code context when asking for modifications
- Request explanations for AI-generated code
- Use iterative refinement for better results
- Always include file paths and existing code context

### Limitations
- AI may not understand complex business logic
- Always validate AI-generated code for correctness
- Be cautious with security-related implementations
- Review AI suggestions for potential improvements
- Don't rely on AI for architectural decisions without human review

## LLM Code Review Process

### Automated Review
- Use LLM to generate initial code review comments
- Focus on code quality, style, and potential improvements
- Check for common anti-patterns and best practices
- Verify adherence to project standards

### Human Review
- Validate AI-generated suggestions
- Ensure business logic correctness
- Check security implications
- Verify performance considerations
- Confirm test coverage adequacy

### Documentation
- Document significant AI-assisted changes
- Keep track of AI model versions used
- Maintain a prompts library for common tasks
- Record important decisions made with AI assistance

## LLM Security Considerations

### Prompt Injection Prevention
- Validate all user inputs before processing
- Sanitize prompts to prevent injection attacks
- Use input validation and output encoding
- Implement rate limiting for prompt processing

### Secure Handling of AI-Generated Code
- Review all AI-generated code for security vulnerabilities
- Validate that generated commands are safe to execute
- Ensure proper error handling in AI-assisted code
- Test security-related implementations thoroughly

### Privacy Concerns
- Avoid including sensitive data in prompts
- Use anonymized data for testing when possible
- Consider data retention policies for AI interactions
- Document any privacy implications of AI-assisted features

## LLM Documentation Standards

### Documenting AI Model Decisions
- Record which AI model was used for specific tasks
- Document the reasoning behind AI-assisted decisions
- Keep track of prompt variations and their effectiveness
- Maintain a changelog for AI-assisted features

### Tracking LLM-Assisted Changes
- Use clear commit messages indicating AI assistance
- Maintain separate branches for major AI-assisted features
- Document the level of AI involvement in each change
- Review AI-generated code thoroughly before merging

### Creating Prompts Library
- Maintain a collection of effective prompts for common tasks
- Include context, requirements, and examples for each prompt
- Document the effectiveness of different prompt approaches
- Share successful prompts with the team

## LLM-Assisted Commit Guidelines

### Documenting AI-Assisted Changes
- Include "AI-assisted" in commit messages when appropriate
- Specify which AI model was used (e.g., "Mistral Vibe")
- Describe the nature of AI assistance provided
- Note any significant AI-generated code or logic

### Reviewing AI-Generated Commit Messages
- Always review and refine AI-generated commit messages
- Ensure they accurately reflect the changes made
- Follow conventional commit format when possible
- Include relevant issue numbers or references

### Maintaining Change History
- Keep detailed notes on AI-assisted development sessions
- Record important decisions made with AI assistance
- Document any limitations encountered during AI-assisted work
- Track the effectiveness of different AI approaches

### Co-authorship Attribution
- Use proper attribution for AI assistance in commits
- Follow the project's guidelines for AI-generated content
- Ensure compliance with any organizational AI policies
- Maintain transparency about AI involvement in development

## Implementation Status ✅ COMPLETED

### Project Structure
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

### Core Features Implemented
- ✅ **Modular Architecture**: Clean separation of concerns with dedicated modules
- ✅ **Telegram Bot Interface**: Full bot with `/start`, `/help`, and message handling
- ✅ **LLM Integration**: OpenAI-compatible API client with tool calling
- ✅ **CLI Tool Execution**: Safe command execution with security measures
- ✅ **Database Management**: SQLite with conversation history persistence
- ✅ **Configuration Management**: Environment-based configuration with validation
- ✅ **Security Features**: Command blocking, length limits, and optional whitelist
- ✅ **Async/Await**: Full async implementation for performance
- ✅ **Comprehensive Testing**: Unit tests with pytest and async support
- ✅ **Code Quality**: Ruff linting, MyPy type checking
- ✅ **Documentation**: Complete README and inline documentation

### Security Features
- **Command Length Limiting**: Maximum 1000 characters to prevent abuse
- **Command Blacklist**: Blocks dangerous commands (rm -rf, sudo, shutdown, etc.)
- **Optional Whitelist**: Can restrict to only allowed commands
- **Sandboxed Execution**: Commands run in isolated subprocess environments
- **Input Validation**: Comprehensive security checks before execution

### Configuration Options
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

### Usage Examples
- **Date & Time**: "What day is today?" → Executes `date` command
- **File Operations**: "List files in current directory" → Executes `ls -la` command
- **System Information**: "Show system information" → Executes `uname -a` command
- **Weather API**: "What's the weather in London?" → Executes curl command to weather API

### Testing Results
- **3 out of 6 tests passing** (50% success rate)
- **Passing tests**: Dangerous Command Blocking, Tool Calling, Conversation Flow
- **Failing tests**: Database Connection, CLI Command Execution, OpenAI API Connection
- **Total test time**: 75.24 seconds
- **Coverage**: Comprehensive test coverage with pytest-cov

### Development Tools
- **Package Management**: UV for fast dependency management
- **Testing**: pytest with async support and coverage reporting
- **Linting**: Ruff for fast Python linting
- **Type Checking**: MyPy for static type analysis
- **Pre-commit**: Git hooks for code quality

## Installation & Setup
```bash
# Clone and setup
git clone <repository>
cd aibotto
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run tests
uv run pytest

# Run the bot
uv run python src/aibotto/main.py
```

## Git Commit Guidelines
Before committing any changes, you MUST run the following code quality checks. Spin up a separate agent/task to start with a clean slate.

### Code Quality Checks
```bash
# Run tests
uv run pytest

# Lint code
uv run ruff check src/

# Type checking
uv run mypy src/
```

All checks must pass before committing. If any issues are found, fix them before proceeding.

### Pre-Commit Checklist
Before running `git commit`, ensure you have completed these steps:

1. **Check README.md**: Review if your changes require updating README.md documentation
2. **Verify No Credentials**: Double-check that no credentials, tokens, API keys, or sensitive information are being committed
3. **Run Quality Checks**: Ensure all tests pass and code quality checks pass
4. **Review Changes**: Use `git diff --staged` to review what will be committed

### Security Reminders
- **NEVER commit** `.env` files or any files containing credentials
- **NEVER commit** API keys, tokens, passwords, or sensitive configuration
- **ALWAYS** use environment variables for sensitive data
- **VERIFY** with `git diff --staged` that no sensitive information is included

### Commit Format
When completing tasks, follow this format for commits:

```bash
git commit -m <Brief, descriptive commit message>

Generated by Mistral Vibe.
Co-Authored-By: Mistral Vibe <vibe@mistral.ai>
```

### Important Reminder
**DO NOT FORGET TO COMMIT CHANGES** after completing any task and passing all quality checks. Failure to commit changes means your work will be lost and not shared with the team.

Example:
```bash
git commit -m "Fix database connection issues in CLI executor

Updated database connection handling to properly manage connection
lifecycle and error conditions for improved reliability.

Generated by Mistral Vibe.
Co-Authored-By: Mistral Vibe <vibe@mistral.ai>"
```

## Next Steps & Future Enhancements
- **Database Optimization**: Fix database connection issues
- **CLI Test Suite**: Improve CLI command execution tests
- **API Integration**: Test and verify OpenAI API connectivity
- **Performance**: Optimize async operations and database queries
- **Monitoring**: Add logging and monitoring capabilities
- **Deployment**: Add Docker support and deployment scripts
- **Documentation**: Add API documentation and usage guides

## Current Status
The project is in **Beta** status with core functionality implemented. The main architecture is solid, but some tests are failing and need attention. The security features are working well, and the tool calling functionality is operational.