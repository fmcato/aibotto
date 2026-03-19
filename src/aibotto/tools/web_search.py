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

    # Engines to use as list (duckduckgo, wikipedia, yahoo, yandex, google)
    ENGINES = ["duckduckgo", "wikipedia", "yahoo", "yandex", "google"]

    def __init__(self) -> None:
        self.ddgs = ddgs.DDGS()
        self.timeout = Config.DDGS_TIMEOUT
        self._retry_count = 0
        self._max_retries = 3

    async def _search_single_engine(self, query: str, engine: str, num_results: int) -> list[dict[str, Any]]:
        """Search against a single engine and return results."""
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(query, backend=engine, max_results=num_results))
            )
            
            # Convert to standard format with engine metadata
            formatted_results = []
            for item in results:
                result = {
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                    "source": engine.title(),  # Show which engine this came from
                    "published_date": None,
                    "content": "",  # Add missing content field for compatibility
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.warning(f"Engine {engine} failed: {e}")
            raise

    async def search(
        self,
        query: str,
        num_results: int = 5,
        days_ago: int | None = None,
        safe_search: str = "moderate",
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
            search_params = self._prepare_search_params(days_ago, safe_search)
            search_params["max_results"] = num_results

            # Perform search using ddgs
            # Note: ddgs is synchronous, so we run it in a thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(
                    self.ddgs.text(query, backend=self.ENGINES, **search_params)
                ),
            )

            # Convert ddgs results to our format
            formatted_results = []
            for item in results:
                result = {
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                    "source": "DuckDuckGo",
                    "published_date": None,  # ddgs doesn't provide date info
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

    async def _search_engine_with_retry(self, query: str, engine: str, num_results: int) -> list[dict[str, Any]]:
        """Search a single engine with retry logic.
        
        Args:
            query: Search query
            engine: Search engine to use
            num_results: Number of results to request
            
        Returns:
            List of search results or empty list if all retries fail
        """
        # Calculate optimal results per engine: balance coverage vs API efficiency
        results_per_engine = min(num_results * 2, 10)  # Cap at 10 to prevent excessive requests
        
        for attempt in range(self._max_retries):
            try:
                engine_results = await self._search_single_engine(
                    query, engine, results_per_engine
                )
                return engine_results
                
            except Exception as e:
                if attempt == self._max_retries - 1:
                    logger.warning(f"Engine {engine} failed after {self._max_retries} attempts: {e}")
                    return []  # Return empty list on final failure
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
        
        return []  # Should never reach here, but defensive return

    async def search_with_cross_engine_scoring(
        self,
        query: str,
        num_results: int = 5,
        days_ago: int | None = None,
        safe_search: str = "moderate",
    ) -> list[dict[str, Any]]:
        """
        Search the web using multiple engines and rank results by cross-engine hits.

        Strategy: Fetch more results per engine to ensure good coverage, but cap to prevent
        excessive API calls. Each engine gets min(num_results * 2, 10) results.
        Engines are processed concurrently for better performance.

        Args:
            query: Search query
            num_results: Maximum number of results to return (1-20)
            days_ago: Filter results from last N days (None for no filter)
            safe_search: Safe search level ('off', 'moderate', 'strict')

        Returns:
            List of search results ranked by prevalence score
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        if num_results < 1 or num_results > 20:
            raise ValueError("Number of results must be between 1 and 20")

        working_engines = []
        all_results: list[Any] = []
        url_to_engines: dict[str, set[str]] = {}
        
        try:
            # Note: Cross-engine search doesn't use search_params to maintain compatibility
            # with single-engine search behavior
            # Create concurrent tasks for all engines with timeout
            engine_tasks = []
            for engine in self.ENGINES:
                engine_tasks.append(self._search_engine_with_retry(query, engine, num_results))
            
            # Execute all engine searches concurrently with timeout
            engine_results = await asyncio.wait_for(
                asyncio.gather(*engine_tasks, return_exceptions=True),
                timeout=30.0  # 30 second timeout for all engines
            )
            
            # Process results from each engine
            for engine, result in zip(self.ENGINES, engine_results):
                if isinstance(result, Exception):
                    logger.warning(f"Engine {engine} failed: {result}")
                    continue
                    
                if not result:  # Empty result list (all retries failed)
                    continue
                    
                # Type guard: ensure result is a list
                if not isinstance(result, list):
                    logger.warning(f"Engine {engine} returned unexpected result type: {type(result)}")
                    continue
                    
                # Engine succeeded - result should be a list of dicts
                working_engines.append(engine)
                
                for result_item in result:
                    url = result_item["url"]
                    if url not in url_to_engines:
                        url_to_engines[url] = set()
                    url_to_engines[url].add(engine)
                    all_results.append(result_item)
            
            # Calculate cross-engine scores
            scored_results: list[dict[str, Any]] = []
            for result in all_results:
                if isinstance(result, dict):
                    url = result["url"]
                    engine_count = len(url_to_engines[url])
                    
                    scored_result = {
                        **result,
                        "prevalence_score": engine_count,
                        "source_engines": list(url_to_engines[url]),
                    }
                    scored_results.append(scored_result)
            
            # Remove duplicates and rank by prevalence score
            unique_results = self._deduplicate_by_url(scored_results)
            ranked_results = sorted(unique_results, key=lambda x: x["prevalence_score"], reverse=True)
            
            logger.info(f"Search completed using {len(working_engines)} working engines")
            
            return ranked_results[:num_results]

        except Exception as e:
            logger.error(f"Error performing cross-engine search: {e}")
            raise RuntimeError(f"Failed to perform web search: {str(e)}")

    async def search_with_content(
        self,
        query: str,
        num_results: int = 5,
        days_ago: int | None = None,
        safe_search: str = "moderate",
        extract_content: bool = True,
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

        # Get basic search results using new cross-engine approach
        results = await self.search_with_cross_engine_scoring(query, num_results, days_ago, safe_search)

        if extract_content and results:
            # Extract content from each result
            content_tasks = []
            for result in results:
                content_tasks.append(self._extract_content(result["url"]))

            contents = await asyncio.gather(*content_tasks, return_exceptions=True)

            # Add content to results
            for _, (result, content) in enumerate(zip(results, contents, strict=True)):
                if isinstance(content, Exception):
                    result["content"] = f"Failed to extract content: {str(content)}"
                else:
                    result["content"] = content

        return results

    async def _extract_content(self, url: str) -> str:
        """Extract content from a URL."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    return await response.text()
        except Exception:
            # Return a more informative message but still indicate failure
            return f"Content from {url}"

    async def close(self) -> None:
        """Close any resources."""
        # ddgs doesn't require explicit closing
        pass

    def _format_results_for_display(self, results: list[dict[str, Any]]) -> str:
        """Format search results for display, supporting both old and new result formats.
        
        Handles results with or without prevalence_score and source_engines keys
        for backward compatibility between single-engine and cross-engine search.
        """
        if not results:
            return "No search results found."
            
        formatted = []
        for i, result in enumerate(results, 1):
            prevalence_text = ""
            # Defensively handle optional cross-engine scoring fields
            prevalence_score = result.get("prevalence_score", 1)
            source_engines = result.get("source_engines", [])
            
            # Add prevalence information for cross-engine results
            if prevalence_score > 1:
                engines_text = ', '.join(source_engines) if source_engines else "multiple engines"
                prevalence_text = f" (found in {prevalence_score} engines: {engines_text})"
            
            # Safely access required fields with fallbacks
            title = result.get('title', 'Untitled')[:100]
            url = result.get('url', '#')
            content = result.get('content', result.get('snippet', ''))[:500]
            source = result.get('source', 'Unknown')
            
            formatted.append(f"""
{i}. **{title}**
   URL: {url}
   Content: {content}...
   Source: {source}{prevalence_text}
""")
        return "\n".join(formatted)

    def _prepare_search_params(self, days_ago: int | None, safe_search: str) -> dict[str, Any]:
        """Prepare common search parameters."""
        search_params = {
            "region": "wt",  # Worldwide
            "safesearch": safe_search,
        }
        
        if days_ago is not None:
            if days_ago <= 1:
                search_params["timelimit"] = "d"
            elif days_ago <= 7:
                search_params["timelimit"] = "w"
            elif days_ago <= 30:
                search_params["timelimit"] = "m"
            else:
                search_params["timelimit"] = "y"
        
        return search_params

    def _deduplicate_by_url(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate results by URL."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results


# Create a global instance
web_search_tool = WebSearchTool()


async def search_web(
    query: str,
    num_results: int = 5,
    days_ago: int | None = None,
    safe_search: str = "moderate",
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
            extract_content=True,
        )

        if not results:
            return f"No search results found for query: {query}"

        # Format results using new prevalence-aware formatting
        return web_search_tool._format_results_for_display(results)

    except Exception as e:
        logger.error(f"Error in search_web tool: {e}")
        return f"Error performing web search: {str(e)}"
