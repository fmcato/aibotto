"""Base subagent class with isolated LLM context and iteration management."""

import asyncio
import logging
from typing import Any

from aibotto.ai.iteration_manager import IterationManager
from aibotto.ai.llm_client import LLMClient
from aibotto.ai.prompt_templates import DateTimeContext
from aibotto.ai.tool_tracker import SubAgentTracker
from aibotto.config.settings import Config
from .toolset import SubAgentToolset

logger = logging.getLogger(__name__)


class SubAgent:
    """Base class for specialized subagents with isolated LLM context."""

    def __init__(self, max_iterations: int = 5):
        self.llm_client = LLMClient()
        self.max_iterations = max_iterations
        self.iteration_manager = IterationManager(max_iterations)
        self._instance_id = id(self)
        self._tracker = SubAgentTracker(self._instance_id)
        self._toolset = SubAgentToolset(self._instance_id)
        logger.info(
            f"Created SubAgent instance {self._instance_id} "
            f"(max_iterations: {max_iterations})"
        )

    def _get_system_prompt(self) -> str:
        """Get subagent-specific system prompt. Override in subclasses."""
        return "You are a helpful assistant."

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions available to this subagent. Override in subclasses."""
        return []
    
    def _register_tools(self) -> None:
        """Register tools available to this subagent. Override in subclasses."""
        pass

    async def execute_task(
        self,
        initial_message: str,
        task_instructions: str = "",
        user_id: int = 0,
        chat_id: int = 0,
    ) -> str:
        """
        Execute a task in isolated LLM context.

        Args:
            initial_message: The initial user message to process
            task_instructions: Additional instructions for the task
            user_id: User ID for proper tracking
            chat_id: Chat ID for proper tracking

        Returns:
            Final response string
        """
        from aibotto.ai.message_processor import MessageProcessor

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
            messages.append({
                "role": "system",
                "content": f"Task: {task_instructions}"
            })

        messages.append({"role": "user", "content": initial_message})

        logger.info(
            f"SubAgent {self._instance_id}: Starting task execution "
            f"(user_id: {user_id}, chat_id: {chat_id})"
        )

        # Register tools for this subagent instance
        self._register_tools()
        
        # SubProtocol implementation for iteration manager
        class SubProcessor:
            def __init__(self, llm_client, tool_defs, tracker, toolset):
                self.llm_client = llm_client
                self.tool_defs = tool_defs
                self.tracker = tracker
                self.toolset = toolset

            async def _process_llm_iteration(
                self,
                messages: list[dict[str, Any]],
                user_id: int = 0,
                chat_id: int = 0,
                db_ops: Any = None,
            ) -> tuple[str | None, list[dict[str, Any]] | None, list[Any] | None]:
                response = await self.llm_client.chat_completion(
                    messages=messages,
                    tools=self.tool_defs if self.tool_defs else None,
                )

                # Extract and handle response
                choice = response["choices"][0]
                message_obj = choice["message"]

                tool_calls = MessageProcessor.extract_tool_calls_from_response(message_obj)

                if tool_calls:
                    # Use subagent-specific tool executor
                    tool_results = await self._execute_subagent_tools(
                        tool_calls, user_id, chat_id
                    )

                    final_content = MessageProcessor.extract_response_content(message_obj)

                    return None, tool_results, tool_calls
                else:
                    final_content = MessageProcessor.extract_response_content(message_obj)
                    return final_content, None, None
            
            async def _execute_subagent_tools(
                self,
                tool_calls: list[Any],
                user_id: int = 0,
                chat_id: int = 0,
            ) -> list[dict[str, Any]]:
                """Execute tool calls in parallel using subagent-specific toolset."""
                from aibotto.ai.message_processor import MessageProcessor
                
                async def execute_single_tool_call(tool_call: Any) -> dict[str, Any]:
                    tool_call_id, function_name, arguments = (
                        MessageProcessor.extract_tool_call_info(tool_call)
                    )
                    
                    logger.info(
                        f"SubAgent {self.tracker._instance_id}: Executing tool {function_name} "
                        f"for user {user_id}, chat {chat_id}"
                    )
                    
                    # Get tool from subagent toolset
                    tool_executor = self.toolset.get_tool(function_name)
                    if not tool_executor:
                        error_result = f"Unknown tool function: {function_name}"
                        logger.warning(f"SubAgent {self.tracker._instance_id}: Unknown tool - {function_name}")
                        return {
                            "tool_call_id": tool_call_id,
                            "content": error_result,
                        }
                    
                    try:
                        # Execute the tool
                        result = await tool_executor.execute(
                            arguments, user_id, None, chat_id
                        )
                        logger.info(
                            f"SubAgent {self.tracker._instance_id}: Tool {function_name} completed "
                            f"successfully for user {user_id}"
                        )
                        return {
                            "tool_call_id": tool_call_id,
                            "content": result,
                        }
                    except Exception as e:
                        error_result = f"Error executing {function_name}: {str(e)}"
                        logger.error(f"SubAgent {self.tracker._instance_id}: Tool {function_name} failed - {e}")
                        return {
                            "tool_call_id": tool_call_id,
                            "content": error_result,
                        }
                
                # Execute tool calls in parallel with concurrency limit
                max_concurrent = Config.SUBAGENT_MAX_CONCURRENT_TOOLS
                semaphore = asyncio.Semaphore(max_concurrent)
                
                async def execute_with_limit(tool_call: Any) -> dict[str, Any]:
                    async with semaphore:
                        return await execute_single_tool_call(tool_call)
                
                # Execute all tool calls in parallel
                results = await asyncio.gather(*[
                    execute_with_limit(tc) for tc in tool_calls
                ], return_exceptions=False)
                
                return results

        processor = SubProcessor(
            self.llm_client,
            self._get_tool_definitions(),
            self._tracker,
            self._toolset
        )

        return await self.iteration_manager.process_iterations(
            processor, messages, user_id=user_id, chat_id=chat_id, db_ops=None
        )