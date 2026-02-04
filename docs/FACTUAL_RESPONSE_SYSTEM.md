# Factual Response System Documentation

## Overview

The AIBot now includes an enhanced factual response system that ensures the AI provides accurate, verifiable information instead of making things up when uncertain.

## Key Improvements

### 1. Enhanced System Prompts

The system now uses comprehensive prompts that explicitly instruct the AI to:
- **ALWAYS use available tools** when factual information is needed
- **NEVER invent or hallucinate** facts, dates, times, or locations
- **Verify information** using tools before providing it
- **Clearly state** when tools are not available for specific queries

### 2. Intelligent Command Selection

The enhanced CLI executor includes:
- **Command suggestions** based on query type
- **Confidence scoring** for command appropriateness
- **Automatic command selection** for common factual queries
- **Fallback mechanisms** when tools aren't available

### 3. Uncertainty Detection

The system automatically detects when responses contain:
- Uncertain language ("probably", "maybe", "might be", "I think")
- Unsourced factual claims
- Responses to factual queries without tool usage

### 4. Automatic Fact-Checking

When uncertainty is detected, the system:
1. Identifies the type of factual query
2. Suggests appropriate commands
3. Executes commands to get factual data
4. Provides verified information to the user

## Architecture

### Components

```
src/aibotto/ai/
├── prompt_templates.py       # System prompts and templates
├── tool_calling.py           # Enhanced tool calling with fact-checking
└── llm_client.py            # LLM API client

src/aibotto/cli/
├── enhanced_executor.py     # Intelligent command selection
├── executor.py              # Basic command execution
└── security.py              # Command validation
```

### Flow

1. **User Query** → System analyzes query type
2. **System Prompts** → Enhanced prompts guide AI behavior
3. **Tool Selection** → AI chooses appropriate tools
4. **Command Execution** → Safe commands executed
5. **Fact Verification** → Response checked for uncertainty
6. **Final Response** → Verified factual information provided

## Usage Examples

### Example 1: Time Query

**User:** "What time is it?"

**Old Behavior:**
```
Bot: "It's probably around 2 PM" ❌ (guessing)
```

**New Behavior:**
```
Bot: 🤔 Thinking...
Bot: "The current time is 14:30:45 UTC on Monday, February 2, 2026" ✅ (from `date` command)
```

### Example 2: Weather Query

**User:** "What's the weather in London?"

**Old Behavior:**
```
Bot: "The weather is probably nice today" ❌ (making up)
```

**New Behavior:**
```
Bot: 🤔 Thinking...
Bot: "Weather in London: 15°C, Light clouds" ✅ (from wttr.in API)
```

### Example 3: System Information

**User:** "Tell me about this computer"

**Old Behavior:**
```
Bot: "It's probably a Linux system" ❌ (guessing)
```

**New Behavior:**
```
Bot: 🤔 Thinking...
Bot: "System: Linux ubuntu 6.14.0-generic #1 SMP x86_64 GNU/Linux" ✅ (from `uname -a`)
```

## Configuration

### System Prompt Customization

You can customize the system prompts in `src/aibotto/ai/prompt_templates.py`:

```python
class SystemPrompts:
    MAIN_SYSTEM_PROMPT = """Your custom prompt here..."""
    TOOL_INSTRUCTIONS = """Your tool instructions here..."""
```

### Command Suggestions

Add or modify command suggestions in `src/aibotto/cli/enhanced_executor.py`:

```python
def _build_command_suggestions(self):
    return {
        "your_category": [
            CommandSuggestion("your_command", 0.9, "Description"),
        ]
    }
```

## Testing

Run the factual response tests:

```bash
# Run all factual response tests
uv run pytest tests/unit/test_factual_responses.py -v

# Run specific test
uv run pytest tests/unit/test_factual_responses.py::TestFactualResponses::test_uncertainty_detection -v

# Run with coverage
uv run pytest tests/unit/test_factual_responses.py --cov=src/aibotto/ai
```

## API Reference

### ToolCallingManager

```python
async def process_user_request(user_id, chat_id, message, db_ops) -> str
    """Process user request with factual verification."""

async def get_factual_commands_info() -> str
    """Get information about available factual commands."""

async def fact_check_response(query, response) -> str
    """Fact-check a response using available tools."""

def _needs_factual_verification(response_content, original_message) -> bool
    """Check if response needs factual verification."""
```

### EnhancedCLIExecutor

```python
def suggest_command(query: str) -> Optional[CommandSuggestion]
    """Suggest the best command for a query."""

async def execute_with_suggestion(query: str) -> str
    """Execute command based on query suggestion."""

async def execute_fact_check(query: str, response: str) -> str
    """Execute commands to fact-check a response."""

async def get_available_commands_info() -> str
    """Get information about available commands."""
```

## Best Practices

### For Developers

1. **Always use tools for factual queries** - Never rely on AI knowledge for verifiable facts
2. **Add new command suggestions** - Expand the command library for better coverage
3. **Test uncertainty detection** - Ensure the system catches uncertain responses
4. **Monitor tool usage** - Track which tools are used most frequently

### For Users

1. **Ask specific questions** - "What time is it?" works better than "Tell me about time"
2. **Use factual keywords** - Include words like "current", "today", "system", "weather"
3. **Verify responses** - The bot will show which commands were executed
4. **Report issues** - If the bot makes up information, report it as a bug

## Troubleshooting

### Issue: Bot still makes up information

**Solution:** Check that:
- System prompts are properly loaded
- Tool calling is enabled
- Commands are not blocked by security

### Issue: Commands not executing

**Solution:** Verify:
- Command is in the allowed list
- Command is not in the blocked list
- Security manager is configured correctly

### Issue: Uncertainty not detected

**Solution:** Ensure:
- Uncertainty keywords are up to date
- Factual indicators are comprehensive
- Response verification logic is working

## Future Enhancements

1. **More command categories** - Add support for more types of factual queries
2. **Confidence scoring** - Show confidence levels in responses
3. **Source attribution** - Cite sources for all factual information
4. **Multi-step verification** - Verify facts from multiple sources
5. **Learning system** - Learn from user feedback on accuracy

## Contributing

To add new factual command support:

1. Add command suggestions to `enhanced_executor.py`
2. Update system prompts if needed
3. Add tests to `test_factual_responses.py`
4. Update this documentation

## License

This feature is part of the AIBot project and follows the same MIT License.