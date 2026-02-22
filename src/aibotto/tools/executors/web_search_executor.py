"""
Web search executor for web search functionality.
"""

import asyncio
import json
import logging
from typing import Any

from ...db.operations import DatabaseOperations
from ..base import ToolExecutor

logger = logging.getLogger(__name__)


class WebSearchExecutor(ToolExecutor):
    """Executor for web search functionality."""

    async def execute(self, arguments: str, user_id: int = 0, db_ops: DatabaseOperations | None = None, chat_id: int = 0) -> str:
        """Execute web search with given arguments."""
        try:
            # Parse arguments
            args = json.loads(arguments)
            
            query = args.get("query", "")
            num_results = args.get("num_results", 5)
            days_ago = args.get("days_ago")

            if not query:
                raise ValueError("Query is required")

            logger.info(f"Performing web search for user {user_id}: {query}")

            # Import search function
            from ..web_search import search_web
            
            result = await search_web(
                query=query,
                num_results=num_results,
                days_ago=days_ago,
            )

            logger.info(
                f"Web search result for user {user_id}: {result[:200]}..."
            )

            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", result)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing web search arguments: {e}")
            error_result = f"Error parsing arguments: {str(e)}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            error_result = f"Error performing web search: {str(e)}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result