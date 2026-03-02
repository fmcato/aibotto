"""Python script execution subagent for creating and running Python code."""

import logging
from typing import Any

from aibotto.ai.subagent.base import SubAgent

logger = logging.getLogger(__name__)


class PythonScriptAgent(SubAgent):
    """Specialized subagent for creating and executing Python scripts."""

    def __init__(self):
        super().__init__(max_iterations=3)

    def _get_system_prompt(self) -> str:
        """Get Python execution-specialized system prompt."""
        return """You are a Python code generator. Your output is executed IMMEDIATELY.

RULES:
- Output ONLY Python 3 code
- No explanations, no markdown code blocks, no extra text
- Your code runs with 45-second timeout
- Maximum 3 iterations
- If errors occur, you'll receive simplified error messages for debugging

EXECUTION:
Your output is automatically executed as Python code. You do not need to call any tools.
Just output the Python code directly.

EXAMPLES:
User: "Calculate 2+2"
You: print(2+2)

User: "Sort numbers [3,1,4,2]"
You: print(sorted([3,1,4,2]))

User: "Calculate factorial of 5"
You: def factorial(n): return 1 if n<=1 else n*factorial(n-1)
print(factorial(5))

User: "Process data"
You: data = [1,2,3,4,5]
print(sum(data))

ERROR HANDLING:
If your code has errors, you'll see: "Error: <type>: <message>"
Fix the code and try again. Each error counts toward your 3 iterations.

IMPORTANT: Your output must be ONLY valid Python 3 code. No other text."""

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """No tool definitions - LLM generates code, auto-execution handles it."""
        return []

    def _register_tools(self) -> None:
        """Register Python executor for auto-execution hook."""
        from aibotto.tools.executors.python_direct_executor import PythonDirectExecutor

        python_executor = PythonDirectExecutor()
        self._toolset.register_tool("execute_python", python_executor)

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
            "Create Python code to accomplish this task. "
            "Your output will be executed automatically. "
            "Output ONLY Python code - no explanations or markdown. "
            "If errors occur, you'll see simplified error messages. "
            "Maximum of 3 iterations to get working code. "
            "Total execution time must stay under 45 seconds."
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
