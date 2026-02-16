"""
Unit tests for web fetch tool.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aibotto.tools.web_fetch import WebFetchTool, fetch_webpage


class TestWebFetchTool:
    """Test cases for WebFetchTool class."""

    @pytest.fixture
    def web_fetch_tool(self):
        """Create a WebFetchTool instance for testing."""
        return WebFetchTool()

    def test_init(self, web_fetch_tool):
        """Test WebFetchTool initialization."""
        assert web_fetch_tool.max_content_length == 10000
        assert "Mozilla" in web_fetch_tool._get_random_user_agent()
        assert web_fetch_tool.max_retries == 3
        assert web_fetch_tool.retry_delay == 1.0

    @pytest.mark.asyncio
    async def test_fetch_empty_url(self, web_fetch_tool):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await web_fetch_tool.fetch("")

    @pytest.mark.asyncio
    async def test_fetch_invalid_url_scheme(self, web_fetch_tool):
        """Test that invalid URL scheme raises ValueError."""
        with pytest.raises(ValueError, match="must start with http"):
            await web_fetch_tool.fetch("ftp://example.com")

    @pytest.mark.asyncio
    async def test_fetch_success(self, web_fetch_tool):
        """Test successful fetch and content extraction."""
        html_content = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
                <meta name="author" content="Test Author">
            </head>
            <body>
                <main>
                    <h1>Main Heading</h1>
                    <p>This is a test paragraph with enough text to be included.</p>
                    <p>Another paragraph here for testing purposes.</p>
                </main>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, '_fetch_url_with_retry', return_value=html_content
        ):
            result = await web_fetch_tool.fetch("https://example.com")

            # Trafailatura extracts title from metadata or first heading
            assert result["title"] in ["Test Page", "Main Heading"]
            assert result["url"] == "https://example.com"
            assert "test paragraph" in result["content"].lower()
            assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_fetch_truncation(self, web_fetch_tool):
        """Test that long content is truncated."""
        long_paragraph = "<p>" + "x" * 15000 + "</p>"
        html_content = f"""
        <html>
            <head><title>Long Page</title></head>
            <body><main>{long_paragraph}</main></body>
        </html>
        """

        with patch.object(
            web_fetch_tool, '_fetch_url_with_retry', return_value=html_content
        ):
            result = await web_fetch_tool.fetch(
                "https://example.com", max_length=1000
            )

            assert result["truncated"] is True
            assert result["content_length"] <= 1100  # Some buffer for truncation msg

    @pytest.mark.asyncio
    async def test_fetch_with_links(self, web_fetch_tool):
        """Test fetching with link extraction."""
        html_content = """
        <html>
            <head><title>Page with Links</title></head>
            <body>
                <main>
                    <p>Check out <a href="https://example.org">this link</a> for more.</p>
                </main>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, '_fetch_url_with_retry', return_value=html_content
        ):
            result = await web_fetch_tool.fetch(
                "https://example.com", include_links=True
            )

            assert "https://example.org" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_removes_unwanted_elements(self, web_fetch_tool):
        """Test that scripts, styles, nav, etc. are removed."""
        html_content = """
        <html>
            <head>
                <title>Test</title>
                <script>var x = 1;</script>
                <style>.foo { color: red; }</style>
            </head>
            <body>
                <nav>Navigation here</nav>
                <header>Header content</header>
                <footer>Footer content</footer>
                <aside>Sidebar</aside>
                <main>
                    <p>Main content paragraph here.</p>
                </main>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, '_fetch_url_with_retry', return_value=html_content
        ):
            result = await web_fetch_tool.fetch("https://example.com")

            assert "var x" not in result["content"]
            assert "color: red" not in result["content"]
            assert "Navigation here" not in result["content"]
            assert "Header content" not in result["content"]
            assert "Footer content" not in result["content"]
            assert "Main content paragraph" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_finds_article_element(self, web_fetch_tool):
        """Test that article element is found as main content."""
        html_content = """
        <html>
            <head><title>Article Test</title></head>
            <body>
                <article>
                    <h1>Article Title</h1>
                    <p>This is article content that should be extracted.</p>
                </article>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, '_fetch_url_with_retry', return_value=html_content
        ):
            result = await web_fetch_tool.fetch("https://example.com")

            assert "Article Title" in result["content"]
            assert "article content" in result["content"].lower()

    @pytest.mark.asyncio
    async def test_fetch_formats_headings(self, web_fetch_tool):
        """Test that headings are extracted."""
        html_content = """
        <html>
            <head><title>Heading Test</title></head>
            <body>
                <main>
                    <h1>Heading One</h1>
                    <h2>Heading Two</h2>
                    <h3>Heading Three</h3>
                    <p>Paragraph content here.</p>
                </main>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, '_fetch_url_with_retry', return_value=html_content
        ):
            result = await web_fetch_tool.fetch("https://example.com")

            # Trafailatura extracts headings as part of content
            assert "Heading One" in result["content"]
            assert "Heading Two" in result["content"]
            assert "Heading Three" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_formats_lists(self, web_fetch_tool):
        """Test that list items are formatted with bullets."""
        html_content = """
        <html>
            <head><title>List Test</title></head>
            <body>
                <main>
                    <ul>
                        <li>First item in the list</li>
                        <li>Second item in the list</li>
                    </ul>
                </main>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, '_fetch_url_with_retry', return_value=html_content
        ):
            result = await web_fetch_tool.fetch("https://example.com")

            assert "- First item in the list" in result["content"]
            assert "- Second item in the list" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_formats_blockquotes(self, web_fetch_tool):
        """Test that blockquotes are extracted."""
        html_content = """
        <html>
            <head><title>Quote Test</title></head>
            <body>
                <main>
                    <blockquote>This is a quoted text block.</blockquote>
                </main>
            </body>
        </html>
        """

        with patch.object(
            web_fetch_tool, '_fetch_url_with_retry', return_value=html_content
        ):
            result = await web_fetch_tool.fetch("https://example.com")

            # Trafailatura extracts blockquote content
            assert "This is a quoted text block" in result["content"]


class TestFetchWebpage:
    """Test cases for fetch_webpage tool function."""

    @pytest.mark.asyncio
    async def test_fetch_webpage_success(self):
        """Test successful webpage fetch."""
        html_content = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="A test page">
            </head>
            <body>
                <main>
                    <p>Test content paragraph here.</p>
                </main>
            </body>
        </html>
        """

        with patch(
            'src.aibotto.tools.web_fetch.web_fetch_tool'
        ) as mock_tool:
            mock_tool.fetch = AsyncMock(return_value={
                "title": "Test Page",
                "content": "Test content paragraph here.",
                "url": "https://example.com",
                "metadata": {"description": "A test page", "author": None},
                "truncated": False,
                "content_length": 28,
            })

            result = await fetch_webpage("https://example.com")

            assert "# Test Page" in result
            assert "https://example.com" in result
            assert "Test content paragraph" in result

    @pytest.mark.asyncio
    async def test_fetch_webpage_invalid_url(self):
        """Test fetch_webpage with invalid URL."""
        result = await fetch_webpage("not-a-url")

        assert "Error:" in result

    @pytest.mark.asyncio
    async def test_fetch_webpage_with_author(self):
        """Test fetch_webpage includes author when available."""
        with patch(
            'src.aibotto.tools.web_fetch.web_fetch_tool'
        ) as mock_tool:
            mock_tool.fetch = AsyncMock(return_value={
                "title": "Article",
                "content": "Content here.",
                "url": "https://example.com",
                "metadata": {
                    "description": "Desc",
                    "author": "John Doe"
                },
                "truncated": False,
                "content_length": 12,
            })

            result = await fetch_webpage("https://example.com")

            assert "Author: John Doe" in result

    @pytest.mark.asyncio
    async def test_fetch_webpage_truncated(self):
        """Test fetch_webpage shows truncation notice."""
        with patch(
            'src.aibotto.tools.web_fetch.web_fetch_tool'
        ) as mock_tool:
            mock_tool.fetch = AsyncMock(return_value={
                "title": "Long Article",
                "content": "x" * 10000,
                "url": "https://example.com",
                "metadata": {"description": None, "author": None},
                "truncated": True,
                "content_length": 10000,
            })

            result = await fetch_webpage("https://example.com")

            assert "truncated" in result.lower()


class TestFetchUrl:
    """Test cases for _fetch_url_with_retry method."""

    @pytest.fixture
    def web_fetch_tool(self):
        """Create a WebFetchTool instance for testing."""
        return WebFetchTool()

    @pytest.mark.asyncio
    async def test_fetch_url_non_html_content(self, web_fetch_tool):
        """Test that non-HTML content raises error."""
        mock_response = MagicMock()
        mock_response.headers.get.return_value = "application/pdf"
        mock_response.text = AsyncMock(return_value="PDF content")
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(RuntimeError, match="Unsupported content type"):
                await web_fetch_tool._fetch_url_with_retry("https://example.com/doc.pdf", 0)

    @pytest.mark.asyncio
    async def test_fetch_url_html_content(self, web_fetch_tool):
        """Test that HTML content is fetched successfully."""
        html = "<html><body>Test</body></html>"
        mock_response = MagicMock()
        mock_response.headers.get.return_value = "text/html"
        mock_response.text = AsyncMock(return_value=html)
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await web_fetch_tool._fetch_url_with_retry("https://example.com", 0)

            assert result == html
