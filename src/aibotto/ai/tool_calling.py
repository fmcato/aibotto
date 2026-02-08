"""
Enhanced tool calling functionality for LLM integration.
"""

import asyncio
import json
import logging
from typing import Any

from ..db.operations import DatabaseOperations
from ..tools import CLIExecutor, search_web
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

    async def process_user_request(
        self, user_id: int, chat_id: int, message: str, db_ops: DatabaseOperations
    ) -> str:
        """Process user request using LLM with tool calling."""

        # Get conversation history
        history = await db_ops.get_conversation_history(user_id, chat_id)

        # Add current message to history
        await db_ops.save_message(user_id, chat_id, 0, "user", message)

        # Prepare messages with improved system prompts
        messages = SystemPrompts.get_conversation_prompt(history)
        messages.append({"role": "user", "content": message})

        try:
            # Enhanced iterative tool calling with loop
            max_iterations = 20  # Prevent infinite loops
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Call LLM with tool calling capability
                response = await self.llm_client.chat_completion(
                    messages=messages,
                    tools=self._get_tool_definitions(),
                )

                # Handle response - response is now a dict from model_dump()
                if "choices" in response and len(response["choices"]) > 0:
                    choice = response["choices"][0]
                    if "message" in choice and choice["message"]:
                        message_obj = choice["message"]

                        # Check if there are tool calls
                        tool_calls = None
                        if isinstance(message_obj, dict):
                            # Dictionary format
                            if ("tool_calls" in message_obj and
                                message_obj.get("tool_calls") is not None and
                                len(message_obj.get("tool_calls", [])) > 0):
                                tool_calls = message_obj.get("tool_calls")
                                # Ensure tool_calls is a list
                                if isinstance(tool_calls, dict):
                                    tool_calls = [tool_calls]

                        if tool_calls:
                            # LLM wants to use tools - handle multiple tool calls
                            # in parallel

                            # Execute all tool calls in parallel using asyncio.gather
                            async def execute_single_tool_call(
                                tool_call: Any
                            ) -> Any:
                                """Execute a single tool call and return the result."""
                                # Handle both dictionary and object formats
                                tool_call_id = None
                                function_name = None
                                arguments = None

                                if isinstance(tool_call, dict):
                                    # Dictionary format
                                    tool_call_id = tool_call.get("id")
                                    function_name = tool_call.get(
                                        "function", {}
                                    ).get("name")
                                    arguments = tool_call.get(
                                        "function", {}
                                    ).get("arguments")
                                else:
                                    # Object format (fallback)
                                    tool_call_id = getattr(tool_call, "id", None)
                                    function_name = getattr(
                                        tool_call.function, "name", None
                                    ) if hasattr(tool_call, "function") else None
                                    arguments = getattr(
                                        tool_call.function, "arguments", None
                                    ) if hasattr(tool_call, "function") else None

                                if function_name == "execute_cli_command":
                                    try:
                                        if arguments is None:
                                            raise ValueError("No arguments provided")
                                        command = json.loads(arguments)["command"]

                                        # Execute the command
                                        res = await self.cli_executor.execute_command(
                                            command
                                        )
                                        result = res

                                        # Log command execution for debugging
                                        logger.info(
                                            f"Executing command for user {user_id}: "
                                            f"{command}"
                                        )
                                        logger.info(
                                            f"Command result for user {user_id}: "
                                            f"{result[:200]}..."
                                        )

                                        # Save tool call result (without showing
                                        # command to user)
                                        await db_ops.save_message(
                                            user_id, chat_id, 0, "system", result
                                        )

                                        return {
                                            "tool_call_id": tool_call_id,
                                            "content": result
                                        }

                                    except Exception as e:
                                        logger.error(
                                            f"Error executing command "
                                            f"{arguments}: {e}"
                                        )
                                        error_result = (
                                            f"Error executing command: {str(e)}"
                                        )
                                        await db_ops.save_message(
                                            user_id, chat_id, 0, "system", error_result
                                        )
                                        return {
                                            "tool_call_id": tool_call_id,
                                            "content": error_result
                                        }
                                elif function_name == "search_web":
                                    try:
                                        if arguments is None:
                                            raise ValueError("No arguments provided")
                                        search_params = json.loads(arguments)

                                        # Log search for debugging
                                        logger.info(
                                            f"Performing web search for user "
                                            f"{user_id}: "
                                            f"{search_params}"
                                        )

                                        # Execute web search
                                        result = await search_web(
                                            query=search_params.get("query", ""),
                                            num_results=search_params.get(
                                                "num_results", 5
                                            ),
                                            days_ago=search_params.get("days_ago")
                                        )

                                        # Log search result for debugging
                                        logger.info(
                                            f"Web search result for user {user_id}: "
                                            f"{result[:200]}..."
                                        )

                                        # Save tool call result
                                        await db_ops.save_message(
                                            user_id, chat_id, 0, "system", result
                                        )

                                        return {
                                            "tool_call_id": tool_call_id,
                                            "content": result
                                        }

                                    except Exception as e:
                                        logger.error(
                                            f"Error performing web search "
                                            f"{arguments}: {e}"
                                        )
                                        error_result = (
                                            f"Error performing web search: {str(e)}"
                                        )
                                        await db_ops.save_message(
                                            user_id, chat_id, 0, "system", error_result
                                        )
                                        return {
                                            "tool_call_id": tool_call_id,
                                            "content": error_result
                                        }
                                else:
                                    # Unknown tool function
                                    error_result = (
                                        f"Unknown tool function: "
                                        f"{function_name}"
                                    )
                                    await db_ops.save_message(
                                        user_id, chat_id, 0, "system", error_result
                                    )
                                    return {
                                        "tool_call_id": tool_call_id,
                                        "content": error_result
                                    }

                            # Execute all tool calls in parallel
                            tool_results = await asyncio.gather(
                                *[execute_single_tool_call(tool_call)
                                  for tool_call in tool_calls]
                            )

                            # Add all tool results to messages
                            for tool_result in tool_results:
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_result["tool_call_id"],
                                    "content": tool_result["content"],
                                })

                            # Save assistant message with tool calls to history
                            assistant_message = (
                                message_obj.get("content", "")
                                if isinstance(message_obj, dict)
                                else (getattr(message_obj, "content", "") or "")
                            )
                            await db_ops.save_message(
                                user_id, chat_id, 0, "assistant", assistant_message
                            )

                            # Continue the loop to allow for more tool calls or
                            # final response
                            continue

                        else:
                            # No tool calls - this is the final response
                            final_response_content = (
                                message_obj.get("content", "")
                                if isinstance(message_obj, dict)
                                else (getattr(message_obj, "content", "") or "")
                            )
                            await db_ops.save_message(
                                user_id, chat_id, 0, "assistant", final_response_content
                            )
                            return final_response_content
                    else:
                        # No message object - return error
                        error_msg = "Invalid response format: no message found"
                        logger.error(error_msg)
                        await db_ops.save_message(
                            user_id, chat_id, 0, "system", error_msg
                        )
                        return error_msg
                else:
                    # No choices in response - return error
                    error_msg = "Invalid response format: no choices found"
                    logger.error(error_msg)
                    await db_ops.save_message(
                        user_id, chat_id, 0, "system", error_msg
                    )
                    return error_msg

            # If we reach max iterations, return an error message
            error_msg = (
                f"Reached maximum iterations ({max_iterations}) without "
                f"getting a final response."
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

    async def process_prompt_stateless(self, message: str) -> str:
        """Process a single prompt without database persistence.

        Args:
            message: The user's prompt/message

        Returns:
            The assistant's response
        """
        # Prepare messages with system prompt (no history for stateless)
        messages = SystemPrompts.get_base_prompt()
        messages.append({"role": "user", "content": message})

        try:
            max_iterations = 20
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                response = await self.llm_client.chat_completion(
                    messages=messages,
                    tools=self._get_tool_definitions(),
                )

                if "choices" in response and len(response["choices"]) > 0:
                    choice = response["choices"][0]
                    if "message" in choice and choice["message"]:
                        message_obj = choice["message"]

                        tool_calls = None
                        if isinstance(message_obj, dict):
                            if (
                                "tool_calls" in message_obj
                                and message_obj.get("tool_calls") is not None
                                and len(message_obj.get("tool_calls", [])) > 0
                            ):
                                tool_calls = message_obj.get("tool_calls")
                                if isinstance(tool_calls, dict):
                                    tool_calls = [tool_calls]

                        if tool_calls:
                            # Execute tool calls in parallel
                            async def execute_single_tool_call(
                                tool_call: Any,
                            ) -> Any:
                                tool_call_id = None
                                function_name = None
                                arguments = None

                                if isinstance(tool_call, dict):
                                    tool_call_id = tool_call.get("id")
                                    function_name = tool_call.get(
                                        "function", {}
                                    ).get("name")
                                    arguments = tool_call.get(
                                        "function", {}
                                    ).get("arguments")
                                else:
                                    tool_call_id = getattr(tool_call, "id", None)
                                    function_name = (
                                        getattr(tool_call.function, "name", None)
                                        if hasattr(tool_call, "function")
                                        else None
                                    )
                                    arguments = (
                                        getattr(tool_call.function, "arguments", None)
                                        if hasattr(tool_call, "function")
                                        else None
                                    )

                                if function_name == "execute_cli_command":
                                    try:
                                        if arguments is None:
                                            raise ValueError("No arguments provided")
                                        command = json.loads(arguments)["command"]
                                        result = (
                                            await self.cli_executor.execute_command(
                                                command
                                            )
                                        )
                                        logger.info(f"CLI: {command}")
                                        return {
                                            "tool_call_id": tool_call_id,
                                            "content": result,
                                        }
                                    except Exception as e:
                                        logger.error(f"Command error: {e}")
                                        return {
                                            "tool_call_id": tool_call_id,
                                            "content": f"Error: {e}",
                                        }
                                elif function_name == "search_web":
                                    try:
                                        if arguments is None:
                                            raise ValueError("No arguments provided")
                                        params = json.loads(arguments)
                                        result = await search_web(
                                            query=params.get("query", ""),
                                            num_results=params.get("num_results", 5),
                                            days_ago=params.get("days_ago"),
                                        )
                                        logger.info(f"Search: {params.get('query')}")
                                        return {
                                            "tool_call_id": tool_call_id,
                                            "content": result,
                                        }
                                    except Exception as e:
                                        logger.error(f"Search error: {e}")
                                        return {
                                            "tool_call_id": tool_call_id,
                                            "content": f"Error: {e}",
                                        }
                                else:
                                    return {
                                        "tool_call_id": tool_call_id,
                                        "content": f"Unknown tool: {function_name}",
                                    }

                            tool_results = await asyncio.gather(
                                *[
                                    execute_single_tool_call(tc)
                                    for tc in tool_calls
                                ]
                            )

                            for tool_result in tool_results:
                                messages.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tool_result["tool_call_id"],
                                        "content": tool_result["content"],
                                    }
                                )

                            continue

                        else:
                            # Final response
                            final_content = (
                                message_obj.get("content", "")
                                if isinstance(message_obj, dict)
                                else (getattr(message_obj, "content", "") or "")
                            )
                            return final_content
                    else:
                        return "Error: Invalid response format"
                else:
                    return "Error: No response from LLM"

            return f"Error: Reached max iterations ({max_iterations})"

        except Exception as e:
            logger.error(f"Error in process_prompt_stateless: {e}")
            return f"Error: {e}"
