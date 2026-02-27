"""
Unit tests for web fetch link citation functionality.
"""

from unittest.mock import patch

import pytest

from src.aibotto.tools.web_fetch import WebFetchTool, fetch_webpage


@pytest.fixture
def web_fetch_tool() -> WebFetchTool:
    """Create a WebFetchTool instance for testing."""
    return WebFetchTool()


class TestLinkCitations:
    """Test cases for link citation formatting and filtering."""

    @pytest.mark.asyncio
    async def test_citations_included_by_default(self, web_fetch_tool):
        """Test that citations are included by default."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="A test page">
            </head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>This is a test paragraph with substantial content. It has <a href="https://example.com">a link</a> in it. The paragraph continues to provide enough text for extraction.</p>
                    <p>This is a second paragraph to ensure the page has enough content for proper extraction by trafilatura.</p>
                </article>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, "_fetch_url_with_retry", return_value=(html_content, "")
        ):
            result = await web_fetch_tool.fetch("https://example.com", no_citations=False)

        assert "[a link](https://example.com)" in result["content"]
        assert result["title"] == "Test Page"

    @pytest.mark.asyncio
    async def test_no_citations_removes_links(self, web_fetch_tool):
        """Test that no_citations=True removes all links."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>This is a test paragraph with <a href="https://example.com">a link</a>. This is additional content to ensure extraction.</p>
                </article>
                <p>Second paragraph for better extraction result.</p>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, "_fetch_url_with_retry", return_value=(html_content, "")
        ):
            result = await web_fetch_tool.fetch("https://example.com", no_citations=True)

        assert "[a link](https://example.com)" not in result["content"]
        assert "a link" in result["content"]
        assert "https://example.com" not in result["content"]

    @pytest.mark.asyncio
    async def test_filters_anchor_only_links(self, web_fetch_tool):
        """Test that anchor-only links (#section) are filtered out."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>You can <a href="#top">Return to top</a> or <a href="#section">go to section</a>. This is more text.</p>
                    <p>Second paragraph to aid extraction.</p>
                </article>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, "_fetch_url_with_retry", return_value=(html_content, "")
        ):
            result = await web_fetch_tool.fetch("https://example.com")

        assert "[Return to top]" not in result["content"]
        assert "Return to top" in result["content"]
        assert "#" not in result["content"]

    @pytest.mark.asyncio
    async def test_filters_javascript_links(self, web_fetch_tool):
        """Test that javascript: links are filtered out."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>You can <a href="javascript:void(0)">Click here</a> or <a href="javascript:alert('test')">click there</a>. Additional content here.</p>
                    <p>More content for extraction purposes.</p>
                </article>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, "_fetch_url_with_retry", return_value=(html_content, "")
        ):
            result = await web_fetch_tool.fetch("https://example.com")

        assert "[Click here](javascript:void(0))" not in result["content"]
        assert "[click there](javascript:alert('test'))" not in result["content"]
        assert "javascript:" not in result["content"]

    @pytest.mark.asyncio
    async def test_filters_protocol_links(self, web_fetch_tool):
        """Test that mailto: tel: and other protocol links are filtered."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>Contact <a href="mailto:test@example.com">us by email</a> or call <a href="tel:123-456">us by phone</a>. More text follows.</p>
                    <p>Additional content paragraph.</p>
                </article>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, "_fetch_url_with_retry", return_value=(html_content, "")
        ):
            result = await web_fetch_tool.fetch("https://example.com")

        assert "[us by email](mailto:test@example.com)" not in result["content"]
        assert "[us by phone](tel:123-456)" not in result["content"]
        assert "mailto:" not in result["content"]
        assert "tel:" not in result["content"]

    @pytest.mark.asyncio
    async def test_keeps_http_links(self, web_fetch_tool):
        """Test that full HTTP/HTTPS links are kept."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>You can visit <a href="http://example.com">HTTP site</a> or <a href="https://secure.com">HTTPS site</a>. Continue reading.</p>
                    <p>This is the second paragraph.</p>
                </article>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, "_fetch_url_with_retry", return_value=(html_content, "")
        ):
            result = await web_fetch_tool.fetch("https://example.com")

        assert "[HTTP site](http://example.com)" in result["content"]
        assert "[HTTPS site](https://secure.com)" in result["content"]

    @pytest.mark.asyncio
    async def test_keeps_urls_with_fragments(self, web_fetch_tool):
        """Test that full URLs with fragments are kept."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>You should <a href="https://example.com/page#section">Go to section</a> for more information. Keep reading.</p>
                    <p>Second paragraph for extraction.</p>
                </article>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, "_fetch_url_with_retry", return_value=(html_content, "")
        ):
            result = await web_fetch_tool.fetch("https://example.com")

        assert "[Go to section](https://example.com/page#section)" in result["content"]

    @pytest.mark.asyncio
    async def test_resolves_relative_urls(self, web_fetch_tool):
        """Test that relative URLs are resolved to absolute."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>Visit <a href="/about">About page</a> and <a href="/page1">Page one</a>. More text continues here.</p>
                    <p>Additional paragraph for extraction.</p>
                </article>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, "_fetch_url_with_retry", return_value=(html_content, "")
        ):
            result = await web_fetch_tool.fetch("https://example.com/mypage.html")

        assert "[About page](https://example.com/about)" in result["content"]
        assert "[Page one](https://example.com/page1)" in result["content"]

    @pytest.mark.asyncio
    async def test_multiple_links_in_paragraph(self, web_fetch_tool):
        """Test handling multiple links in a single paragraph."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title><meta name="description" content="Test"></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>Visit <a href="https://a.com">site A</a>, then <a href="https://b.com">site B</a>, and <a href="#skip">anchor text</a>. More text here.</p>
                    <p>Second paragraph for better extraction</p>
                </article>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, "_fetch_url_with_retry", return_value=(html_content, "")
        ):
            result = await web_fetch_tool.fetch("https://example.com")

        assert "[site A](https://a.com)" in result["content"]
        assert "[site B](https://b.com)" in result["content"]
        assert "[anchor text](#skip)" not in result["content"]
        assert "anchor text" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_webpage_function_with_citations(self):
        """Test the fetch_webpage function includes citations."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>This is a paragraph with <a href="https://example.com">a link</a> inside it. Additional text follows.</p>
                    <p>Second paragraph for extraction.</p>
                </article>
            </body>
        </html>
        """

        with patch(
            "src.aibotto.tools.web_fetch.web_fetch_tool._fetch_url_with_retry",
            return_value=(html_content, ""),
        ):
            result = await fetch_webpage("https://example.com")

        assert "[a link](https://example.com)" in result
        assert "# Test Page" in result

    @pytest.mark.asyncio
    async def test_fetch_webpage_function_no_citations(self):
        """Test the fetch_webpage function with no_citations=True."""
        html_content = """
        <!DOCTYPE html>
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Test Page</h1>
                    <p>This is a paragraph with <a href="https://example.com">a link</a> inside. Additional content.</p>
                    <p>Second paragraph helps with extraction.</p>
                </article>
            </body>
        </html>
        """

        with patch(
            "src.aibotto.tools.web_fetch.web_fetch_tool._fetch_url_with_retry",
            return_value=(html_content, ""),
        ):
            result = await fetch_webpage("https://example.com", no_citations=True)

        assert "[a link](https://example.com)" not in result
        assert "a link" in result
        assert "# Test Page" in result

    def test_filter_unwanted_links_empty_string(self, web_fetch_tool):
        """Test filter_unwanted_links with empty string."""
        result = web_fetch_tool._filter_unwanted_links("")
        assert result == ""

    def test_filter_unwanted_links_no_links(self, web_fetch_tool):
        """Test filter_unwanted_links with text but no links."""
        result = web_fetch_tool._filter_unwanted_links("Just some text with no links")
        assert result == "Just some text with no links"

    def test_filter_unwanted_links_anchor_only(self, web_fetch_tool):
        """Test filter_unwanted_links with anchor-only links."""
        text = "Go to [top](#top) or [section](#section)"
        result = web_fetch_tool._filter_unwanted_links(text)
        assert result == "Go to top or section"

    def test_filter_unwanted_links_javascript(self, web_fetch_tool):
        """Test filter_unwanted_links with javascript links."""
        text = "Click [here](javascript:void(0)) or [there](javascript:alert)"
        result = web_fetch_tool._filter_unwanted_links(text)
        assert result == "Click here or there"

    def test_filter_unwanted_links_mailto_tel(self, web_fetch_tool):
        """Test filter_unwanted_links with mailto and tel links."""
        text = "Email [us](mailto:test@example.com) or call [us](tel:123)"
        result = web_fetch_tool._filter_unwanted_links(text)
        assert result == "Email us or call us"

    def test_filter_unwanted_links_http_https(self, web_fetch_tool):
        """Test filter_unwanted_links with HTTP/HTTPS links (should keep)."""
        text = "Visit [HTTP site](http://example.com) or [HTTPS site](https://secure.com)"
        result = web_fetch_tool._filter_unwanted_links(text)
        assert result == text  # Should be unchanged

    def test_filter_unwanted_links_mixed(self, web_fetch_tool):
        """Test filter_unwanted_links with mix of link types."""
        text = "Visit [good](https://example.com), skip [anchor](#top), [bad javascript](javascript:x), [mail](mailto:test@example.com)"
        result = web_fetch_tool._filter_unwanted_links(text)
        assert "[good](https://example.com)" in result
        assert "[anchor](#top)" not in result
        assert "[bad javascript](javascript:x)" not in result
        assert "[mail](mailto:test@example.com)" not in result
        assert "anchor" in result
        assert "bad javascript" in result
        assert "mail" in result
