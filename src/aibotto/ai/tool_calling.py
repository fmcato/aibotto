"""
Enhanced tool calling functionality for LLM integration.
"""

import asyncio
import logging
from typing import Any

from ..config.settings import Config
from ..db.operations import DatabaseOperations
from ..tools.tool_registry import tool_registry
from .iteration_manager import IterationManager
from .llm_client import LLMClient
from .message_processor import MessageProcessor
from .prompt_templates import ResponseTemplates, SystemPrompts, ToolDescriptions

logger = logging.getLogger(__name__)


class ToolCallingManager:
    """Manager for LLM tool calling functionality."""

    def __init__(self) -> None:
        self.llm_client = LLMClient()
        self.max_iterations = Config.MAX_TOOL_ITERATIONS
        self.iteration_manager = IterationManager(self.max_iterations)

        # Register tool executors
        self._register_tools()

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for the LLM."""
        return ToolDescriptions.get_tool_definitions()

    def _register_tools(self) -> None:
        """Register tool executors with the registry."""
        from ..tools.executors.cli_executor import CLIExecutor
        from ..tools.executors.web_fetch_executor import WebFetchExecutor
        from ..tools.executors.web_search_executor import WebSearchExecutor

        # Register executors
        tool_registry.register_executor("execute_cli_command", CLIExecutor())
        tool_registry.register_executor("search_web", WebSearchExecutor())
        tool_registry.register_executor("fetch_webpage", WebFetchExecutor())

        logger.info("Registered all tool executors")



    async def _execute_single_tool(
        self,
        function_name: str | None,
        arguments: str | None,
        user_id: int = 0,
        db_ops: DatabaseOperations | None = None,
        chat_id: int = 0,
    ) -> str:
        """Execute a single tool and return the result.

        Args:
            function_name: Name of the tool function to execute
            arguments: JSON string of arguments
            user_id: User ID for logging (optional)
            db_ops: Database operations for saving results (optional)
            chat_id: Chat ID for database operations (optional)

        Returns:
            Tool execution result as string
        """
        if function_name is None:
            error_result = "No function name provided"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result

        if arguments is None:
            arguments = "{}"

        # Get executor from registry
        executor = tool_registry.get_executor(function_name)
        if not executor:
            error_result = f"Unknown tool function: {function_name}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result

        try:
            logger.info(f"Executing tool {function_name} for user {user_id}")
            result = await executor.execute(arguments, user_id, db_ops, chat_id)

            logger.info(
                f"Tool {function_name} result for user {user_id}: {result[:200]}..."
            )

            return result

        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}")
            error_result = f"Error executing {function_name}: {str(e)}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result

    async def _execute_tool_calls(
        self,
        tool_calls: list[Any],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> list[dict[str, Any]]:
        """Execute all tool calls in parallel and return results.

        Args:
            tool_calls: List of tool call objects
            user_id: User ID for logging and database
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results (optional)

        Returns:
            List of tool results with tool_call_id and content
        """

        async def execute_single(tool_call: Any) -> dict[str, Any]:
            tool_call_id, function_name, arguments = (
                MessageProcessor.extract_tool_call_info(tool_call)
            )
            content = await self._execute_single_tool(
                function_name, arguments, user_id, db_ops, chat_id
            )
            return {
                "tool_call_id": tool_call_id,
                "content": content,
            }

        return await asyncio.gather(
            *[execute_single(tc) for tc in tool_calls]
        )





    async def _process_llm_iteration(
        self,
        messages: list[dict[str, Any]],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> tuple[str | None, list[dict[str, Any]] | None]:
        """Process a single LLM iteration.

        Args:
            messages: Conversation messages
            user_id: User ID for logging and database
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results (optional)

        Returns:
            Tuple of (final_response, tool_results)
            - If final_response is not None, it's the final response
            - If tool_results is not None, they should be added to messages
        """
        response = await self.llm_client.chat_completion(
            messages=messages,
            tools=self._get_tool_definitions(),
        )

        if "choices" not in response or len(response["choices"]) == 0:
            error_msg = "Invalid response format: no choices found"
            logger.error(error_msg)
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "system", error_msg
                )
            return error_msg, None

        choice = response["choices"][0]
        if "message" not in choice or not choice["message"]:
            error_msg = "Invalid response format: no message found"
            logger.error(error_msg)
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "system", error_msg
                )
            return error_msg, None

        message_obj = choice["message"]
        tool_calls = MessageProcessor.extract_tool_calls_from_response(message_obj)

        if tool_calls:
            # Execute tool calls
            tool_results = await self._execute_tool_calls(
                tool_calls, user_id, chat_id, db_ops
            )

            # Save assistant message with tool calls to history
            assistant_message = MessageProcessor.extract_response_content(message_obj)
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "assistant", assistant_message
                )

            return None, tool_results
        else:
            # Final response
            final_content = MessageProcessor.extract_response_content(message_obj)
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "assistant", final_content
                )
            return final_content, None

    async def process_user_request(
        self, user_id: int, chat_id: int, message: str, db_ops: DatabaseOperations
    ) -> str:
        """Process user request with LLM tool calling (stateful with db).

        Args:
            user_id: User ID
            chat_id: Chat ID
            message: User message
            db_ops: Database operations instance

        Returns:
            Assistant's response
        """
        # Get conversation history
        history = await db_ops.get_conversation_history(user_id, chat_id)

        # Add current message to history
        await db_ops.save_message(user_id, chat_id, 0, "user", message)

        # Prepare messages with improved system prompts
        messages = SystemPrompts.get_conversation_prompt(
            history, max_turns=self.max_iterations
        )
        messages.append({"role": "user", "content": message})

        try:
            return await self.iteration_manager.process_iterations(
                self, messages, user_id, chat_id, db_ops
            )

        except Exception as e:
            logger.error(f"Error in process_user_request: {e}")
            error_msg = ResponseTemplates.ERROR_RESPONSE.format(
                error=str(e) if hasattr(e, "__str__") else str(type(e))
            )
            await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg

    async def process_prompt_stateless(self, message: str) -> str:
        """Process a single prompt without database persistence (stateless).

        Args:
            message: The user's prompt/message

        Returns:
            The assistant's response
        """
        # Prepare messages with system prompt (no history for stateless)
        messages = SystemPrompts.get_base_prompt(max_turns=self.max_iterations)
        messages.append({"role": "user", "content": message})

        try:
            return await self.iteration_manager.process_iterations(
                self, messages, 0, 0, None
            )

        except Exception as e:
            logger.error(f"Error in process_prompt_stateless: {e}")
            return f"Error: {e}"


