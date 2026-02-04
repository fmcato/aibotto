"""
Enhanced CLI command executor with intelligent command selection for factual information.
"""

import logging
from dataclasses import dataclass

from .executor import CLIExecutor

logger = logging.getLogger(__name__)


@dataclass
class CommandSuggestion:
    """Suggested command for a given query."""

    command: str
    confidence: float
    reason: str


class EnhancedCLIExecutor(CLIExecutor):
    """Enhanced CLI executor with intelligent command selection."""

    def __init__(self):
        super().__init__()
        self.command_suggestions = self._build_command_suggestions()

    def _build_command_suggestions(self) -> dict[str, list[CommandSuggestion]]:
        """Build command suggestions for different query types."""
        return {
            "time": [
                CommandSuggestion("date", 0.9, "Get current date and time"),
                CommandSuggestion("timedatectl", 0.8, "Get detailed time information"),
                CommandSuggestion("uptime", 0.7, "Get system uptime"),
            ],
            "date": [
                CommandSuggestion("date", 0.9, "Get current date"),
                CommandSuggestion("cal", 0.7, "Get calendar view"),
            ],
            "weather": [
                CommandSuggestion(
                    "curl 'https://wttr.in/?format=3'", 0.9, "Get weather from wttr.in"
                ),
                CommandSuggestion(
                    "curl 'https://wttr.in/London?format=3'",
                    0.8,
                    "Get weather for specific city",
                ),
            ],
            "file": [
                CommandSuggestion("ls -la", 0.9, "List files with details"),
                CommandSuggestion("pwd", 0.8, "Show current directory"),
                CommandSuggestion("df -h", 0.7, "Show disk usage"),
            ],
            "directory": [
                CommandSuggestion("ls -la", 0.9, "List directory contents"),
                CommandSuggestion("pwd", 0.8, "Show current directory path"),
            ],
            "system": [
                CommandSuggestion("uname -a", 0.9, "Get system information"),
                CommandSuggestion("uptime", 0.8, "Get system uptime"),
                CommandSuggestion("free -h", 0.7, "Get memory usage"),
            ],
            "computer": [
                CommandSuggestion("uname -a", 0.9, "Get computer information"),
                CommandSuggestion("lscpu", 0.8, "Get CPU information"),
                CommandSuggestion("free -h", 0.7, "Get memory information"),
            ],
            "os": [
                CommandSuggestion("uname -a", 0.9, "Get OS information"),
                CommandSuggestion("cat /etc/os-release", 0.8, "Get OS version"),
            ],
            "ip": [
                CommandSuggestion("ip addr", 0.9, "Get IP addresses"),
                CommandSuggestion("hostname -I", 0.8, "Get IP addresses"),
            ],
            "address": [
                CommandSuggestion("ip addr", 0.9, "Get network addresses"),
                CommandSuggestion("hostname -I", 0.8, "Get IP addresses"),
            ],
            "memory": [
                CommandSuggestion("free -h", 0.9, "Get memory usage"),
                CommandSuggestion("vmstat", 0.8, "Get memory statistics"),
            ],
            "storage": [
                CommandSuggestion("df -h", 0.9, "Get storage information"),
                CommandSuggestion("du -sh *", 0.7, "Get directory sizes"),
            ],
            "disk": [
                CommandSuggestion("df -h", 0.9, "Get disk usage"),
                CommandSuggestion("lsblk", 0.8, "Get disk information"),
            ],
            "cpu": [
                CommandSuggestion("lscpu", 0.9, "Get CPU information"),
                CommandSuggestion("top -bn1 | grep 'Cpu(s)'", 0.7, "Get CPU usage"),
            ],
            "processor": [
                CommandSuggestion("lscpu", 0.9, "Get processor information"),
                CommandSuggestion("cat /proc/cpuinfo", 0.8, "Get detailed CPU info"),
            ],
            "kernel": [
                CommandSuggestion("uname -r", 0.9, "Get kernel version"),
                CommandSuggestion("uname -a", 0.8, "Get full system information"),
            ],
            "news": [
                CommandSuggestion(
                    "curl -A \"Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36\" https://www.cnn.com",
                    0.9,
                    "Get news from CNN",
                ),
                CommandSuggestion(
                    "curl -A \"Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36\" https://www.bbc.com",
                    0.8,
                    "Get news from BBC",
                ),
            ],
            "web": [
                CommandSuggestion(
                    "curl -A \"Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36\" https://www.example.com",
                    0.9,
                    "Get web page content",
                ),
            ],
            "website": [
                CommandSuggestion(
                    "curl -A \"Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36\" https://www.example.com",
                    0.9,
                    "Fetch website content",
                ),
            ],
        }

    def suggest_command(self, query: str) -> CommandSuggestion | None:
        """Suggest the best command for a given query."""
        query_lower = query.lower()

        # Find matching categories
        matches = []
        for category, suggestions in self.command_suggestions.items():
            if category in query_lower:
                matches.extend(suggestions)

        if not matches:
            return None

        # Return the best match (highest confidence)
        return max(matches, key=lambda x: x.confidence)

    async def execute_with_suggestion(self, query: str) -> str:
        """Execute a command based on query suggestion."""
        suggestion = self.suggest_command(query)

        if suggestion:
            logger.info(
                f"Executing suggested command for query '{query}': {suggestion.command}"
            )
            result = await self.execute_command(suggestion.command)
            # Clean up the result to remove extra whitespace and formatting
            clean_result = result.strip()
            logger.info(
                f"Suggestion command result for query '{query}': {clean_result[:200]}..."
            )
            return clean_result
        else:
            logger.info(f"No suitable command found for query: {query}")
            return "I don't have access to the specific tools needed for this query."

    async def execute_fact_check(self, query: str, response: str) -> str:
        """Execute commands to fact-check a response."""
        # Check if response contains uncertain language
        uncertain_keywords = [
            "probably",
            "maybe",
            "might be",
            "could be",
            "I think",
            "I believe",
            "approximately",
            "around",
            "about",
            "roughly",
            "seems like",
            "likely",
            "possibly",
            "potentially",
            "perhaps",
        ]

        response_lower = response.lower()
        has_uncertainty = any(
            keyword in response_lower for keyword in uncertain_keywords
        )

        if has_uncertainty:
            logger.info(f"Fact-checking uncertain response for query: {query}")
            # Suggest factual commands
            suggestion = self.suggest_command(query)
            if suggestion:
                logger.info(
                    f"Executing fact-check command for query '{query}': {suggestion.command}"
                )
                result = await self.execute_command(suggestion.command)
                # Clean up the result to remove extra whitespace and formatting
                clean_result = result.strip()
                logger.info(
                    f"Fact-check result for query '{query}': {clean_result[:200]}..."
                )
                return clean_result
            else:
                logger.info(f"No fact-check command found for query: {query}")
                return "No fact-check needed for this response."
        else:
            logger.info(f"No uncertainty detected in response for query: {query}")
            return "No fact-check needed for this response."

    async def get_available_commands_info(self) -> str:
        """Get information about available commands."""
        info = "🤖 **I can help you with factual information about:**\n\n"

        categories = [
            ("time", "Current date and time"),
            ("weather", "Weather information"),
            ("files", "File system and directory information"),
            ("system", "Computer and system information"),
            ("network", "Network and IP addresses"),
            ("hardware", "Memory, CPU, and storage information"),
        ]

        for _category, description in categories:
            info += f"• **{description}**\n"

        info += (
            "\n💡 Just ask me any question and I'll get you the factual information!"
        )

        return info
