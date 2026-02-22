"""
Web fetch executor for fetching webpage content.
"""

import json
import logging

from ...db.operations import DatabaseOperations
from ..base import ToolExecutor

logger = logging.getLogger(__name__)


class WebFetchExecutor(ToolExecutor):
    """Executor for web page fetching functionality."""

    async def execute(
        self,
        arguments: str,
        user_id: int = 0,
        db_ops: DatabaseOperations | None = None,
        chat_id: int = 0,
    ) -> str:
        """Execute web fetch with given arguments."""
        try:
            # Parse arguments
            args = json.loads(arguments)

            url = args.get("url", "")
            max_length = args.get("max_length")
            include_links = args.get("include_links", False)

            if not url:
                raise ValueError("URL is required")

            logger.info(f"Fetching webpage for user {user_id}: {url}")

            # Import fetch function
            from ..web_fetch import fetch_webpage

            result = await fetch_webpage(
                url=url,
                max_length=max_length,
                include_links=include_links,
            )

            logger.info(
                f"Web fetch result for user {user_id}: {result[:200]}..."
            )

            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", result)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing web fetch arguments: {e}")
            error_result = f"Error parsing arguments: {str(e)}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result
        except Exception as e:
            logger.error(f"Error fetching webpage: {e}")
            error_result = f"Error fetching webpage: {str(e)}"
            if db_ops:
                await db_ops.save_message(user_id, chat_id, 0, "system", error_result)
            return error_result
