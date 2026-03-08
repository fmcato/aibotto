"""
Prompt templates for the AI system.
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


# Reusable tool description components
_TOOL_CATEGORIES = """
1. Python code execution:
   - Use execute_python_code for mathematical computations, algorithms, and data processing
   - Supports 60KB code length for complex scripts
   - PREFER Python computation over web search for math problems
   - Examples: "Calculate nth prime", "Compute factorial", "Find GCD"
   - Just provide Python code - 'uv run python' is added automatically

2. CLI commands for system information:
   - Use execute_cli_command for date/time, system info, file operations
   - Examples: date, uname -a, ls, pwd, df
   - DEPRECATED: Do NOT use execute_cli_command for Python execution

3. Web research for discovering new information:
   - Use a specialized subagent to comprehensively research topics
   - Finds multiple sources, evaluates credibility, synthesizes findings
   - Returns summary with inline citations [Title](URL)
   - Examples: "AI developments", "climate change impacts"
   - NOT for: mathematical computations, prime numbers, factorials

4. Web fetch for specific URLs:
   - Use when you have a specific URL and want to read its full content
   - Extracts readable text from web pages (not HTML code)
   - Useful for reading articles, blog posts, documentation pages

5. Task delegation to subagents:
   - Use delegate_task tool for web research tasks
   - Use subagent_name="web_research" for comprehensive research
   - Returns summary with inline citations [Title](URL)
"""

_PYTHON3_LIMITATIONS = """
**Programming Language Access:**
You ONLY have access to Python 3 interpreter. You cannot execute code in
other programming languages like JavaScript, Ruby, Java, C++, etc.

**Python Code Execution:**
Use the execute_python_code tool:
- Simple: execute_python_code(code="print(2+2)")
- Multi-line: execute_python_code(code="def func(): return 42\\nprint(func())")
- With imports: execute_python_code(code="import math; print(math.pi)")
"""

_ALGORITHM_GUIDANCE = """
**OPTIMAL ALGORITHM GUIDANCE - CRITICAL:**

**Mathematical Problems - Use Standard Library:**
- Factorials: `import math; math.factorial(n)` - never write loops
- GCD/LCM: `import math; math.gcd(a, b)`, `math.lcm(a, b)`
- Combinatorics: `import math; math.comb(n, k)`, `math.perm(n, k)`
- Prime checking: Write efficient isprime() using trial division up to sqrt(n)
- Nth prime: Use Sieve of Eratosthenes algorithm - estimate upper bound with n*log(n*log(n))
- Fibonacci: Use matrix exponentiation for large n, or simple iteration
- Statistics: `import statistics; statistics.mean()`, `median()`, `stdev()`

**Efficient Data Structures:**
- Use `collections.Counter` for counting
- Use `collections.defaultdict` for grouping
- Use `itertools` for permutations, combinations, product
- Use list/dict comprehensions instead of manual loops
- Use `set()` for O(1) lookups instead of `in` on lists

**Performance Rules:**
- Avoid O(n²) algorithms when O(n log n) or O(n) exists
- Use Sieve of Eratosthenes for finding multiple primes
- Use binary search (`bisect` module) for sorted data
- Pre-compute and cache when possible

**AVAILABLE PYTHON LIBRARIES:**
- Standard: math, itertools, collections, functools, bisect, heapq, decimal, fractions, statistics, random, json, re, datetime, pathlib
- Transitive: pydantic (validation), httpx (HTTP), lxml (XML/HTML), rich (pretty print), regex (enhanced regex), yaml (YAML parsing)
"""

_COMPUTATIONAL_PREFERENCE = """
**TOOL SELECTION FOR COMPUTATIONS:**

**Use execute_cli_command (Python) for:**
- Mathematical calculations (arithmetic, algebra, calculus)
- Number theory (primes, factors, GCD, etc.)
- Statistical computations
- String/text processing
- Data transformations
- Any problem with a known algorithmic solution

**Use delegate_task for web research:**
- Current events, news, recent developments
- Factual information not computable (population, prices, etc.)
- Finding documentation or tutorials
- Topics requiring multiple sources
- Use subagent_name="web_research" to delegate web searches with source evaluation

**Example:** "What is the 500000th prime?" → Use Python with Sieve of Eratosthenes, NOT web search
"""

_BEHAVIORAL_RULES = """
**CRITICAL BEHAVIOR RULES:**
- You can call multiple tools in parallel in a single turn
- Execute each tool ONCE and provide the best answer you can
- NEVER retry the same tool with the same parameters to "verify" or "get more details"
- If results are incomplete, try a DIFFERENT tool or approach
- Complex calculations should be executed once, not multiple times
- Web searches should be done once per topic, not repeated
- Finalize your answer after getting results, don't keep looking for "better" ones
"""

_DETAILED_TOOL_EXAMPLES = """
- **Python one-liners**: uv run python -c 'import math; print(math.sqrt(16))'
   * uv run python -c 'import math; print(math.gcd(48, 18))'
   * uv run python -c 'import math; print(math.factorial(10))'

- **Python multi-line**: Use heredoc syntax:
   uv run python << 'EOF'
def sieve(n):
    is_prime = [True] * (n+1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5)+1):
        if is_prime[i]:
            for j in range(i*i, n+1, i):
                is_prime[j] = False
    return [i for i, prime in enumerate(is_prime) if prime]

primes = sieve(100)
print(f"Found {len(primes)} primes: {primes}")
EOF

- **CRITICAL RULES**:
   * Use ONLY single quotes with -c: uv run python -c 'code'
   * Use ONLY standard library: math, itertools, collections, bisect, heapq
   * NO external libraries: numpy, pandas, sympy, etc.
   * Keep one-liners simple and avoid shell syntax conflicts
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
            "content": f"Current date and time: {iso_format} ({day_name}, UTC)",
        }


class SystemPrompts:
    """System prompts for the AI assistant."""

    MAIN_SYSTEM_PROMPT = f"""You are a helpful AI assistant that can use CLI tools
    and web tools to get factual information.

    When users ask for factual information like date/time, weather, system info,
    news, or web content, use the available tools to get accurate information.

    You have these tools available:
    1. CLI commands for system information (date, weather, files, Python code execution)
    2. Web research for discovering and synthesizing information from web sources
    3. Web fetch for reading the full content of a specific URL
    {_get_temporal_resolution_guidelines()}
    {_BEHAVIORAL_RULES}
    {_PYTHON3_LIMITATIONS}
    {_ALGORITHM_GUIDANCE}
    {_COMPUTATIONAL_PREFERENCE}
    {_SOURCE_CREDIBILITY_GUIDELINES}
    **EXECUTION SAFETY:**
    - Use single quotes only: uv run python -c 'code'
    - Standard library only: math, itertools, collections, bisect, heapq
    - No external libraries: numpy, pandas, sympy, etc.
    - Avoid shell syntax conflicts in one-liners
    Provide a helpful response based on the actual information you received.
    Don't mention the tool commands or technical details."""

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
{_ALGORITHM_GUIDANCE}
{_COMPUTATIONAL_PREFERENCE}

    IMPORTANT GUIDELINES:
    - **CRITICAL**: Do NOT call the same tool with the same parameters multiple times
    - **CRITICAL**: Do NOT fetch the same URL more than once
    - **CRITICAL**: Use Python (execute_cli_command) for ALL mathematical computations
    - **CRITICAL**: Use delegate_task for ALL web search and research tasks
    - **Use delegate_task**: For web research (subagent_name="web_research")
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
                "Execute safe CLI commands for system information only. "
                "Use for: date, ls, pwd, df, uname, cat, head, tail, grep, find, etc. "
                "DEPRECATED: Do NOT use for Python execution - use execute_python_code instead. "
                "For file operations: Use standard Linux commands safely."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "The CLI command for system tasks only. "
                            "File operations: ls, cat, head, tail, less, grep, find. "
                            "System info: date, uname, whoami, hostname, ps, df, free, top. "
                            "WARNING: Do NOT use for Python code execution."
                        ),
                    }
                },
                "required": ["command"],
            },
        },
    }

    PYTHON_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": (
                "Execute Python code for mathematical computations, algorithms, and data processing. "
                "Supports 60KB code length. Available: math (factorial, gcd, comb), itertools, collections, bisect, heapq. "
                "Use efficient algorithms: Sieve of Eratosthenes for primes, math.factorial(n) for factorials, math.gcd() for GCD. "
                "Just provide the Python code - 'uv run python' is added automatically. "
                "For simple system commands (date, ls, pwd), use execute_cli_command instead. "
                "DEPRECATED: Do NOT use execute_cli_command for Python execution."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": (
                            "Python code to execute. No 'uv run python' prefix needed. "
                            "Use efficient algorithms: Sieve of Eratosthenes for primes, "
                            "math.factorial(n) for factorials, math.gcd() for GCD. "
                            "STANDARD LIBRARY ONLY: math, itertools, collections, bisect, heapq, statistics, random. "
                            "NO numpy, pandas, or external libraries."
                        ),
                    }
                },
                "required": ["code"],
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
                            "Maximum number of results to return (1-10, default: 5)"
                        ),
                        "default": 5,
                    },
                    "days_ago": {
                        "type": "integer",
                        "description": (
                            "Filter results from last N days (optional, "
                            "e.g., 7 for last week, 30 for last month)"
                        ),
                        "default": None,
                    },
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
                "- web_research: Comprehensive web search with source evaluation, multi-source synthesis, and inline citations [Title](URL)"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subagent_name": {
                        "type": "string",
                        "description": ("Name of the subagent to use: 'web_research'"),
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

    USER_ASPECT_TOOL_DESCRIPTION = {
        "type": "function",
        "function": {
            "name": "store_user_aspect",
            "description": (
                "Store a discovered aspect about the user. Use when you learn something meaningful "
                "about their personality, interests, status, preferences, or other characteristics. "
                "This helps build a user profile that improves future conversations. "
                "Examples: 'enjoys Python programming', 'works as a software engineer', 'likes hiking', 'friendly personality'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": (
                            "Category of the aspect (e.g., 'interests', 'personality', 'status', "
                            "'preferences', 'profession', 'lifestyle')"
                        ),
                    },
                    "aspect": {
                        "type": "string",
                        "description": (
                            "The discovered aspect description (e.g., 'enjoys Python programming', "
                            "'works as software engineer', 'friendly personality')"
                        ),
                    },
                    "confidence": {
                        "type": "number",
                        "description": (
                            "Confidence level 0.0-1.0 (default 0.5). Use higher confidence "
                            "when you're very certain about the aspect, lower when less certain."
                        ),
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.5,
                    },
                },
                "required": ["category", "aspect"],
            },
        },
    }

    @classmethod
    def get_tool_definitions(cls) -> list[dict[str, Any]]:
        """Get all available tool definitions."""
        return [
            cls.PYTHON_TOOL_DESCRIPTION,
            cls.CLI_TOOL_DESCRIPTION,
            cls.WEB_FETCH_TOOL_DESCRIPTION,
            cls.DELEGATE_TASK_TOOL_DESCRIPTION,
            cls.USER_ASPECT_TOOL_DESCRIPTION,
        ]
