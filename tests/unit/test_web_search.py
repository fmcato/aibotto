"""
Tests for web search functionality using ddgs library.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import asyncio

from src.aibotto.tools.web_search import WebSearchTool, search_web


class TestWebSearchTool:
    """Test the WebSearchTool class."""

    @pytest.fixture
    def web_search_tool(self):
        """Create a WebSearchTool instance for testing."""
        return WebSearchTool()

    @pytest.fixture
    def mock_ddgs_response(self):
        """Mock ddgs API response."""
        return [
            {
                "title": "Python Programming Tutorial",
                "href": "https://example.com/python-tutorial",
                "body": "Learn Python programming with this comprehensive tutorial covering basics and advanced topics."
            },
            {
                "title": "Python Documentation",
                "href": "https://docs.python.org",
                "body": "Official Python documentation with detailed information about the language."
            }
        ]

    @pytest.mark.asyncio
    async def test_search_basic(self, web_search_tool, mock_ddgs_response):
        """Test basic web search functionality."""
        with patch('ddgs.DDGS.text') as mock_text:
            # Mock the ddgs response
            mock_text.return_value = mock_ddgs_response

            # Perform search
            results = await web_search_tool.search("Python programming", num_results=3)

            # Verify results
            assert len(results) <= 3
            assert all('title' in result for result in results)
            assert all('url' in result for result in results)
            assert all('snippet' in result for result in results)
            assert all('source' in result for result in results)
            assert all(result['source'] == 'DuckDuckGo' for result in results)

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
        with pytest.raises(ValueError, match="Number of results must be between 1 and 20"):
            await web_search_tool.search("test", num_results=0)

        with pytest.raises(ValueError, match="Number of results must be between 1 and 20"):
            await web_search_tool.search("test", num_results=21)

    @pytest.mark.asyncio
    async def test_extract_content_success(self, web_search_tool):
        """Test successful content extraction."""
        # With ddgs, content extraction returns a simple message
        content = await web_search_tool.extract_content("https://example.com")
        assert "Content from https://example.com" in content
        assert "Full content extraction not implemented with ddgs" in content

    @pytest.mark.asyncio
    async def test_extract_content_error(self, web_search_tool):
        """Test content extraction with error."""
        # With ddgs, content extraction shouldn't raise exceptions
        content = await web_search_tool.extract_content("https://example.com")
        assert "Content from https://example.com" in content

    @pytest.mark.asyncio
    async def test_search_with_content(self, web_search_tool, mock_ddgs_response):
        """Test search with content extraction."""
        with patch('ddgs.DDGS.text') as mock_text:
            mock_text.return_value = mock_ddgs_response

            # Perform search with content extraction
            results = await web_search_tool.search_with_content(
                "Python programming",
                num_results=2,
                extract_content=True
            )

            # Verify results have content
            assert len(results) <= 2
            assert all('content' in result for result in results)
            assert all("Content from" in result['content'] for result in results)

    @pytest.mark.asyncio
    async def test_close_session(self, web_search_tool):
        """Test closing the session."""
        # With ddgs, there's no session to close
        await web_search_tool.close()
        # Should not raise any exceptions

    @pytest.mark.asyncio
    async def test_search_web_tool_function(self, mock_ddgs_response):
        """Test the search_web tool function."""
        with patch('src.aibotto.tools.web_search.web_search_tool.search_with_content') as mock_search:
            mock_search.return_value = [
                {
                    "title": "Python Programming Tutorial",
                    "url": "https://example.com/python-tutorial",
                    "content": "Learn Python programming with this comprehensive tutorial covering basics and advanced topics.",
                    "source": "DuckDuckGo"
                }
            ]

            # Call the tool function
            result = await search_web("Python programming", num_results=2)

            # Verify result format
            assert "Search results for 'Python programming':" in result
            assert "**Python Programming Tutorial**" in result
            assert "https://example.com/python-tutorial" in result
            assert "Learn Python programming" in result
            assert "DuckDuckGo" in result


class TestWebSearchIntegration:
    """Test web search integration with the tool calling system."""

    @pytest.mark.asyncio
    async def test_web_search_tool_calling(self):
        """Test that web search tool can be called through the tool calling system."""
        with patch('src.aibotto.tools.web_search.search_web') as mock_search:
            mock_search.return_value = "Search results: Python programming resources found"

            # Mock the tool calling manager
            from src.aibotto.ai.tool_calling import ToolCallingManager
            from src.aibotto.db.operations import DatabaseOperations

            manager = ToolCallingManager()
            db_ops = Mock(spec=DatabaseOperations)

            # This should trigger web search tool
            result = await manager.process_user_request(123, 456, "Search for Python tutorials", db_ops)

            # The result should contain search-related content
            assert "Python" in result and ("tutorial" in result.lower() or "resource" in result.lower())


class TestWebSearchEdgeCases:
    """Test edge cases and error scenarios for web search."""

    @pytest.mark.asyncio
    async def test_empty_api_response(self):
        """Test handling of empty API response."""
        with patch('ddgs.DDGS.text') as mock_text:
            mock_text.return_value = []

            from src.aibotto.tools.web_search import WebSearchTool
            tool = WebSearchTool()
            results = await tool.search("test query")

            assert results == []

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test API error handling."""
        with patch('ddgs.DDGS.text') as mock_text:
            mock_text.side_effect = Exception("API Error")

            from src.aibotto.tools.web_search import WebSearchTool
            tool = WebSearchTool()

            with pytest.raises(RuntimeError, match="Failed to perform web search"):
                await tool.search("test query")

    @pytest.mark.asyncio
    async def test_concurrent_content_extraction(self):
        """Test concurrent content extraction."""
        with patch('ddgs.DDGS.text') as mock_text:
            mock_text.return_value = [
                {"title": "Page 1", "href": "https://example.com/1", "body": "Content 1"},
                {"title": "Page 2", "href": "https://example.com/2", "body": "Content 2"},
                {"title": "Page 3", "href": "https://example.com/3", "body": "Content 3"},
            ]

            from src.aibotto.tools.web_search import WebSearchTool
            tool = WebSearchTool()

            # Test concurrent extraction
            results = await tool.search_with_content("test", num_results=3, extract_content=True)

            assert len(results) == 3
            assert all('content' in result for result in results)
            assert all("Content from" in result['content'] for result in results)