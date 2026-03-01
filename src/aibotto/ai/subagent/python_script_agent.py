"""Python script execution subagent for creating and running Python code."""

import logging
from typing import Any

from aibotto.ai.subagent.base import SubAgent
from aibotto.ai.prompt_templates import ToolDescriptions

logger = logging.getLogger(__name__)


class PythonScriptAgent(SubAgent):
    """Specialized subagent for creating and executing Python scripts."""

    def __init__(self):
        super().__init__(max_iterations=3)

    def _get_system_prompt(self) -> str:
        """Get Python execution-specialized system prompt."""
        return """You are a specialized Python code execution assistant focused on creating and running Python scripts to solve problems.

Your capabilities:
- Create Python scripts to accomplish tasks based on user requests
- Execute Python code in isolated environment with 45-second timeout
- Use CLI tool to execute Python code (python3 -c "your_code")
- Debug and fix code based on error messages
- Provide natural language explanations of what the code does

Execution guidelines:
1. Understand the user's request and determine what Python code would help
2. Create a complete Python script that addresses the request
3. Execute the script using the CLI tool (python3 -c "your_code")
4. If there are errors, read error messages carefully and fix the code
5. You have up to 3 iterations total - use them to debug and improve the script
6. Provide the result in natural language with context about what was done
7. Maximum of 45 seconds total execution time for all scripts
8. Script size can be unlimited, but runtime must stay under 45 seconds

Debugging strategy:
- First iteration: Try initial implementation
- Second iteration: Fix syntax errors, import issues, or runtime errors
- Third iteration: Optimize or handle edge cases if needed
- Always read error messages completely before fixing

Output format:
Provide a helpful response that includes:
1. Explanation of what the Python code does
2. Key result(s) from execution
3. Any insights or findings from the execution
4. Mention if code ran successfully or encountered errors

Example scenarios:
- User asks: "Calculate pi to 10 decimal places" → Create Python code using math.pi
- User asks: "Sort a list of numbers" → Create Python code with list.sort()
- User asks: "Parse this CSV data" → Create Python code with csv module

IMPORTANT: You can only execute Python 3 code using the CLI tool. No other programming languages or system commands are available directly."""

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Subagent only has access to Python execution tool."""
        return [
            ToolDescriptions.CLI_TOOL_DESCRIPTION,
        ]

    def _register_tools(self) -> None:
        """Register CLI tool for Python execution."""
        from aibotto.tools.cli_executor import CLIExecutor

        # Register CLI tool for Python execution
        cli_executor = CLIExecutor()
        self._toolset.register_tool("execute_cli_command", cli_executor)

        logger.info(
            f"PythonScriptAgent {self._instance_id}: Registered tools: "
            f"{self._toolset.get_registered_tools()}"
        )

    async def execute_python_script(
        self,
        task_description: str,
        user_id: int = 0,
        chat_id: int = 0,
    ) -> str:
        """
        Execute Python script to accomplish a task.

        Args:
            task_description: Description of what Python script should accomplish
            user_id: User ID for proper tracking
            chat_id: Chat ID for proper tracking

        Returns:
            Natural language description of results with execution output
        """
        logger.info(
            f"PythonScriptAgent {self._instance_id}: Starting Python execution "
            f"(task: {task_description[:50]}..., user_id: {user_id}, chat_id: {chat_id})"
        )

        task_instructions = (
            "Create and execute Python code to accomplish this task. "
            "Use the execute_cli_command tool with python3 -c 'your_code' format. "
            "Total execution time must stay under 45 seconds. "
            "Explain what the code does and provide results in natural language. "
            "If errors occur, read the error messages and fix the code. "
            "Maximum of 3 iterations to complete the task."
        )

        try:
            result = await self.execute_task(
                initial_message=task_description,
                task_instructions=task_instructions,
                user_id=user_id,
                chat_id=chat_id,
            )
            logger.info(
                f"PythonScriptAgent {self._instance_id}: Python execution completed "
                f"(user_id: {user_id}, chat_id: {chat_id})"
            )
            return result
        except Exception as e:
            logger.error(f"PythonScriptAgent error: {e}")
            return f"Python script execution encountered an error: {str(e)}"
