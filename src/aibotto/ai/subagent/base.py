"""Subagent class with isolated LLM context and iteration management."""

import logging
from typing import Any

from aibotto.ai.agentic_loop_processor import (
    BaseAgenticLoopProcessor,
    ToolExecutionInterface,
)
from aibotto.ai.llm_client import LLMClient, LLMConfig
from aibotto.ai.prompt_templates import DateTimeContext
from aibotto.ai.tool_tracker import ToolTracker
from aibotto.config.subagent_config import LLMProviderConfig, SubAgentDefinition
from .toolset import SubAgentToolset

logger = logging.getLogger(__name__)


class SubAgent(BaseAgenticLoopProcessor):
    """Subagent with isolated LLM context, configured from YAML definition."""

    def __init__(
        self,
        definition: SubAgentDefinition,
        provider: LLMProviderConfig,
    ):
        """Initialize the subagent with config.

        Args:
            definition: Subagent definition from config
            provider: LLM provider configuration
        """
        self._definition = definition
        self._provider = provider

        llm_config = LLMConfig.from_provider(
            provider_config=provider,
            model=definition.model,
            max_tokens=definition.max_tokens,
            temperature=definition.temperature,
        )

        llm_client = LLMClient(config=llm_config)
        tracker = ToolTracker(id(self))

        super().__init__(
            max_iterations=definition.max_iterations,
            llm_client=llm_client,
            tracker=tracker,
        )
        self._instance_id = id(self)
        self._toolset = SubAgentToolset(self._instance_id)
        self._tracker = self.tracker
        logger.info(
            f"Created SubAgent '{definition.name}' "
            f"(model: {definition.model}, tools: {definition.tools}, "
            f"max_iterations: {definition.max_iterations})"
        )

    def _get_system_prompt(self) -> str:
        """Get system prompt from config definition with dynamic values.

        Returns:
            System prompt string with max_iterations injected
        """
        base_prompt = self._definition.system_prompt

        dynamic_context = f"""

OPERATIONAL LIMITS:
- Maximum iterations allowed: {self._definition.max_iterations}
- Use your iterations wisely - each tool call counts as one iteration
- Plan your approach before executing to stay within the limit"""

        return base_prompt + dynamic_context

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for this subagent.

        Returns:
            List of tool definition dicts
        """
        from aibotto.ai.prompt_templates import ToolDescriptions

        tool_map = {
            "search_web": ToolDescriptions.WEB_SEARCH_TOOL_DESCRIPTION,
            "fetch_webpage": ToolDescriptions.WEB_FETCH_TOOL_DESCRIPTION,
            "execute_cli_command": ToolDescriptions.CLI_TOOL_DESCRIPTION,
            "execute_python_code": ToolDescriptions.PYTHON_TOOL_DESCRIPTION,
            "delegate_task": ToolDescriptions.DELEGATE_TASK_TOOL_DESCRIPTION,
        }

        definitions = []
        for tool_name in self._definition.tools:
            if tool_name in tool_map:
                definitions.append(tool_map[tool_name])
            else:
                logger.warning(
                    f"Unknown tool '{tool_name}' in subagent '{self._definition.name}'"
                )

        return definitions

    def _register_tools(self) -> None:
        """Register tools from config definition."""
        from aibotto.tools.executors.cli_executor import CLIExecutor
        from aibotto.tools.executors.python_executor import PythonExecutor
        from aibotto.tools.executors.web_fetch_executor import WebFetchExecutor
        from aibotto.tools.executors.web_search_executor import WebSearchExecutor
        from aibotto.tools.delegate_tool import DelegateExecutor

        tool_executors = {
            "search_web": WebSearchExecutor,
            "fetch_webpage": WebFetchExecutor,
            "execute_cli_command": CLIExecutor,
            "execute_python_code": PythonExecutor,
            "delegate_task": DelegateExecutor,
        }

        for tool_name in self._definition.tools:
            if tool_name in tool_executors:
                executor_class = tool_executors[tool_name]
                executor = executor_class()  # type: ignore[abstract]
                self._toolset.register_tool(tool_name, executor)
                logger.debug(
                    f"Registered tool '{tool_name}' for subagent '{self._definition.name}'"
                )
            else:
                logger.warning(
                    f"Cannot register unknown tool '{tool_name}' "
                    f"for subagent '{self._definition.name}'"
                )

        logger.info(
            f"SubAgent '{self._definition.name}': "
            f"Registered tools: {self._toolset.get_registered_tools()}"
        )

    def get_tool_execution_interface(self) -> ToolExecutionInterface:
        """Get the tool execution interface for this subagent."""
        from aibotto.ai.tool_executor import ToolExecutor
        from aibotto.config.settings import Config

        return ToolExecutor(
            tracker=self.tracker,
            toolset=self._toolset,
            max_concurrent=Config.SUBAGENT_MAX_CONCURRENT_TOOLS,
            instance_id=self._instance_id,
        )

    async def execute_task(
        self,
        initial_message: str,
        task_instructions: str = "",
        user_id: int = 0,
        chat_id: int = 0,
    ) -> str:
        """Execute a task in isolated LLM context.

        Args:
            initial_message: The initial user message to process
            task_instructions: Additional instructions for the task
            user_id: User ID for proper tracking
            chat_id: Chat ID for proper tracking

        Returns:
            Final response string
        """

        # Build messages
        datetime_msg = DateTimeContext.get_current_datetime_message()
        logger.info(
            f"SubAgent {self._instance_id}: Added datetime context: "
            f"{datetime_msg['content']}"
        )

        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            datetime_msg,
        ]

        if task_instructions:
            messages.append({"role": "system", "content": f"Task: {task_instructions}"})

        messages.append({"role": "user", "content": initial_message})

        logger.info(
            f"SubAgent {self._instance_id}: Starting task execution "
            f"(user_id: {user_id}, chat_id: {chat_id})"
        )

        # Register tools for this subagent instance
        self._register_tools()

        return await self.process_iterations(
            messages, user_id=user_id, chat_id=chat_id, db_ops=None
        )

    @property
    def name(self) -> str:
        """Get subagent name.

        Returns:
            Subagent name
        """
        return self._definition.name

    @property
    def description(self) -> str:
        """Get subagent description.

        Returns:
            Subagent description
        """
        return self._definition.description

    async def execute(
        self,
        query: str,
        user_id: int = 0,
        chat_id: int = 0,
        **kwargs: Any,
    ) -> str:
        """Execute the subagent task.

        This is a generic execute method that works with any subagent.

        Args:
            query: The task/query to process
            user_id: User ID for tracking
            chat_id: Chat ID for tracking
            **kwargs: Additional arguments (ignored for now)

        Returns:
            Result string from subagent execution
        """
        logger.info(
            f"SubAgent '{self._definition.name}': Starting execution "
            f"(query: {query[:50]}..., user_id: {user_id}, chat_id: {chat_id})"
        )

        try:
            result = await self.execute_task(
                initial_message=query,
                task_instructions="",
                user_id=user_id,
                chat_id=chat_id,
            )
            logger.info(
                f"SubAgent '{self._definition.name}': Execution completed "
                f"(user_id: {user_id}, chat_id: {chat_id})"
            )
            return result
        except Exception as e:
            logger.error(f"SubAgent '{self._definition.name}': Execution failed - {e}")
            return f"Subagent '{self._definition.name}' encountered an error: {str(e)}"
