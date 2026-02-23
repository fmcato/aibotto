"""
Enhanced tool calling functionality for LLM integration.
"""

import asyncio
import hashlib
import logging
import time
from typing import Any

from ..config.settings import Config
from ..db.operations import DatabaseOperations
from ..tools.tool_registry import tool_registry
from .iteration_manager import IterationManager
from .llm_client import LLMClient
from .message_processor import MessageProcessor
from .prompt_templates import ResponseTemplates, SystemPrompts, ToolDescriptions

logger = logging.getLogger(__name__)

# Global tracking for tool call deduplication
_tool_call_tracker: dict[str, set[str]] = {}  # user_chat_id -> set of tool call hashes


class ToolCallingManager:
    """Manager for LLM tool calling functionality."""

    def __init__(self) -> None:
        self.llm_client = LLMClient()
        self.max_iterations = Config.MAX_TOOL_ITERATIONS
        self.iteration_manager = IterationManager(self.max_iterations)

        # Tool call tracking
        self._executed_tool_calls: set[str] = set()  # Track tool calls in current session
        self._iteration_count = 0  # Track current iteration number
        self._recent_tool_calls: set[str] = set()  # Track calls in recent iterations

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

    def _generate_tool_call_hash(self, function_name: str, arguments: str) -> str:
        """Generate a unique hash for a tool call to detect duplicates."""
        # Create a deterministic hash of function name and arguments
        call_data = f"{function_name}:{arguments}"
        return hashlib.md5(call_data.encode()).hexdigest()

    def _is_duplicate_tool_call(self, function_name: str, arguments: str, user_id: int, chat_id: int = 0) -> bool:
        """Check if this tool call has been executed before in this conversation."""
        call_hash = self._generate_tool_call_hash(function_name, arguments)

        # Check global tracker for this user
        user_key = f"{user_id}_{chat_id}" if chat_id else f"user_{user_id}"
        if user_key not in _tool_call_tracker:
            _tool_call_tracker[user_key] = set()

        # Check if this exact call has been made before
        is_duplicate = call_hash in _tool_call_tracker[user_key]

        if is_duplicate:
            logger.warning(
                f"DUPLICATE TOOL CALL DETECTED: {function_name} with arguments {arguments[:100]}... "
                f"User: {user_id}, Chat: {chat_id}, Iteration: {self._iteration_count}"
            )
        else:
            _tool_call_tracker[user_key].add(call_hash)
            logger.info(
                f"New tool call: {function_name}, Arguments: {arguments[:100]}..., "
                f"User: {user_id}, Chat: {chat_id}, Iteration: {self._iteration_count}"
            )

        return is_duplicate

    def _is_similar_tool_call(self, function_name: str, arguments: str, user_id: int, chat_id: int = 0) -> bool:
        """Check if this tool call is similar to a previous one (same function, different args)."""
        # Check for similar function calls that might indicate retry logic issues
        user_key = f"{user_id}_{chat_id}" if chat_id else f"user_{user_id}"

        if user_key not in _tool_call_tracker:
            return False

        existing_calls = _tool_call_tracker[user_key]

        # Check if we have calls to the same function with different arguments
        for call_hash in existing_calls:
            try:
                # Parse the hash to extract function name
                # Format: function_name:arguments_hash
                if ":" in call_hash:
                    existing_func_name = call_hash.split(":", 1)[0]
                    if existing_func_name == function_name:
                        logger.info(
                            f"Similar tool call detected: {function_name} "
                            f"(may indicate retry logic issue)"
                        )
                        return True
            except Exception:
                continue

        return False

    def _should_prevent_retry(self, function_name: str, arguments: str, user_id: int, chat_id: int = 0) -> bool:
        """Intelligently determine if a tool call should be prevented based on retry patterns."""
        user_key = f"{user_id}_{chat_id}" if chat_id else f"user_{user_id}"

        if user_key not in _tool_call_tracker:
            return False

        existing_calls = _tool_call_tracker[user_key]

        # Count calls to the same function
        same_function_calls = 0
        for call_hash in existing_calls:
            try:
                if ":" in call_hash:
                    existing_func_name = call_hash.split(":", 1)[0]
                    if existing_func_name == function_name:
                        same_function_calls += 1
            except Exception:
                continue

        # Prevent retry if:
        # 1. Same function called more than 3 times (excessive)
        # 2. Complex calculations called more than once (unnecessary retry)
        # 3. Simple commands called more than 5 times (clearly stuck)
        if same_function_calls > 3:
            logger.warning(f"Excessive function calls detected: {function_name} called {same_function_calls} times")
            return True

        # Special handling for different types of tools
        if "python3" in arguments.lower():
            # Complex calculations shouldn't be retried
            if same_function_calls > 1:
                logger.warning(f"Preventing retry of complex calculation: {function_name}")
                return True
        elif function_name == "execute_cli_command":
            # Other CLI commands shouldn't be retried excessively
            if same_function_calls > 5:
                logger.warning(f"Excessive CLI command retries: {function_name}")
                return True

        return False

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
        start_time = time.time()

        if function_name is None:
            error_result = "No function name provided"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result

        if arguments is None:
            arguments = "{}"

        # Check for duplicate tool calls
        if self._is_duplicate_tool_call(function_name, arguments, user_id, chat_id):
            # Return early for duplicates to prevent infinite loops
            logger.warning(f"Skipping duplicate tool call: {function_name}")
            return f"⚠️ Tool call '{function_name}' already executed in this conversation. Skipping to prevent infinite loops."

        # Track this call in recent calls (keep last 10 calls)
        call_hash = self._generate_tool_call_hash(function_name, arguments)
        self._recent_tool_calls.add(call_hash)
        if len(self._recent_tool_calls) > 10:
            self._recent_tool_calls.pop()

        # Check for similar tool calls that might indicate retry logic issues
        if self._is_similar_tool_call(function_name, arguments, user_id, chat_id):
            logger.info(f"Implementing smart retry prevention for {function_name}")
            # For complex calculations, suggest optimization instead of retry
            if "python3" in arguments.lower() and "calc" in arguments.lower():
                return "🔄 I already attempted a similar calculation. Let me try a different approach or provide you with what I found so far."

        # Check if this call should be prevented due to retry patterns
        if self._should_prevent_retry(function_name, arguments, user_id, chat_id):
            logger.warning(f"Preventing retry of {function_name} - detected unnecessary retry pattern")
            return "🚫 I've already attempted this type of operation multiple times. Let me try a different approach or provide you with the results I have so far."

        # Get executor from registry
        executor = tool_registry.get_executor(function_name)
        if not executor:
            error_result = f"Unknown tool function: {function_name}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result

        try:
            logger.info(
                f"Starting tool execution: {function_name} for user {user_id}, "
                f"chat {chat_id}, iteration {self._iteration_count}"
            )

            result = await executor.execute(arguments, user_id, db_ops, chat_id)
            execution_time = time.time() - start_time

            logger.info(
                f"Tool {function_name} completed in {execution_time:.2f}s for user {user_id}: "
                f"{result[:200]}..."
            )

            # Log slow executions (> 10 seconds)
            if execution_time > 10:
                logger.warning(
                    f"SLOW TOOL EXECUTION: {function_name} took {execution_time:.2f}s "
                    f"for user {user_id}, chat {chat_id}"
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Tool {function_name} failed after {execution_time:.2f}s for user {user_id}: {e}"
            )
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
        if not tool_calls:
            logger.info("No tool calls to execute")
            return []

        logger.info(
            f"Executing {len(tool_calls)} tool calls in parallel for user {user_id}, "
            f"chat {chat_id}, iteration {self._iteration_count}"
        )

        async def execute_single(tool_call: Any) -> dict[str, Any]:
            tool_call_id, function_name, arguments = (
                MessageProcessor.extract_tool_call_info(tool_call)
            )

            safe_args = arguments[:100] if arguments else "None"
            logger.info(
                f"Processing tool call {tool_call_id}: {function_name} "
                f"with arguments: {safe_args}..."
            )

            content = await self._execute_single_tool(
                function_name, arguments, user_id, db_ops, chat_id
            )

            logger.info(
                f"Tool call {tool_call_id} completed: {function_name} "
                f"result length: {len(content)} chars"
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
        # Track iteration number
        self._iteration_count += 1
        logger.info(
            f"Starting LLM iteration {self._iteration_count} for user {user_id}, "
            f"chat {chat_id}, messages: {len(messages)}"
        )

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
        logger.info(
            f"LLM iteration {self._iteration_count} returned {len(tool_calls) if tool_calls else 0} tool calls"
        )

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

            logger.info(
                f"Tool execution completed for iteration {self._iteration_count}, "
                f"results: {len(tool_results)} tool results"
            )
            return None, tool_results
        else:
            # Final response
            final_content = MessageProcessor.extract_response_content(message_obj)
            if db_ops:
                await db_ops.save_message(
                    user_id, chat_id, 0, "assistant", final_content
                )
            logger.info(
                f"Final response received in iteration {self._iteration_count}: "
                f"{len(final_content)} chars"
            )
            return final_content, None

    async def process_user_request(
        self,
        user_id: int,
        chat_id: int,
        message: str,
        db_ops: DatabaseOperations | None = None,
    ) -> str:
        """Process a user request with tool calling capabilities.

        Args:
            user_id: User ID for tracking
            chat_id: Chat ID for tracking
            message: User's message
            db_ops: Database operations for saving results

        Returns:
            Assistant's response
        """
        # Reset tracking for new request
        self._iteration_count = 0
        self._executed_tool_calls.clear()
        self._recent_tool_calls.clear()

        # Prepare messages with conversation history
        messages = await self._prepare_messages(user_id, chat_id, message, db_ops)

        try:
            # Add overall timeout to prevent excessive LLM retries
            overall_timeout = min(self.max_iterations * 15, 120)  # Max 2 minutes total
            logger.info(f"Starting user request with overall timeout: {overall_timeout}s")

            return await asyncio.wait_for(
                self.iteration_manager.process_iterations(
                    self, messages, user_id, chat_id, db_ops
                ),
                timeout=overall_timeout
            )

        except TimeoutError:
            logger.error(f"User request timed out after {overall_timeout}s")
            error_msg = f"⏰ Request timed out after {overall_timeout} seconds. The system was taking too long to process your request."
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg

        except Exception as e:
            logger.error(f"Error in process_user_request: {e}")
            error_msg = ResponseTemplates.ERROR_RESPONSE.format(
                error=str(e) if hasattr(e, "__str__") else str(type(e))
            )
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg

    async def _prepare_messages(
        self,
        user_id: int,
        chat_id: int,
        message: str,
        db_ops: DatabaseOperations | None
    ) -> list[dict[str, str]]:
        """Prepare messages for LLM including conversation history.
        
        Args:
            user_id: User ID 
            chat_id: Chat ID
            message: Current message
            db_ops: Database operations
            
        Returns:
            List of message dicts
        """
        # Get base system prompt
        messages = SystemPrompts.get_base_prompt(max_turns=self.max_iterations)

        # Add conversation history if available
        if db_ops:
            history = await db_ops.get_conversation_history(user_id, chat_id)
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current message
        messages.append({"role": "user", "content": message})

        return messages

        try:
            # Add overall timeout to prevent excessive LLM retries
            overall_timeout = min(self.max_iterations * 15, 120)  # Max 2 minutes total
            logger.info(f"Starting user request with overall timeout: {overall_timeout}s")

            return await asyncio.wait_for(
                self.iteration_manager.process_iterations(
                    self, messages, user_id, chat_id, db_ops
                ),
                timeout=overall_timeout
            )

        except TimeoutError:
            logger.error(f"User request timed out after {overall_timeout}s")
            error_msg = f"⏰ Request timed out after {overall_timeout} seconds. The system was taking too long to process your request."
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg

        except Exception as e:
            logger.error(f"Error in process_user_request: {e}")
            error_msg = ResponseTemplates.ERROR_RESPONSE.format(
                error=str(e) if hasattr(e, "__str__") else str(type(e))
            )
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
            return error_msg

    async def process_prompt_stateless(self, message: str) -> str:
        """Process a single prompt without database persistence (stateless).

        Args:
            message: The user's prompt/message

        Returns:
            The assistant's response
        """
        # Reset tracking for stateless processing
        self._iteration_count = 0
        self._executed_tool_calls.clear()

        # Prepare messages with system prompt (no history for stateless)
        messages = SystemPrompts.get_base_prompt(max_turns=self.max_iterations)
        messages.append({"role": "user", "content": message})

        try:
            # Add overall timeout to prevent excessive LLM retries
            overall_timeout = min(self.max_iterations * 15, 60)  # Max 1 minute for stateless
            logger.info(f"Starting stateless prompt with overall timeout: {overall_timeout}s")

            return await asyncio.wait_for(
                self.iteration_manager.process_iterations(
                    self, messages, 0, 0, None
                ),
                timeout=overall_timeout
            )

        except TimeoutError:
            logger.error(f"Stateless prompt timed out after {overall_timeout}s")
            return f"⏰ Request timed out after {overall_timeout} seconds. The system was taking too long to process your request."

        except Exception as e:
            logger.error(f"Error in process_prompt_stateless: {e}")
            return f"Error: {e}"

    def cleanup_old_entries(self, max_age_hours: int = 24) -> None:
        """Clean up old entries from the global tracker to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age of entries to keep (default: 24 hours)
        """
        # Simple cleanup: remove empty user entries to prevent memory growth
        global _tool_call_tracker
        empty_users = [user_key for user_key, calls in _tool_call_tracker.items() if len(calls) == 0]
        for user_key in empty_users:
            del _tool_call_tracker[user_key]

        if empty_users:
            logger.info(f"Cleaned up {len(empty_users)} empty user entries from tracker")
