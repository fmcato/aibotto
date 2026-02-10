"""
Web fetch tool for extracting readable content from URLs.
"""

import logging
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
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    async def fetch(
        self,
        url: str,
        max_length: int | None = None,
        include_links: bool = False
    ) -> dict[str, Any]:
        """
        Fetch a URL and extract readable text content.

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

        try:
            html = await self._fetch_url(url)
            extracted = self._extract_content(html, url, include_links)

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

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise RuntimeError(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise RuntimeError(f"Failed to fetch URL: {str(e)}")

    async def _fetch_url(self, url: str) -> str:
        """Fetch URL content with proper headers and timeout."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url, headers=headers, raise_for_status=True
            ) as response:
                # Check content type
                content_type = response.headers.get("Content-Type", "")
                supported_types = ["text/html", "application/xhtml"]
                if not any(ct in content_type for ct in supported_types):
                    raise RuntimeError(
                        f"Unsupported content type: {content_type}. "
                        "Only HTML pages are supported."
                    )

                return await response.text()

    def _extract_content(
        self,
        html: str,
        url: str,
        include_links: bool
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

    async def close(self) -> None:
        """Close any resources."""
        pass


# Create a global instance
web_fetch_tool = WebFetchTool()


async def fetch_webpage(
    url: str,
    max_length: int | None = None,
    include_links: bool = False
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
        output_parts = [
            f"# {result['title']}",
            f"URL: {result['url']}",
        ]

        if result["metadata"].get("description"):
            output_parts.append(f"Description: {result['metadata']['description']}")

        if result["metadata"].get("author"):
            output_parts.append(f"Author: {result['metadata']['author']}")

        output_parts.append("")  # Blank line before content
        output_parts.append(result["content"])

        if result.get("truncated"):
            output_parts.append(
                f"\n[Content truncated at {result['content_length']} characters]"
            )

        return "\n".join(output_parts)

    except ValueError as e:
        logger.error(f"Invalid URL: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in fetch_webpage tool: {e}")
        return f"Error fetching webpage: {str(e)}"
