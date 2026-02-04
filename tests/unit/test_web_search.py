"""
Tests for web search functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.aibotto.tools.web_search import WebSearchTool, search_web


class TestWebSearchTool:
    """Test the WebSearchTool class."""

    @pytest.fixture
    def web_search_tool(self):
        """Create a WebSearchTool instance for testing."""
        return WebSearchTool()

    @pytest.fixture
    def mock_duckduckgo_response(self):
        """Mock DuckDuckGo API response."""
        return {
            "AbstractText": "This is a test abstract about Python programming.",
            "Heading": "Python Programming",
            "AbstractURL": "https://example.com/python",
            "RelatedTopics": [
                {
                    "Text": "Python tutorial - Learn Python programming basics",
                    "FirstURL": "https://example.com/python-tutorial"
                },
                {
                    "Text": "Python documentation - Official Python docs",
                    "FirstURL": "https://docs.python.org"
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_search_basic(self, web_search_tool, mock_duckduckgo_response):
        """Test basic web search functionality."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock the API response
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value=mock_duckduckgo_response)
            mock_get.return_value.__aenter__.return_value = mock_response

            # Perform search
            results = await web_search_tool.search("Python programming", num_results=3)

            # Verify results
            assert len(results) <= 3
            assert all('title' in result for result in results)
            assert all('url' in result for result in results)
            assert all('snippet' in result for result in results)
            assert all('source' in result for result in results)

    @pytest.mark.asyncio
    async def test_search_with_invalid_query(self, web_search_tool):
        """Test search with invalid query."""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await web_search_tool.search("", num_results=5)

        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await web_search_tool.search("   ", num_results=5)

    @pytest.mark.asyncio
    async def test_search_with_invalid_num_results(self, web_search_tool):
        """Test search with invalid number of results."""
        with pytest.raises(ValueError, match="Number of results must be between 1 and 10"):
            await web_search_tool.search("test", num_results=0)

        with pytest.raises(ValueError, match="Number of results must be between 1 and 10"):
            await web_search_tool.search("test", num_results=11)

    @pytest.mark.asyncio
    async def test_extract_content_success(self, web_search_tool):
        """Test successful content extraction."""
        mock_html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Title</h1>
                <p>This is a paragraph with some text.</p>
                <script>var x = 1;</script>
                <style>body { color: red; }</style>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response

            content = await web_search_tool.extract_content("https://example.com")

            assert "Main Title" in content
            assert "This is a paragraph" in content
            assert "var x = 1;" not in content  # Script should be removed
            assert "color: red" not in content  # Style should be removed

    @pytest.mark.asyncio
    async def test_extract_content_error(self, web_search_tool):
        """Test content extraction with error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock(side_effect=Exception("Network error"))
            mock_get.return_value.__aenter__.return_value = mock_response

            content = await web_search_tool.extract_content("https://example.com")

            assert "Failed to extract content" in content

    @pytest.mark.asyncio
    async def test_search_with_content(self, web_search_tool, mock_duckduckgo_response):
        """Test search with content extraction."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock the API response
            mock_api_response = AsyncMock()
            mock_api_response.raise_for_status = lambda: None
            mock_api_response.json.return_value = mock_duckduckgo_response
            
            # Mock the content extraction response
            mock_content_response = AsyncMock()
            mock_content_response.raise_for_status = lambda: None
            mock_content_response.text.return_value = "Extracted content here"
            
            # Configure mock to return different responses for different calls
            mock_get.side_effect = [mock_api_response, mock_content_response]

            # Perform search with content extraction
            results = await web_search_tool.search_with_content(
                "Python programming", 
                num_results=2, 
                extract_content=True
            )

            # Verify results have content
            assert len(results) <= 2
            assert all('content' in result for result in results)
            assert all(result['content'] == "Extracted content here" for result in results)

    @pytest.mark.asyncio
    async def test_close_session(self, web_search_tool):
        """Test closing the aiohttp session."""
        # Create a real session instead of a mock
        session = await web_search_tool._get_session()
        assert web_search_tool.session is not None
        
        # Close session
        await web_search_tool.close()
        
        # Verify session was closed and set to None
        assert web_search_tool.session is None

    @pytest.mark.asyncio
    async def test_search_web_tool_function(self, mock_duckduckgo_response):
        """Test the search_web tool function."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock the API response
            mock_response = AsyncMock()
            mock_response.raise_for_status = lambda: None
            mock_response.json.return_value = mock_duckduckgo_response
            
            # Mock the content extraction response
            mock_content_response = AsyncMock()
            mock_content_response.raise_for_status = lambda: None
            mock_content_response.text.return_value = "Test content"
            
            # Configure mock to return different responses
            mock_get.side_effect = [mock_response, mock_content_response]

            # Call the tool function
            result = await search_web("Python programming", num_results=2)

            # Verify result format
            assert "Search results for 'Python programming':" in result
            assert "**Python Programming**" in result
            assert "https://example.com/python" in result
            assert "Test content" in result


class TestWebSearchIntegration:
    """Test web search integration with the tool calling system."""

    @pytest.mark.asyncio
    async def test_web_search_tool_calling(self):
        """Test that web search tool can be called through the tool calling system."""
        with patch('src.aibotto.tools.web_search.search_web') as mock_search:
            mock_search.return_value = "Search results: Python programming resources found"
            
            from src.aibotto.ai.tool_calling import ToolCallingManager
            from src.aibotto.db.operations import DatabaseOperations
            
            manager = ToolCallingManager()
            db_ops = MagicMock(spec=DatabaseOperations)
            
            # Mock the database operations
            db_ops.get_conversation_history = AsyncMock(return_value=[])
            db_ops.save_message = AsyncMock()
            
            # This should trigger web search tool
            # Note: This is a simplified test - in reality, the LLM would decide
            # when to use the tool
            result = await manager.process_user_request(123, 456, "Search for Python tutorials", db_ops)
            
            # The result should contain search results
            assert "Search results" in result or "Python tutorials" in result


class TestWebSearchEdgeCases:
    """Test edge cases and error scenarios for web search."""

    @pytest.mark.asyncio
    async def test_empty_api_response(self):
        """Test handling of empty API response."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={})
            mock_get.return_value.__aenter__.return_value = mock_response

            from src.aibotto.tools.web_search import WebSearchTool
            tool = WebSearchTool()
            results = await tool.search("test query")
            
            assert results == []

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test API error handling."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock(side_effect=Exception("API Error"))
            mock_get.return_value.__aenter__.return_value = mock_response

            from src.aibotto.tools.web_search import WebSearchTool
            tool = WebSearchTool()
            
            with pytest.raises(RuntimeError, match="Failed to perform web search"):
                await tool.search("test query")

    @pytest.mark.asyncio
    async def test_concurrent_content_extraction(self):
        """Test concurrent content extraction from multiple URLs."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock multiple content extraction responses
            mock_responses = [
                AsyncMock(
                    raise_for_status=lambda: None,
                    text=lambda: "Content 1"
                ),
                AsyncMock(
                    raise_for_status=lambda: None,
                    text=lambda: "Content 2"
                ),
                AsyncMock(
                    raise_for_status=lambda: None,
                    text=lambda: "Content 3"
                )
            ]
            
            mock_get.side_effect = mock_responses

            from src.aibotto.tools.web_search import WebSearchTool
            tool = WebSearchTool()
            
            # Create mock results
            mock_results = [
                {"url": "https://example.com/1"},
                {"url": "https://example.com/2"},
                {"url": "https://example.com/3"}
            ]
            
            # Test concurrent extraction
            contents = await asyncio.gather(*[
                tool.extract_content(result["url"]) for result in mock_results
            ])
            
            assert contents == ["Content 1", "Content 2", "Content 3"]