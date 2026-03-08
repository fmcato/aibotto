"""
Web search executor for web search functionality.
"""

from typing import Any

from ...tools.base import ToolExecutor, ToolExecutionError


class WebSearchExecutor(ToolExecutor):
    """Executor for web search functionality."""

    async def _do_execute(
        self, args: dict, user_id: int, chat_id: int = 0, db_ops: Any = None
    ) -> str:
        """Execute web search with given arguments.

        Args:
            args: Parsed arguments with 'query', 'num_results', and 'days_ago' fields
            user_id: User ID for logging
            chat_id: Chat ID for database operations

        Returns:
            Search results or error message

        Raises:
            ToolExecutionError: If query is not provided
        """
        query = args.get("query", "")
        num_results = args.get("num_results", 5)
        days_ago = args.get("days_ago")

        if not query:
            raise ToolExecutionError("Query is required")

        self.logger.info(f"Performing web search for user {user_id}: {query}")

        from ...tools.web_search import search_web

        result = await search_web(
            query=query,
            num_results=num_results,
            days_ago=days_ago,
        )

        self.logger.info(f"Web search result for user {user_id}: {result[:200]}...")

        return result
