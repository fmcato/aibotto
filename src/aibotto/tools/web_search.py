"""
Web search tool implementation using DuckDuckGo API.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import aiohttp

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Web search tool using DuckDuckGo API with content extraction."""

    def __init__(self):
        self.base_url = "https://api.duckduckgo.com/"
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def search(
        self,
        query: str,
        num_results: int = 5,
        days_ago: Optional[int] = None,
        safe_search: str = "moderate"
    ) -> List[Dict[str, Any]]:
        """
        Search the web using DuckDuckGo API with content extraction.
        
        Args:
            query: Search query
            num_results: Maximum number of results to return (1-10)
            days_ago: Filter results from last N days (None for no filter)
            safe_search: Safe search level ('off', 'moderate', 'strict')
        
        Returns:
            List of search results with extracted content
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        if num_results < 1 or num_results > 10:
            raise ValueError("Number of results must be between 1 and 10")

        # Build DuckDuckGo API URL
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }

        try:
            session = await self._get_session()
            
            # Make API request
            async with session.get(self.base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

            # Extract basic search results
            results = []
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", ""),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", ""),
                    "source": "DuckDuckGo"
                })

            # Add related topics as additional results
            related_topics = data.get("RelatedTopics", [])
            for topic in related_topics[:num_results]:
                if "Text" in topic and "FirstURL" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "source": "DuckDuckGo"
                    })

            # Limit results and filter by date if specified
            if days_ago is not None:
                filtered_results = []
                cutoff_date = datetime.now() - timedelta(days=days_ago)
                
                for result in results:
                    if _is_content_recent(result["url"], cutoff_date):
                        filtered_results.append(result)
                
                results = filtered_results

            # Limit to requested number of results
            return results[:num_results]

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
            session = await self._get_session()
            
            # Add user agent to avoid blocking
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with session.get(url, headers=headers, timeout=20) as response:
                response.raise_for_status()
                html = await response.text()

            # Parse HTML and extract content
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
            text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines to single newline
            
            # Limit length
            if len(text) > max_length:
                text = text[:max_length] + "... [content truncated]"
            
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return f"Failed to extract content: {str(e)}"

    async def search_with_content(
        self,
        query: str,
        num_results: int = 5,
        days_ago: Optional[int] = None,
        safe_search: str = "moderate",
        extract_content: bool = True
    ) -> List[Dict[str, Any]]:
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
        # Get basic search results
        results = await self.search(query, num_results, days_ago, safe_search)
        
        if extract_content and results:
            # Extract content from each result
            content_tasks = []
            for result in results:
                content_tasks.append(self.extract_content(result["url"]))
            
            contents = await asyncio.gather(*content_tasks, return_exceptions=True)
            
            # Add content to results
            for i, (result, content) in enumerate(zip(results, contents)):
                if isinstance(content, Exception):
                    result["content"] = f"Failed to extract content: {str(content)}"
                else:
                    result["content"] = content
        
        return results

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None


# Create a global instance
web_search_tool = WebSearchTool()


async def search_web(
    query: str,
    num_results: int = 5,
    days_ago: Optional[int] = None,
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


def _is_content_recent(url: str, cutoff_date: datetime) -> bool:
    """
    Check if content from a URL is recent (simplified implementation).
    Note: This is a basic implementation - in production, you might want to
    use web archives or other methods to check content dates.
    """
    # For now, we'll assume all content is recent since DuckDuckGo doesn't
    # provide date information in the basic API
    return True