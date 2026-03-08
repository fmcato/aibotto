"""
Web fetch executor for fetching webpage content.
"""

from typing import Any

from ...tools.base import ToolExecutor, ToolExecutionError


class WebFetchExecutor(ToolExecutor):
    """Executor for web page fetching functionality."""

    async def _do_execute(
        self, args: dict, user_id: int, chat_id: int = 0, db_ops: Any = None
    ) -> str:
        """Execute web fetch with given arguments.

        Args:
            args: Parsed arguments with 'url', 'max_length', and 'no_citations' fields
            user_id: User ID for logging
            chat_id: Chat ID for database operations

        Returns:
            Webpage content or error message

        Raises:
            ToolExecutionError: If URL is not provided
        """
        url = args.get("url", "")
        max_length = args.get("max_length")
        no_citations = args.get("no_citations", False)

        if not url:
            raise ToolExecutionError("URL is required")

        self.logger.info(f"Fetching webpage for user {user_id}: {url}")

        from ...tools.web_fetch import fetch_webpage

        result = await fetch_webpage(
            url=url,
            max_length=max_length,
            no_citations=no_citations,
        )

        self.logger.info(f"Web fetch result for user {user_id}: {result[:200]}...")

        return result
