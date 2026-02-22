"""
Iteration management for LLM tool calling.
"""

import asyncio
import logging
from typing import Any, List, Tuple

from ..config.settings import Config
from ..db.operations import DatabaseOperations

logger = logging.getLogger(__name__)


class IterationManager:
    """Manages LLM iteration limits and warning messages."""
    
    def __init__(self, max_iterations: int) -> None:
        self.max_iterations = max_iterations
    
    async def process_iterations(
        self,
        llm_processor,
        messages: List[dict[str, Any]],
        user_id: int = 0,
        chat_id: int = 0,
        db_ops: DatabaseOperations | None = None,
    ) -> str:
        """Process LLM iterations with proper limits and warnings.
        
        Args:
            llm_processor: LLM processor instance with _process_llm_iteration method
            messages: Conversation messages
            user_id: User ID for logging and database
            chat_id: Chat ID for database operations
            db_ops: Database operations for saving results (optional)
            
        Returns:
            Assistant's response
        """
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            remaining = self.max_iterations - iteration
            
            # Add warning when running low on turns
            if remaining <= 3:
                messages.append({
                    "role": "user",
                    "content": (
                        f"Warning: Only {remaining} turn(s) remaining. "
                        "Provide a final answer now."
                    ),
                })

            final_response, tool_results = await llm_processor._process_llm_iteration(
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
            f"Reached maximum iterations ({self.max_iterations}) "
            f"without getting a final response."
        )
        logger.error(error_msg)
        if db_ops:
            await db_ops.save_message(user_id, chat_id, 0, "system", error_msg)
        return error_msg