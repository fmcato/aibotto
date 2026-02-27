"""Unit tests for RSS feed functionality in web fetch tool."""

import aiohttp
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.tools.web_fetch import WebFetchTool, fetch_webpage


class TestWebFetchRSS:
    """Test cases for RSS feed functionality in WebFetchTool."""

    @pytest.fixture
    def web_fetch_tool(self):
        """Create a WebFetchTool instance for testing."""
        return WebFetchTool()

    def test_is_rss_feed_by_content_type(self, web_fetch_tool):
        """Test RSS detection by content type."""
        rss_content = "<?xml version='1.0'?><rss version='2.0'><channel><title>Test</title></channel></rss>"
        rss_content_types = [
            "application/rss+xml",
            "text/xml; charset=utf-8",
            "application/xml"
        ]
        
        for ct in rss_content_types:
            assert web_fetch_tool._is_rss_feed(rss_content, ct) is True

    def test_is_rss_feed_by_content_structure(self, web_fetch_tool):
        """Test RSS detection by content structure."""
        # Test basic indicators
        content_with_rss = "<rss version='2.0'><channel><title>Test</title></channel></rss>"
        content_with_atom = "<feed><title>Test</title></feed>"
        content_with_rdf = "<rdf:RDF><channel>test</channel></rdf:RDF>"
        
        assert web_fetch_tool._is_rss_feed(content_with_rss) is True
        assert web_fetch_tool._is_rss_feed(content_with_atom) is True
        assert web_fetch_tool._is_rss_feed(content_with_rdf) is True

    def test_is_not_rss_feed(self, web_fetch_tool):
        """Test that non-RSS content is detected correctly."""
        html_content = "<html><body><h1>Regular HTML page</h1></body></html>"
        assert web_fetch_tool._is_rss_feed(html_content, "text/html") is False

    @pytest.mark.asyncio
    async def test_extract_rss_2_0_content(self, web_fetch_tool):
        """Test RSS 2.0 content extraction."""
        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <description>A test RSS feed</description>
                <item>
                    <title>First Item</title>
                    <description>First description</description>
                    <link>https://example.com/1</link>
                    <pubDate>Mon, 27 Feb 2026 10:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Second Item</title>
                    <description>Second description with more text</description>
                    <link>https://example.com/2</link>
                </item>
            </channel>
        </rss>"""

        result = web_fetch_tool.rss_extractor.extract_rss_content(rss_content, "https://example.com/rss")

        assert result["title"] == "Test Feed"
        assert "First Item" in result["content"]
        assert "Second Item" in result["content"]
        assert "https://example.com/1" in result["content"]

    @pytest.mark.asyncio
    async def test_extract_atom_content(self, web_fetch_tool):
        """Test Atom feed content extraction."""
        atom_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Atom Feed</title>
            <subtitle>A test atom feed</subtitle>
            <entry>
                <title>Atom Entry 1</title>
                <link href="https://example.com/atom1"/>
                <summary>First atom summary</summary>
                <updated>2026-02-27T10:00:00Z</updated>
            </entry>
        </feed>"""

        result = web_fetch_tool.rss_extractor.extract_rss_content(atom_content, "https://example.com/atom")

        assert result["title"] == "Atom Feed"
        assert "Atom Entry 1" in result["content"]
        assert "First atom summary" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_rss_feed_integration(self, web_fetch_tool):
        """Test full RSS feed fetch integration."""
        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>News Feed</title>
                <description>Latest news</description>
                <item>
                    <title>Breaking News</title>
                    <description>Something important happened</description>
                    <link>https://news.example.com/breaking</link>
                </item>
            </channel>
        </rss>"""
        
        with patch.object(
            web_fetch_tool, '_fetch_url_with_retry', 
            return_value=(rss_content, "application/rss+xml")
        ):
            result = await web_fetch_tool.fetch("https://example.com/news.rss")
        
        assert result["title"] == "News Feed"
        assert "Breaking News" in result["content"]
        assert "Something important happened" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_webpage_rss_function(self):
        """Test the fetch_webpage function with RSS."""
        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test RSS</title>
                <description>Test description</description>
                <item>
                    <title>Test Item</title>
                    <link>https://test.com/item</link>
                    <description>Test description</description>
                </item>
            </channel>
        </rss>"""
        
        with patch('src.aibotto.tools.web_fetch.web_fetch_tool') as mock_tool:
            mock_tool.fetch = AsyncMock(return_value={
                "title": "Test RSS",
                "url": "https://test.com/rss",
                "content": "Test RSS content with item",
                "metadata": {"description": "Test description"},
                "truncated": False,
                "content_length": 100
            })
            
            result = await fetch_webpage("https://test.com/rss")
            
            assert "Test RSS" in result
            assert "Test RSS content with item" in result

    @pytest.mark.asyncio
    async def test_malformed_rss_fallback(self, web_fetch_tool):
        """Test handling of malformed RSS feeds."""
        malformed_rss = "<rss><channel><title>Broken</title>"

        result = web_fetch_tool.rss_extractor.extract_rss_content(malformed_rss, "https://example.com")

        assert "parse failed" in result["title"]
        assert "Broken" in result["content"][:100]

    @pytest.mark.asyncio
    async def test_max_items_limit(self, web_fetch_tool):
        """Test that RSS items are limited to max_items."""
        # Create RSS with many items
        items_xml = ""
        for i in range(25):  # More than the max limit of 20
            items_xml += f"""
                <item>
                    <title>Item {i}</title>
                    <description>Description {i}</description>
                    <link>https://example.com/{i}</link>
                </item>"""

        rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Many Items Feed</title>
                {items_xml}
            </channel>
        </rss>"""

        result = web_fetch_tool.rss_extractor.extract_rss_content(rss_content, "https://example.com")

        # Should have at most 20 items
        item_count = result["content"].count("📌")
        assert item_count <= 20