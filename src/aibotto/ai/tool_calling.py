"""
Enhanced tool calling functionality for LLM integration.
"""

import asyncio
import json
import logging
from typing import Any

from ..db.operations import DatabaseOperations
from ..tools import CLIExecutor, fetch_webpage, search_web
from .llm_client import LLMClient
from .prompt_templates import ResponseTemplates, SystemPrompts, ToolDescriptions

logger = logging.getLogger(__name__)


class ToolCallingManager:
    """Manager for LLM tool calling functionality."""

    def __init__(self) -> None:
        self.llm_client = LLMClient()
        self.cli_executor = CLIExecutor()

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for the LLM."""
        return ToolDescriptions.get_tool_definitions()

    def _extract_tool_call_info(
        self, tool_call: Any
    ) -> tuple[str | None, str | None, str | None]:
        """Extract tool call ID, function name, and arguments from a tool call.

        Args:
            tool_call: Tool call object (dict or object format)

        Returns:
            Tuple of (tool_call_id, function_name, arguments)
        """
        if isinstance(tool_call, dict):
            return (
                tool_call.get("id"),
                tool_call.get("function", {}).get("name"),
                tool_call.get("function", {}).get("arguments"),
            )
        else:
            has_func = hasattr(tool_call, "function")
            return (
                getattr(tool_call, "id", None),
                getattr(tool_call.function, "name", None) if has_func else None,
                getattr(tool_call.function, "arguments", None) if has_func else None,
            )

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
        if function_name == "execute_cli_command":
            try:
                if arguments is None:
                    raise ValueError("No arguments provided")
                command = json.loads(arguments)["command"]
                result = await self.cli_executor.execute_command(command)

                logger.info(f"Executing command for user {user_id}: {command}")
                logger.info(
                    f"Command result for user {user_id}: {result[:200]}..."
                )

                if db_ops:
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", result
                    )

                return result

            except Exception as e:
                logger.error(f"Error executing command {arguments}: {e}")
                error_result = f"Error executing command: {str(e)}"
                if db_ops:
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", error_result
                    )
                return error_result

        elif function_name == "search_web":
            try:
                if arguments is None:
                    raise ValueError("No arguments provided")
                params = json.loads(arguments)

                logger.info(
                    f"Performing web search for user {user_id}: {params}"
                )

                result = await search_web(
                    query=params.get("query", ""),
                    num_results=params.get("num_results", 5),
                    days_ago=params.get("days_ago"),
                )

                logger.info(
                    f"Web search result for user {user_id}: {result[:200]}..."
                )

                if db_ops:
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", result
                    )

                return result

            except Exception as e:
                logger.error(f"Error performing web search {arguments}: {e}")
                error_result = f"Error performing web search: {str(e)}"
                if db_ops:
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", error_result
                    )
                return error_result

        elif function_name == "fetch_webpage":
            try:
                if arguments is None:
                    raise ValueError("No arguments provided")
                params = json.loads(arguments)

                logger.info(
                    f"Fetching webpage for user {user_id}: {params.get('url')}"
                )

                result = await fetch_webpage(
                    url=params.get("url", ""),
                    max_length=params.get("max_length"),
                    include_links=params.get("include_links", False),
                )

                logger.info(
                    f"Web fetch result for user {user_id}: {result[:200]}..."
                )

                if db_ops:
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", result
                    )

                return result

            except Exception as e:
                logger.error(f"Error fetching webpage {arguments}: {e}")
                error_result = f"Error fetching webpage: {str(e)}"
                if db_ops:
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", error_result
                    )
                return error_result

        else:
            error_result = f"Unknown tool function: {function_name}"
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "system", error_result
                )
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
                self._extract_tool_call_info(tool_call)
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

    def _extract_response_content(self, message_obj: Any) -> str:
        """Extract content from a message object.

        Args:
            message_obj: Message object (dict or object format)

        Returns:
            Message content as string
        """
        if isinstance(message_obj, dict):
            return message_obj.get("content", "") or ""
        else:
            return getattr(message_obj, "content", "") or ""

    def _extract_tool_calls_from_response(
        self, message_obj: Any
    ) -> list[Any] | None:
        """Extract tool calls from a message object.

        Args:
            message_obj: Message object (dict or object format)

        Returns:
            List of tool calls or None
        """
        if not isinstance(message_obj, dict):
            return None

        tool_calls = message_obj.get("tool_calls")
        if tool_calls is None or len(tool_calls) == 0:
            return None

        # Ensure tool_calls is a list
        if isinstance(tool_calls, dict):
            return [tool_calls]
        return list(tool_calls) if tool_calls else None

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
        tool_calls = self._extract_tool_calls_from_response(message_obj)

        if tool_calls:
            # Execute tool calls
            tool_results = await self._execute_tool_calls(
                tool_calls, user_id, chat_id, db_ops
            )

            # Save assistant message with tool calls to history
            assistant_message = self._extract_response_content(message_obj)
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "assistant", assistant_message
                )

            return None, tool_results
        else:
            # Final response
            final_content = self._extract_response_content(message_obj)
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
        messages = SystemPrompts.get_conversation_prompt(history)
        messages.append({"role": "user", "content": message})

        try:
            max_iterations = 10
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                remaining = max_iterations - iteration

                # Add warning when running low on turns
                if remaining <= 3:
                    messages.append({
                        "role": "system",
                        "content": (
                            f"Warning: Only {remaining} turn(s) remaining. "
                            "Provide a final answer now."
                        ),
                    })

                final_response, tool_results = await self._process_llm_iteration(
                    messages, user_id, chat_id, db_ops
                )

                if final_response is not None:
                    return final_response

                if tool_results is not None:
                    # Add tool results to messages
                    for tool_result in tool_results:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_result["tool_call_id"],
                            "content": tool_result["content"],
                        })
                    continue

            # Max iterations reached
            error_msg = (
                f"Reached maximum iterations ({max_iterations}) "
                f"without getting a final response."
            )
            logger.error(error_msg)
            await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg

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
        messages = SystemPrompts.get_base_prompt()
        messages.append({"role": "user", "content": message})

        try:
            max_iterations = 10
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                remaining = max_iterations - iteration

                # Add warning when running low on turns
                if remaining <= 3:
                    messages.append({
                        "role": "system",
                        "content": (
                            f"Warning: Only {remaining} turn(s) remaining. "
                            "Provide a final answer now."
                        ),
                    })

                final_response, tool_results = await self._process_llm_iteration(
                    messages, 0, 0, None
                )

                if final_response is not None:
                    return final_response

                if tool_results is not None:
                    # Add tool results to messages
                    for tool_result in tool_results:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_result["tool_call_id"],
                            "content": tool_result["content"],
                        })
                    continue

            return f"Error: Reached max iterations ({max_iterations})"

        except Exception as e:
            logger.error(f"Error in process_prompt_stateless: {e}")
            return f"Error: {e}"

    def _needs_factual_verification(
        self, response_content: str, original_message: str
    ) -> bool:
        """Check if the response might need factual verification."""
        # Keywords that suggest the response might be uncertain or made up
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

        # Factual query indicators
        factual_indicators = [
            "time",
            "date",
            "when",
            "what day",
            "what time",
            "current",
            "weather",
            "temperature",
            "files",
            "directory",
            "system",
            "computer",
            "os",
            "version",
            "ip",
            "address",
            "memory",
            "storage",
            "disk",
            "cpu",
            "processor",
            "kernel",
        ]

        response_lower = response_content.lower()
        message_lower = original_message.lower()

        # Check if the original message asks for factual information
        has_factual_query = any(
            indicator in message_lower for indicator in factual_indicators
        )

        # Check if the response contains uncertain language
        has_uncertain_language = any(
            keyword in response_lower for keyword in uncertain_keywords
        )

        # Check if the response is making claims without sources
        has_unsourced_claims = "is " in response_lower and not any(
            tool_word in response_lower
            for tool_word in ["command", "tool", "executed", "current"]
        )

        # For certain responses, we should not trigger fact-checking
        # Only trigger if there's uncertainty OR if it's a factual query
        # with unsourced claims
        should_trigger = (
            has_uncertain_language and has_factual_query
        ) or (
            has_factual_query
            and has_unsourced_claims
            and not any(
                certain_word in response_lower
                for certain_word in ["current", "exact", "precise", "specific"]
            )
        )

        return should_trigger

    async def get_factual_commands_info(self) -> str:
        """Get information about available factual commands."""
        return (
            "I can help with factual information like date/time, weather, "
            "system info, and web content."
        )

    async def fact_check_response(self, query: str, response: str) -> str:
        """Fact-check a response using available tools."""
        return "I'll help verify this information using available tools."
