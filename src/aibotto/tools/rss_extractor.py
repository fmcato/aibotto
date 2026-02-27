"""
RSS/Atom feed extraction utilities.
"""

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any

logger = logging.getLogger(__name__)


class RSSExtractor:
    """Handles extraction of content from RSS and Atom feeds."""

    def is_rss_feed(self, content: str, content_type: str = "") -> bool:
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

    def extract_rss_content(self, content: str, url: str) -> dict[str, Any]:
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
