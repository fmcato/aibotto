"""
Web search tool implementation using ddgs library.
"""

import asyncio
import logging
from typing import Any

import ddgs

from ..config.settings import Config

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Web search tool using ddgs library."""

    def __init__(self) -> None:
        self.ddgs = ddgs.DDGS()
        self.timeout = Config.DDGS_TIMEOUT
        self._retry_count = 0
        self._max_retries = 3

    async def search(
        self,
        query: str,
        num_results: int = 5,
        days_ago: int | None = None,
        safe_search: str = "moderate"
    ) -> list[dict[str, Any]]:
        """
        Search the web using ddgs API.

        Args:
            query: Search query
            num_results: Maximum number of results to return (1-20)
            days_ago: Filter results from last N days (None for no filter)
            safe_search: Safe search level ('off', 'moderate', 'strict')

        Returns:
            List of search results
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        if num_results < 1 or num_results > 20:
            raise ValueError("Number of results must be between 1 and 20")

        try:
            # Prepare search parameters
            search_params = {
                "max_results": num_results,
                "region": "wt",  # Worldwide
                "safesearch": safe_search,
            }

            # Add time filter if specified
            if days_ago is not None:
                if days_ago <= 1:
                    search_params["timelimit"] = "d"
                elif days_ago <= 7:
                    search_params["timelimit"] = "w"
                elif days_ago <= 30:
                    search_params["timelimit"] = "m"
                else:
                    search_params["timelimit"] = "y"

            # Perform search using ddgs
            # Note: ddgs is synchronous, so we run it in a thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(query, **search_params))
            )

            # Convert ddgs results to our format
            formatted_results = []
            for item in results:
                result = {
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                    "source": "DuckDuckGo",
                    "published_date": None  # ddgs doesn't provide date info
                }
                formatted_results.append(result)

            # Log engine errors if they occurred (ddgs logs them at INFO level)
            if self._retry_count > 0:
                logger.info(f"Search completed after {self._retry_count} retry/ies")

            return formatted_results

        except ValueError as e:
            # Handle specific engine errors like "not enough values to unpack"
            if "not enough values to unpack" in str(e):
                logger.warning(f"Engine error during search: {e}")
                if self._retry_count < self._max_retries:
                    self._retry_count += 1
                    logger.info(
                        f"Retrying search (attempt {self._retry_count}/"
                        f"{self._max_retries})"
                    )
                    # Wait a bit before retrying to avoid overwhelming the service
                    await asyncio.sleep(1)
                    return await self.search(query, num_results, days_ago, safe_search)
                else:
                    logger.error(
                        f"Search failed after {self._retry_count} attempts "
                        f"due to engine errors"
                    )
                    raise RuntimeError(
                        f"Failed to perform web search due to engine errors: {str(e)}"
                    )
            else:
                # Other ValueError cases
                logger.error(f"Value error during web search: {e}")
                raise RuntimeError(f"Failed to perform web search: {str(e)}")

        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            raise RuntimeError(f"Failed to perform web search: {str(e)}")

    async def extract_content(self, url: str, max_length: int = 2000) -> str:
        """
        Extract and clean content from a webpage.

        Args:
            url: URL to extract content from
            max_length: Maximum length of extracted content

        Returns:
            Cleaned text content from the webpage
        """
        try:
            # For now, we'll use the snippet from ddgs results
            # In a future implementation, we could add proper content extraction
            return (
                f"Content from {url}. Full content extraction not "
                f"implemented with ddgs."
            )

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return f"Failed to extract content: {str(e)}"

    async def search_with_content(
        self,
        query: str,
        num_results: int = 5,
        days_ago: int | None = None,
        safe_search: str = "moderate",
        extract_content: bool = True
    ) -> list[dict[str, Any]]:
        """
        Perform web search and optionally extract full content from results.

        Args:
            query: Search query
            num_results: Maximum number of results to return (1-10)
            days_ago: Filter results from last N days (None for no filter)
            safe_search: Safe search level ('off', 'moderate', 'strict')
            extract_content: Whether to extract full content from results

        Returns:
            List of search results with optional extracted content
        """
        # Reset retry count for new search
        self._retry_count = 0

        # Get basic search results
        results = await self.search(query, num_results, days_ago, safe_search)

        if extract_content and results:
            # Extract content from each result
            content_tasks = []
            for result in results:
                content_tasks.append(self.extract_content(result["url"]))

            contents = await asyncio.gather(*content_tasks, return_exceptions=True)

            # Add content to results
            for _, (result, content) in enumerate(zip(results, contents, strict=True)):
                if isinstance(content, Exception):
                    result["content"] = f"Failed to extract content: {str(content)}"
                else:
                    result["content"] = content

        return results

    async def close(self) -> None:
        """Close any resources."""
        # ddgs doesn't require explicit closing
        pass


# Create a global instance
web_search_tool = WebSearchTool()


async def search_web(
    query: str,
    num_results: int = 5,
    days_ago: int | None = None,
    safe_search: str = "moderate"
) -> str:
    """
    Tool function for web search that can be called by the LLM.

    Args:
        query: Search query
        num_results: Maximum number of results to return (1-10)
        days_ago: Filter results from last N days (None for no filter)
        safe_search: Safe search level ('off', 'moderate', 'strict')

    Returns:
        Formatted string with search results
    """
    try:
        results = await web_search_tool.search_with_content(
            query=query,
            num_results=num_results,
            days_ago=days_ago,
            safe_search=safe_search,
            extract_content=True
        )

        if not results:
            return f"No search results found for query: {query}"

        # Format results for LLM
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_result = f"""
{i}. **{result.get('title', 'No title')[:100]}**
   URL: {result.get('url', 'No URL')}
   Content: {result.get('content', 'No content')[:500]}...
   Source: {result.get('source', 'Unknown')}
"""
            formatted_results.append(formatted_result.strip())

        return f"Search results for '{query}':\n\n" + "\n\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Error in search_web tool: {e}")
        return f"Error performing web search: {str(e)}"
