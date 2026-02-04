"""
Tool calling functionality for LLM integration.
"""

import asyncio
import json
import logging
import re
from typing import Any

from ..cli.executor import CLIExecutor
from ..db.operations import DatabaseOperations
from .llm_client import LLMClient
from .prompt_templates import ResponseTemplates, SystemPrompts, ToolDescriptions

logger = logging.getLogger(__name__)


class ToolCallingManager:
    """Manager for LLM tool calling functionality."""

    def __init__(self):
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
            # Call LLM with tool calling capability
            response = await self.llm_client.chat_completion(
                messages=messages,
                tools=self._get_tool_definitions(),
                # tool_choice="auto",  # Removed for simplified testing
            )

            # Handle response
            if response.choices[0].message.tool_calls:
                # LLM wants to use tools - handle multiple tool calls in parallel
                tool_calls = response.choices[0].message.tool_calls

                # Execute all tool calls in parallel using asyncio.gather
                async def execute_single_tool_call(tool_call):
                    """Execute a single tool call and return the result."""
                    if tool_call.function.name == "execute_cli_command":
                        try:
                            command = json.loads(tool_call.function.arguments)[
                                "command"
                            ]

                            # Execute the command
                            result = await self.cli_executor.execute_command(command)

                            # Log command execution for debugging
                            logger.info(
                                f"Executing command for user {user_id}: {command}"
                            )
                            logger.info(
                                f"Command result for user {user_id}: {result[:200]}..."
                            )

                            # Save tool call result (without showing command to user)
                            await db_ops.save_message(
                                user_id, chat_id, 0, "system", result
                            )

                            return {"tool_call_id": tool_call.id, "content": result}

                        except Exception as e:
                            logger.error(
                                f"Error executing command {tool_call.function.arguments}: {e}"
                            )
                            error_result = f"Error executing command: {str(e)}"
                            await db_ops.save_message(
                                user_id, chat_id, 0, "system", error_result
                            )
                            return {
                                "tool_call_id": tool_call.id,
                                "content": error_result,
                            }
                    else:
                        # Unknown tool function
                        error_result = (
                            f"Unknown tool function: {tool_call.function.name}"
                        )
                        await db_ops.save_message(
                            user_id, chat_id, 0, "system", error_result
                        )
                        return {"tool_call_id": tool_call.id, "content": error_result}

                # Execute all tool calls in parallel
                tool_results = await asyncio.gather(
                    *[execute_single_tool_call(tool_call) for tool_call in tool_calls]
                )

                # Add all tool results to messages
                for tool_result in tool_results:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_result["tool_call_id"],
                            "content": tool_result["content"],
                        }
                    )

                # Get final response from LLM with all tool results
                final_response = await self.llm_client.chat_completion(
                    messages=messages
                )

                await db_ops.save_message(
                    user_id,
                    chat_id,
                    0,
                    "assistant",
                    final_response.choices[0].message.content,
                )
                return final_response.choices[0].message.content

            else:
                # For simplified system, use direct response without auto-suggestion
                enhanced_response = response.choices[0].message.content
                await db_ops.save_message(
                    user_id, chat_id, 0, "assistant", enhanced_response
                )
                return enhanced_response

        except Exception as e:
            logger.error(f"Error in process_user_request: {e}")
            error_msg = ResponseTemplates.ERROR_RESPONSE.format(error=str(e))
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
        # Only trigger if there's uncertainty OR if it's a factual query with unsourced claims
        should_trigger = (has_uncertain_language and has_factual_query) or (
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
        return "I can help with factual information like date/time, weather, system info, and web content."

    async def fact_check_response(self, query: str, response: str) -> str:
        """Fact-check a response using available tools."""
        return "I'll help verify this information using available tools."