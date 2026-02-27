"""
Web fetch tool for extracting readable content from URLs.
"""

import asyncio
import logging
import random
import xml.etree.ElementTree as ET
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
                content_result = await self._fetch_url_with_retry(url, attempt)
                html, content_type = content_result
                extracted = self._extract_content(html, url, include_links, content_type)
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

    async def _fetch_url_with_retry(self, url: str, attempt: int) -> tuple[str, str]:
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
                supported_types = ["text/html", "application/xhtml", "application/rss+xml", 
                                 "text/xml", "application/xml"]

                if not any(ct in content_type for ct in supported_types):
                    if self.strict_content_type:
                        raise RuntimeError(
                            f"Unsupported content type: {content_type}. "
                            "Only HTML pages and RSS/XML feeds are supported."
                        )
                    else:
                        # If not strict, try to process anyway but log a warning
                        logger.warning(
                            f"Unsupported content type '{content_type}' for "
                            f"{url}, attempting to process anyway"
                        )

                return await response.text(), content_type

    def _is_rss_feed(self, content: str, content_type: str = "") -> bool:
        """Check if content is an RSS feed."""
        # Check by content type
        if content_type:
            content_type_lower = content_type.lower()
            if any(ct in content_type_lower for ct in ["application/rss+xml", "text/xml", "application/xml"]):
                # Need to verify it's actually RSS by checking the content
                try:
                    root = ET.fromstring(content)
                    # Check for RSS or Atom root elements
                    return root.tag in ["rss", "feed", "rdf:RDF"]
                except ET.ParseError:
                    pass
        
        # Check by content structure (common RSS patterns)
        try:
            # Look for common RSS elements
            lower_content = content.lower()
            rss_indicators = [
                "<rss", "<channel>", "<item>", "<atom:", 
                "<feed>", "<entry>", "xmlns:rdf=", "<rdf:rdf"
            ]
            return any(indicator in lower_content for indicator in rss_indicators)
        except Exception:
            return False
    
    def _extract_content(
        self,
        html: str,
        url: str,
        include_links: bool,
        content_type: str = "",
    ) -> dict[str, Any]:
        """Extract readable content from HTML or RSS feed."""
        # Check if this is an RSS feed first
        if self._is_rss_feed(html, content_type):
            return self._extract_rss_content(html, url)
        
        # Regular HTML content extraction
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
    
    def _extract_rss_content(self, content: str, url: str) -> dict[str, Any]:
        """Extract content from RSS/Atom feed."""
        try:
            root = ET.fromstring(content)
            
            # Handle namespace-qualified tags
            tag_name = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            
            # Handle different feed types
            if tag_name == "rss":
                return self._extract_rss_2_0(root, url)
            elif tag_name == "feed":
                return self._extract_atom(root, url)
            elif tag_name == "RDF":  # rdf:RDF
                return self._extract_rss_1_0(root, url)
            else:
                # Try to find feed elements anywhere
                if root.find(".//channel") is not None:
                    return self._extract_rss_2_0(root, url)
                elif root.find(".//entry") is not None:
                    return self._extract_atom(root, url)
        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS feed: {e}")
        
        # Fallback to basic text extraction if parsing fails
        return {
            "title": "RSS Feed (parse failed)",
            "content": content[:5000],  # Limit content for failed parses
            "url": url,
            "metadata": {
                "description": "RSS feed content (parsing may be incomplete)",
                "author": None,
                "published_date": None,
            },
        }
    
    def _extract_rss_2_0(self, root: ET.Element, url: str) -> dict[str, Any]:
        """Extract content from RSS 2.0 feed."""
        channel = root.find("channel")
        title = channel.findtext("title", "").strip() if channel is not None else "RSS Feed"
        description = channel.findtext("description", "").strip() if channel is not None else ""
        
        items = []
        item_count = 0
        max_items = 20  # Limit number of items to fetch
        
        for item in root.findall(".//item"):
            if item_count >= max_items:
                break
            
            item_title = item.findtext("title", "").strip()
            item_desc = item.findtext("description", "").strip()
            item_link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            
            # Clean HTML from description
            if item_desc:
                import re
                item_desc = re.sub(r'<[^>]+>', ' ', item_desc)
                item_desc = ' '.join(item_desc.split())  # Clean whitespace
            
            item_text = f"\n📌 {item_title or 'No title'}"
            if item_link:
                item_text += f"\n   Link: {item_link}"
            if pub_date:
                item_text += f"\n   Date: {pub_date}"
            if item_desc:
                item_text += f"\n   Summary: {item_desc[:500]}{'...' if len(item_desc) > 500 else ''}"
            
            items.append(item_text)
            item_count += 1
        
        content = f"Feed Description: {description}\n\nLatest Entries:\n" + "\n\n".join(items)
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "metadata": {
                "description": description,
                "author": None,
                "published_date": None,
            },
        }
    
    def _extract_atom(self, root: ET.Element, url: str) -> dict[str, Any]:
        """Extract content from Atom feed."""
        # Atom namespace handling
        if '}' in root.tag:
            # Extract namespace from the root tag
            ns_uri = root.tag.split('}')[0][1:]
            ns = {"atom": ns_uri}
        else:
            ns = {}
        
        # Try both namespaced and non-namespaced lookups
        title = (root.findtext("title", "") or 
                 root.findtext("atom:title", "", ns)).strip() or "Atom Feed"
        subtitle = (root.findtext("subtitle", "") or 
                   root.findtext("atom:subtitle", "", ns)).strip() or ""
        
        entries = []
        entry_count = 0
        max_entries = 20  # Limit number of entries to fetch
        
        entry_list = root.findall(".//entry") if not ns else root.findall(".//atom:entry", ns)
        for entry in entry_list:
            if entry_count >= max_entries:
                break
            
            entry_title = (entry.findtext("title", "") or entry.findtext("atom:title", "", ns)).strip()
            
            # Link element in Atom is an attribute
            link_elem = entry.find("link") if not ns else entry.find("atom:link", ns)
            entry_link = link_elem.get("href", "").strip() if link_elem is not None else ""
            
            entry_summary = (entry.findtext("summary", "") or entry.findtext("atom:summary", "", ns)).strip()
            entry_content = (entry.findtext("content", "") or entry.findtext("atom:content", "", ns)).strip()
            entry_updated = (entry.findtext("updated", "") or entry.findtext("atom:updated", "", ns)).strip()
            
            # Use summary or content, clean HTML if necessary
            entry_text = f"\n📌 {entry_title or 'No title'}"
            if entry_link:
                entry_text += f"\n   Link: {entry_link}"
            if entry_updated:
                entry_text += f"\n   Date: {entry_updated}"
            
            # Prefer summary, fallback to content, limit length
            text_content = entry_summary or entry_content or ""
            if text_content:
                import re
                text_content = re.sub(r'<[^>]+>', ' ', text_content)
                text_content = ' '.join(text_content.split())
                text_content = text_content[:500] + ('...' if len(text_content) > 500 else '')
                entry_text += f"\n   Summary: {text_content}"
            
            entries.append(entry_text)
            entry_count += 1
        
        content = f"Feed Description: {subtitle or title}\n\nLatest Entries:\n" + "\n\n".join(entries)
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "metadata": {
                "description": subtitle or title,
                "author": None,
                "published_date": None,
            },
        }
    
    def _extract_rss_1_0(self, root: ET.Element, url: str) -> dict[str, Any]:
        """Extract content from RSS 1.0 feed."""
        # RSS 1.0 uses RDF
        channel = root.find(".//channel")
        title = channel.findtext("title", "").strip() if channel is not None else "RSS 1.0 Feed"
        description = channel.findtext("description", "").strip() if channel is not None else ""
        
        items = []
        item_count = 0
        max_items = 20
        
        for item in root.findall(".//item"):
            if item_count >= max_items:
                break
            
            item_title = item.findtext("title", "").strip()
            item_desc = item.findtext("description", "").strip()
            item_link = item.findtext("link", "").strip()
            
            # Clean HTML from description
            if item_desc:
                import re
                item_desc = re.sub(r'<[^>]+>', ' ', item_desc)
                item_desc = ' '.join(item_desc.split())
            
            item_text = f"\n📌 {item_title or 'No title'}"
            if item_link:
                item_text += f"\n   Link: {item_link}"
            if item_desc:
                item_text += f"\n   Summary: {item_desc[:500]}{'...' if len(item_desc) > 500 else ''}"
            
            items.append(item_text)
            item_count += 1
        
        content = f"Feed Description: {description}\n\nLatest Entries:\n" + "\n\n".join(items)
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "metadata": {
                "description": description,
                "author": None,
                "published_date": None,
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

