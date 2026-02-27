"""
Web fetch tool for extracting readable content from URLs.
"""

import asyncio
import logging
import random
from typing import Any

import aiohttp
import trafilatura

from ..config.settings import Config

logger = logging.getLogger(__name__)


class WebFetchTool:
    """Tool for fetching and extracting readable content from web pages."""

    def __init__(self) -> None:
        self.timeout = Config.DDGS_TIMEOUT  # Reuse timeout config
        self.max_content_length = 10000  # Max characters to return
        self.max_retries = Config.WEB_FETCH_MAX_RETRIES
        self.retry_delay = Config.WEB_FETCH_RETRY_DELAY
        self.strict_content_type = Config.WEB_FETCH_STRICT_CONTENT_TYPE

        # Multiple user agents to rotate through
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
            "Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) "
            "Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) "
            "Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/15.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 15_6 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/15.6 Mobile/15E148 Safari/604.1",
        ]

        # Common browser headers
        self.common_headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;"
                "q=0.8,application/signed-exchange;v=b3;q=0.7"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the list."""
        return random.choice(self.user_agents)

    def _get_headers(self) -> dict[str, str]:
        """Get realistic browser headers with random user agent."""
        headers = self.common_headers.copy()
        headers["User-Agent"] = self._get_random_user_agent()

        # Add Accept-Language variation
        languages = [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9",
            "en-CA,en;q=0.9",
            "en-AU,en;q=0.9",
            "en-ZA,en;q=0.9",
        ]
        headers["Accept-Language"] = random.choice(languages)

        return headers

    async def fetch(
        self,
        url: str,
        max_length: int | None = None,
        include_links: bool = False,
    ) -> dict[str, Any]:
        """
        Fetch a URL and extract readable text content with retry logic.

        Args:
            url: URL to fetch
            max_length: Maximum content length (default: 10000)
            include_links: Whether to include link URLs in output

        Returns:
            Dictionary with title, content, url, and metadata
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        # Validate URL scheme
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        max_length = max_length or self.max_content_length

        # Retry logic with exponential backoff
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                html = await self._fetch_url_with_retry(url, attempt)
                extracted = self._extract_content(html, url, include_links)
                return self._finalize_content(extracted, max_length)

            except (aiohttp.ClientError, Exception) as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    # This is the last attempt, break out to raise final error
                    break
                else:
                    await self._handle_retry_error(url, e, attempt)
        
        # All retries exhausted, raise final error
        if last_error:
            await self._handle_final_error(url, last_error)
        
        # Should never reach here, but just in case
        raise RuntimeError(
            f"Failed to fetch URL after {self.max_retries} attempts"
        )

    async def _fetch_url_with_retry(self, url: str, attempt: int) -> str:
        """Fetch URL content with proper headers and timeout, with retry logic."""
        headers = self._get_headers()

        # Add some variation to headers on different attempts to avoid detection
        if attempt > 0:
            # Add a random referer
            referers = [
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://duckduckgo.com/",
                "https://www.yahoo.com/",
                "https://www.reddit.com/",
                "https://news.ycombinator.com/",
            ]
            headers["Referer"] = random.choice(referers)

            # Add Accept-Language variation
            languages = ["en-US,en;q=0.9", "en-GB,en;q=0.9", "en-CA,en;q=0.9"]
            headers["Accept-Language"] = random.choice(languages)

            # Add some additional headers that real browsers send
            if random.random() > 0.5:
                headers["Sec-Ch-Ua"] = (
                    '"Not_A Brand";v="8", "Chromium";v="120", '
                    '"Google Chrome";v="120"'
                )
                headers["Sec-Ch-Ua-Mobile"] = "?0"
                headers["Sec-Ch-Ua-Platform"] = '"Windows"'

            # Add cookie header to simulate returning visitor
            if random.random() > 0.7:
                headers["Cookie"] = (
                    f"session_{random.randint(1000, 9999)}="
                    f"{random.randint(100000, 999999)}"
                )

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url, headers=headers, raise_for_status=True
            ) as response:
                # Check content type
                content_type = response.headers.get("Content-Type", "")
                supported_types = ["text/html", "application/xhtml"]

                if not any(ct in content_type for ct in supported_types):
                    if self.strict_content_type:
                        raise RuntimeError(
                            f"Unsupported content type: {content_type}. "
                            "Only HTML pages are supported."
                        )
                    else:
                        # If not strict, try to process anyway but log a warning
                        logger.warning(
                            f"Non-HTML content type '{content_type}' for "
                            f"{url}, attempting to process anyway"
                        )

                return await response.text()

    def _extract_content(
        self,
        html: str,
        url: str,
        include_links: bool,
    ) -> dict[str, Any]:
        """Extract readable content from HTML using trafilatura."""
        # Use trafilatura for extraction
        # include_links=True will preserve links in the output
        extracted = trafilatura.extract(
            html,
            url=url,
            include_links=include_links,
            include_comments=False,
            include_images=False,
            output_format="txt",
            favor_precision=True,  # Prefer precision over recall
        )

        if not extracted:
            # Fallback: try with less precision if nothing found
            extracted = trafilatura.extract(
                html,
                url=url,
                include_links=include_links,
                include_comments=False,
                include_images=False,
                output_format="txt",
                favor_precision=False,
            )

        content = extracted or ""

        # Extract metadata using trafilatura
        metadata = trafilatura.extract_metadata(html, default_url=url)

        title = ""
        if metadata:
            title = metadata.title or ""
        if not title:
            # Fallback to URL-derived title
            title = url.split("/")[-1] or url

        return {
            "title": title,
            "content": content.strip(),
            "url": url,
            "metadata": {
                "description": metadata.description if metadata else None,
                "author": metadata.author if metadata else None,
                "published_date": metadata.date if metadata else None,
            },
        }

    def _finalize_content(
        self, extracted: dict[str, Any], max_length: int
    ) -> dict[str, Any]:
        """Finalize content by truncating if needed and setting length."""
        # Truncate if needed
        if len(extracted["content"]) > max_length:
            extracted["content"] = (
                extracted["content"][:max_length] +
                "\n\n[Content truncated...]"
            )
            extracted["truncated"] = True
        else:
            extracted["truncated"] = False

        extracted["content_length"] = len(extracted["content"])
        return extracted

    async def _handle_final_error(self, url: str, error: Exception) -> None:
        """Handle the final error after all retry attempts."""
        error_type = "HTTP error" if isinstance(error, aiohttp.ClientError) else "Error"
        logger.error(
            f"{error_type} fetching {url} after {self.max_retries} attempts: {error}"
        )
        raise RuntimeError(
            f"Failed to fetch URL after {self.max_retries} attempts: {str(error)}"
        )

    async def _handle_retry_error(
        self, url: str, error: Exception, attempt: int
    ) -> None:
        """Handle retry error by logging and waiting with exponential backoff."""
        delay = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
        logger.warning(
            f"Attempt {attempt + 1} failed for {url}, "
            f"retrying in {delay:.2f}s: {error}"
        )
        await asyncio.sleep(delay)

    async def close(self) -> None:
        """Close any resources."""
        pass


# Create a global instance
web_fetch_tool = WebFetchTool()


async def fetch_webpage(
    url: str,
    max_length: int | None = None,
    include_links: bool = False,
) -> str:
    """
    Tool function for fetching web page content that can be called by the LLM.

    Args:
        url: URL to fetch
        max_length: Maximum content length (default: 10000 characters)
        include_links: Whether to include link URLs in output

    Returns:
        Formatted string with page content
    """
    try:
        result = await web_fetch_tool.fetch(url, max_length, include_links)

        # Format output for LLM
        output_parts = []

        output_parts = [
            f"# {result['title']}",
            f"URL: {result['url']}",
        ]

        if result["metadata"].get("description"):
            output_parts.append(
                f"Description: {result['metadata']['description']}"
            )

        if result["metadata"].get("author"):
            output_parts.append(f"Author: {result['metadata']['author']}")

        output_parts.append("")  # Blank line before content
        output_parts.append(result["content"])

        if result.get("truncated"):
            output_parts.append(
                f"\n[Content truncated at {result['content_length']} "
                f"characters]"
            )

        return "\n".join(output_parts)

    except ValueError as e:
        logger.error(f"Invalid URL: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in fetch_webpage tool: {e}")
        return f"Error fetching webpage: {str(e)}"

