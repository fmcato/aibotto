"""
Prompt templates for the AI system.
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


# Reusable tool description components
_TOOL_CATEGORIES = """
1. CLI commands for system information:
   - Use for date/time, system info, file operations, calculations
   - Examples: date, uname -a, ls -la, python3 -c "print(2**10)"

2. Web research for discovering new information:
   - Use a specialized subagent to comprehensively research topics
   - Finds multiple sources, evaluates credibility, synthesizes findings
   - Returns summary with inline citations [Title](URL)
   - Examples: "AI developments", "climate change impacts"

3. Web fetch for specific URLs:
   - Use when you have a specific URL and want to read its full content
   - Extracts readable text from web pages (not HTML code)
   - Useful for reading articles, blog posts, documentation pages

4. Python script execution for code-based solutions:
   - Use a specialized subagent to create and execute Python scripts
   - Creates Python code to accomplish complex tasks
   - Executes with 45-second timeout, unlimited script size
   - Returns natural language results with execution output
   - Examples: "Calculate statistics", "Process data", "Generate reports"

5. Task delegation to subagents:
   - Use delegate_task tool for complex tasks requiring specialized subagents
   - Specificially indicate which subagent: web_research or python_script
   - More flexible than specific tools, subagent can be chosen dynamically
"""

_PYTHON3_LIMITATIONS = """
**Programming Language Access:**
You ONLY have access to Python 3 interpreter. You cannot execute code in
other programming languages like JavaScript, Ruby, Java, C++, etc.

**Python Code Execution Options:**
1. **Simple one-liners** (use CLI tool):
   - python3 -c "print('Hello World')"
   - python3 -c "import datetime; print(datetime.datetime.now())"
   - python3 -c "2**10"  # For simple calculations

2. **Complex Python scripts** (use Python script subagent via delegate_task):
   - Multi-line code, functions, classes
   - Code that needs debugging or iteration
   - Tasks requiring file I/O, data processing
   - Use `delegate_task` with subagent_name="python_script" for these cases
"""

_BEHAVIORAL_RULES = """
**CRITICAL BEHAVIOR RULES:**
- Execute each tool ONCE and provide the best answer you can
- NEVER retry the same tool with the same parameters to "verify" or "get more details"
- If results are incomplete, try a DIFFERENT tool or approach
- Complex calculations should be executed once, not multiple times
- Web searches should be done once per topic, not repeated
- Finalize your answer after getting results, don't keep looking for "better" ones
"""

_DETAILED_TOOL_EXAMPLES = """
- **Simple Python 3 Execution**: For one-line calculations and simple operations:
  * python3 -c "import math; print(math.sqrt(16))"
  * python3 -c "import datetime; print(datetime.datetime.now())"
  * python3 -c "[x*2 for x in range(5)]"  # Simple list comprehension

- **Complex Python Scripts**: For multi-line code, debugging, or complex tasks:
  * Use `delegate_task` with subagent_name="python_script" and a task description
  * The Python script subagent will create, execute, and debug the code
  * Maximum 45-second execution time, unlimited script size
  * Subagent has multiple iterations to fix problems

- **LIMITATION**: You ONLY have access to Python 3. No other languages
  like JavaScript, Java, C++, Ruby, etc. are available.
"""

def _get_temporal_resolution_guidelines() -> str:
    """Generate temporal resolution guidelines with current year."""
    current_year = datetime.now(UTC).year
    return f"""
**TEMPORAL REFERENCE RESOLUTION - CRITICAL:**
The system provides the current date and time. You MUST resolve temporal references
using this context before responding or delegating tasks:

Common references to resolve (extract from provided datetime context):
- "this year" → the year from datetime context (e.g., if context is {current_year}-07-15, use "{current_year}")
- "this month" → month and year from context (e.g., if context is {current_year}-07-15, use "July {current_year}")
- "this week" → current week within current year (e.g., "week of July 14, {current_year}")
- "last week", "last month", "last year" → calculate relative to context date
- "next week", "next month", "next year" → calculate relative to context date

Do NOT use training data or outdated years. Always use the provided datetime context.
"""

_SOURCE_CREDIBILITY_GUIDELINES = """
**Source Credibility Guidelines for Web Content:**

When using web search or fetch, ALWAYS evaluate source credibility:

1. **High-Credibility Sources** (prioritize these):
   - Educational domains (.edu, university websites)
   - Government domains (.gov, .gov.uk, .eu, etc.)
   - Established news organizations with editorial standards
   - Peer-reviewed scientific publications
   - Official documentation from software/hardware vendors

2. **Medium-Credibility Sources** (use with caution):
   - .org domains (verify organization's reputation)
   - Reputable tech publications and documentation
   - Community-maintained knowledge bases (e.g., Stack Overflow for validated answers)

3. **Low-Credibility Sources** (avoid or verify with multiple sources):
   - Personal blogs without proven expertise
   - Unknown or recently created domains
   - Content farms or heavily AI-generated sites

4. **Red Flags for AI-Generated or Low-Quality Content**:
   - Generic, vague language with no specific details
   - Contradictory statements within the same article
   - No author attribution or publication date
   - Excessive repetition or filler text
   - Claims without supporting evidence or citations
   - Grammar that is too perfect but lacks substance
   - Topic coverage that seems too broad/shallow

5. **Cross-Checking Requirements**:
   - For sensitive topics (health, finance, safety): verify with multiple HIGH-credibility sources
   - If sources contradict each other: cite the disagreement and explain the more credible source
   - For breaking news: check multiple reputable outlets before presenting as fact
   - Never present a single low-credibility source as definitive

6. **Reporting to Users**:
   - If information comes from a questionable source, explicitly mention this limitation
   - When uncertain about accuracy, acknowledge it and suggest verifying from authoritative sources
   - Prefer providing partial but reliable information over complete but unreliable information
"""


class DateTimeContext:
    """Provides current date/time context for the LLM."""

    @classmethod
    def get_current_datetime_message(cls) -> dict[str, str]:
        """Get a system message with the current date and time.

        Returns:
            A system message dict with current date/time in ISO format.
        """
        now = datetime.now(UTC)
        iso_format = now.isoformat()
        day_name = now.strftime("%A")

        return {
            "role": "system",
            "content": f"Current date and time: {iso_format} ({day_name}, UTC)"
        }


class SystemPrompts:
    """System prompts for the AI assistant."""

    MAIN_SYSTEM_PROMPT = f"""You are a helpful AI assistant that can use CLI tools
    and web tools to get factual information.

    When users ask for factual information like date/time, weather, system info,
    news, or web content, use the available tools to get accurate information.

    You have these tools available:
    1. CLI commands for system information (date, weather, files, etc.)
    2. Web research for discovering and synthesizing information from web sources
    3. Web fetch for reading the full content of a specific URL
    4. Python script execution for creating and running Python code to solve problems
    {_get_temporal_resolution_guidelines()}
    {_BEHAVIORAL_RULES}
    {_PYTHON3_LIMITATIONS}
    {_SOURCE_CREDIBILITY_GUIDELINES}
    Provide a helpful response based on the actual information you received.
    Don\'t mention the tool commands or technical details."""

    @classmethod
    def get_tool_instructions(cls, max_turns: int = 10) -> str:
        """Get tool instructions with dynamic turn limit.

        Args:
            max_turns: Maximum number of tool-calling turns allowed

        Returns:
            Tool instructions string with turn limit
        """
        return f"""You have these tools available:
{_TOOL_CATEGORIES}
{_DETAILED_TOOL_EXAMPLES}

    IMPORTANT GUIDELINES:
    - **CRITICAL**: Do NOT call the same tool with the same parameters multiple times
    - **CRITICAL**: Do NOT fetch the same URL more than once
    - **Use delegate_task**: For complex research (web_research) or Python tasks (python_script)
    - **Use search_web**: For quick web searches without needing synthesis
    - **Use fetch_webpage**: For URLs the user provides or you already have
    - If a tool result is not useful, try a DIFFERENT approach instead of repeating
    - **For calculations**: Once you get a result, provide your answer. Don't retry to "verify" or get "more details"
    - **For complex operations**: Execute once and provide the best answer you can
    - **For CLI commands**: Execute once and move on. Don't repeat the same command
    - Provide your best answer based on available information, even if incomplete

    You have a maximum of {max_turns} tool-calling turns to complete your
    task. Use them wisely - each turn should provide new information, not
    repeat the same work."""

    FALLBACK_RESPONSE = f"""I don't have access to the specific tools needed
    for this request.

    I can help with:
    - Date and time queries
    - Weather information
    - System information
    - File and directory operations
    - Python 3 code execution and calculations
    - Python script creation and execution (complex tasks)
    - Web content retrieval
    - News and information gathering
{_PYTHON3_LIMITATIONS}"""

    @classmethod
    def get_base_prompt(cls, max_turns: int = 10) -> list[dict[str, str]]:
        """Get the base system prompt without conversation history.

        Args:
            max_turns: Maximum number of tool-calling turns allowed

        Returns:
            List of system message dicts
        """
        return [
            {"role": "system", "content": cls.MAIN_SYSTEM_PROMPT},
            {"role": "system", "content": cls.get_tool_instructions(max_turns)},
            DateTimeContext.get_current_datetime_message(),
        ]

    @classmethod
    def get_conversation_prompt(
        cls, conversation_history: list[dict[str, str]], max_turns: int = 10
    ) -> list[dict[str, str]]:
        """Get the complete conversation prompt with system message.

        Args:
            conversation_history: List of previous conversation messages
            max_turns: Maximum number of tool-calling turns allowed

        Returns:
            List of message dicts including system prompt and history
        """
        messages = cls.get_base_prompt(max_turns)

        if conversation_history:
            messages.extend(conversation_history)

        return messages


class ToolDescriptions:
    """Tool descriptions for the LLM."""

    CLI_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "execute_cli_command",
            "description": (
                "Execute safe CLI commands to get factual information. "
                "Supports system commands and simple Python 3 code execution. "
                "For simple Python one-liners: use python3 -c 'your_code_here'. "
                "For complex Python scripts, use delegate_task tool instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "The CLI command to execute. For simple Python 3 code, use: "
                            "python3 -c 'your_code_here'. For complex Python scripts, "
                            "use delegate_task tool instead. Available: system "
                            "commands (date, ls, etc.) and Python 3 interpreter only."
                        ),
                    }
                },
                "required": ["command"],
            },
        },
    }

    WEB_SEARCH_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the web for current information using DuckDuckGo. "
                "Results may vary in reliability - always evaluate source credibility "
                "and prioritize authoritative sources (.gov, .edu, established news sites). "
                "Be cautious of AI-generated content and cross-check important claims."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The search query. Use this for current information, "
                            "recent news, or topics not covered by CLI tools."
                        ),
                    },
                    "num_results": {
                        "type": "integer",
                        "description": (
                        "Maximum number of results to return "
                        "(1-10, default: 5)"
                        ),
                        "default": 5
                    },
                    "days_ago": {
                        "type": "integer",
                        "description": (
                            "Filter results from last N days (optional, "
                            "e.g., 7 for last week, 30 for last month)"
                        ),
                        "default": None
                    }
                },
                "required": ["query"],
            },
        },
    }

    WEB_FETCH_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": (
                "Fetch and extract readable text content from a specific URL. "
                "Use this when you have a URL and want to read its full content. "
                "Returns the page title, content, and metadata. "
                "Link citations are included in markdown format [text](url) by default."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The URL to fetch. Must start with http:// or https://"
                        ),
                    },
                    "max_length": {
                        "type": "integer",
                        "description": (
                            "Maximum content length to return in characters "
                            "(default: 10000)"
                        ),
                        "default": 10000,
                    },
                    "no_citations": {
                        "type": "boolean",
                        "description": (
                            "Whether to exclude link citations from the output "
                            "(default: false, includes markdown links)"
                        ),
                        "default": False,
                    },
                },
                "required": ["url"],
            },
        },
    }

    DELEGATE_TASK_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "delegate_task",
            "description": (
                "Delegate a task to a specialized subagent with isolated LLM context. "
                "Use this for complex tasks that benefit from specialized processing and iteration. "
                "Available subagents: "
                "- web_research: Comprehensive web search with source evaluation, multi-source synthesis, and inline citations [Title](URL) "
                "- python_script: Create and execute Python code with 45-second timeout, unlimited script size, and multi-iteration debugging"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subagent_name": {
                        "type": "string",
                        "description": (
                            "Name of the subagent to use: 'web_research' or 'python_script'"
                        ),
                    },
                    "task_description": {
                        "type": "string",
                        "description": (
                            "Description of the task to accomplish. "
                            "Be specific about requirements and desired outputs."
                        ),
                    },
                },
                "required": ["subagent_name", "task_description"],
            },
        },
    }

    @classmethod
    def get_tool_definitions(cls) -> list[dict[str, Any]]:
        """Get all available tool definitions."""
        return [
            cls.CLI_TOOL_DESCRIPTION,
            cls.WEB_SEARCH_TOOL_DESCRIPTION,
            cls.WEB_FETCH_TOOL_DESCRIPTION,
            cls.DELEGATE_TASK_TOOL_DESCRIPTION,
        ]
