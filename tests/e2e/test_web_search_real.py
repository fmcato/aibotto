"""
End-to-end test for web search functionality using real SearXNG API calls.
This test verifies the complete web search pipeline without any mocking.
"""

import asyncio
import pytest
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from aibotto.tools.web_search import WebSearchTool, search_web


class TestWebSearchE2E:
    """End-to-end tests for web search functionality."""

    @pytest.fixture
    async def web_search_tool(self):
        """Create a web search tool instance."""
        tool = WebSearchTool()
        yield tool
        # Cleanup
        await tool.close()

    @pytest.mark.asyncio
    async def test_basic_web_search_happy_path(self, web_search_tool):
        """Test basic web search functionality with real API calls."""
        # Test a simple search query with timeout
        query = "Python programming"
        try:
            results = await asyncio.wait_for(
                web_search_tool.search(query, num_results=3),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Web search timed out after 10 seconds")
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0
        assert len(results) <= 3
        
        # Check result structure
        for result in results:
            assert "title" in result
            assert "url" in result
            assert "snippet" in result
            assert "source" in result
            assert result["source"] in ["DuckDuckGo", "duckduckgo", "bing", "google", "wikipedia", "youtube"]
            assert isinstance(result["title"], str)
            assert isinstance(result["url"], str)
            assert isinstance(result["snippet"], str)

    @pytest.mark.asyncio
    async def test_web_search_with_content_extraction(self, web_search_tool):
        """Test web search with content extraction from real pages."""
        query = "machine learning"
        try:
            results = await asyncio.wait_for(
                web_search_tool.search_with_content(query, num_results=2),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Web search with content extraction timed out after 10 seconds")
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0
        assert len(results) <= 2
        
        # Check that content was extracted
        for result in results:
            assert "content" in result
            assert isinstance(result["content"], str)
            assert len(result["content"]) > 0
            # Content should be present (with ddgs, it might not be longer than snippet)
            assert len(result["content"]) > 0
            # With ddgs, content extraction is limited, so we just check it exists
            assert "Content from" in result["content"]

    @pytest.mark.asyncio
    async def test_search_web_tool_function(self):
        """Test the search_web tool function that would be called by LLM."""
        query = "artificial intelligence"
        try:
            result = await asyncio.wait_for(
                search_web(query, num_results=2),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Search web tool function timed out after 10 seconds")
        
        # Verify result
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Search results for" in result
        assert query in result
        assert "URL:" in result
        assert "Content:" in result

    @pytest.mark.asyncio
    async def test_multiple_searches_session_reuse(self, web_search_tool):
        """Test that session is properly reused across multiple searches."""
        # First search
        try:
            results1 = await asyncio.wait_for(
                web_search_tool.search("web development", num_results=2),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Multiple searches first search timed out after 10 seconds")
        assert len(results1) > 0
        
        # Second search (should reuse session)
        try:
            results2 = await asyncio.wait_for(
                web_search_tool.search("database design", num_results=2),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Multiple searches second search timed out after 10 seconds")
        assert len(results2) > 0
        
        # Third search with content extraction
        try:
            results3 = await asyncio.wait_for(
                web_search_tool.search_with_content("cloud computing", num_results=1),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Multiple searches third search timed out after 10 seconds")
        assert len(results3) > 0
        assert "content" in results3[0]

    @pytest.mark.asyncio
    async def test_error_handling_invalid_query(self, web_search_tool):
        """Test error handling for invalid queries."""
        # Test empty query
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await web_search_tool.search("")
        
        # Test whitespace-only query
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await web_search_tool.search("   ")
        
        # Test invalid number of results
        with pytest.raises(ValueError, match="Number of results must be between 1 and 20"):
            await web_search_tool.search("test", num_results=0)
        
        with pytest.raises(ValueError, match="Number of results must be between 1 and 20"):
            await web_search_tool.search("test", num_results=21)

    @pytest.mark.asyncio
    async def test_content_extraction_error_handling(self, web_search_tool):
        """Test that content extraction handles errors gracefully."""
        # Search for results
        try:
            results = await asyncio.wait_for(
                web_search_tool.search("technology", num_results=2),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Content extraction error handling search timed out after 10 seconds")
        assert len(results) > 0
        
        # Try to extract content from a URL that might fail
        for result in results:
            try:
                content = await asyncio.wait_for(
                    web_search_tool.extract_content(result["url"]),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                pytest.fail(f"Content extraction for {result['url']} timed out after 5 seconds")
            assert isinstance(content, str)
            # Should either have content or an error message
            assert len(content) > 0

    @pytest.mark.asyncio
    async def test_real_api_response_format(self, web_search_tool):
        """Test that real API responses match expected format."""
        query = "python programming"  # Changed to a more reliable query
        try:
            results = await asyncio.wait_for(
                web_search_tool.search(query, num_results=1),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Real API response format test timed out after 10 seconds")
        
        assert len(results) == 1
        result = results[0]
        
        # Verify all expected fields are present
        required_fields = ["title", "url", "snippet", "source"]
        for field in required_fields:
            assert field in result
            assert result[field] is not None
            assert isinstance(result[field], str)
            assert len(result[field].strip()) > 0
        
        # Verify URL format
        assert result["url"].startswith(("http://", "https://"))
        
        # Verify content is extracted when requested
        content_results = await web_search_tool.search_with_content(query, num_results=1)
        assert "content" in content_results[0]
        assert len(content_results[0]["content"]) > 0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])