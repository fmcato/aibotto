"""
Test ddgs error handling to ensure robustness against engine errors.
"""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock

from src.aibotto.tools.web_search import WebSearchTool


class TestDdgsErrorHandling:
    """Test error handling in ddgs web search."""

    @pytest.mark.asyncio
    async def test_mojeek_engine_error_handling(self):
        """Test handling of specific engine errors like the mojeek error."""
        tool = WebSearchTool()
        
        # Mock the ddgs.text method to raise the specific error
        with patch.object(tool.ddgs, 'text') as mock_text:
            mock_text.side_effect = ValueError('not enough values to unpack (expected 2, got 1)')
            
            # The search should handle the error gracefully
            with pytest.raises(RuntimeError, match="Failed to perform web search"):
                await tool.search("test query")

    @pytest.mark.asyncio
    async def test_general_exception_handling(self):
        """Test general exception handling in web search."""
        tool = WebSearchTool()
        
        # Mock the ddgs.text method to raise a general exception
        with patch.object(tool.ddgs, 'text') as mock_text:
            mock_text.side_effect = Exception("General error")
            
            # The search should handle the error gracefully
            with pytest.raises(RuntimeError, match="Failed to perform web search"):
                await tool.search("test query")

    @pytest.mark.asyncio
    async def test_successful_search_after_error(self):
        """Test that search works after an error occurs."""
        tool = WebSearchTool()
        
        # First call raises error
        with patch.object(tool.ddgs, 'text') as mock_text:
            mock_text.side_effect = ValueError('not enough values to unpack (expected 2, got 1)')
            
            with pytest.raises(RuntimeError):
                await tool.search("test query")
        
        # Second call succeeds
        with patch.object(tool.ddgs, 'text') as mock_text:
            mock_text.return_value = [
                {
                    "title": "Test Result",
                    "href": "https://example.com",
                    "body": "Test snippet"
                }
            ]
            
            results = await tool.search("test query")
            assert len(results) == 1
            assert results[0]["title"] == "Test Result"

    @pytest.mark.asyncio
    async def test_empty_query_validation(self):
        """Test validation of empty queries."""
        tool = WebSearchTool()
        
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await tool.search("")
        
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await tool.search("   ")

    @pytest.mark.asyncio
    async def test_num_results_validation(self):
        """Test validation of num_results parameter."""
        tool = WebSearchTool()
        
        with pytest.raises(ValueError, match="Number of results must be between 1 and 20"):
            await tool.search("test", num_results=0)
        
        with pytest.raises(ValueError, match="Number of results must be between 1 and 20"):
            await tool.search("test", num_results=21)

    @pytest.mark.asyncio
    async def test_partial_results_handling(self):
        """Test handling when ddgs returns partial or malformed results."""
        tool = WebSearchTool()
        
        # Mock ddgs to return results with missing fields
        with patch.object(tool.ddgs, 'text') as mock_text:
            mock_text.return_value = [
                {
                    "title": "Complete Result",
                    "href": "https://example.com",
                    "body": "Complete snippet"
                },
                {
                    # Missing title
                    "href": "https://example2.com",
                    "body": "Partial snippet"
                },
                {
                    # Missing href and body
                    "title": "Incomplete Result"
                }
            ]
            
            results = await tool.search("test query")
            assert len(results) == 3
            
            # Check that missing fields are handled gracefully
            assert results[0]["title"] == "Complete Result"
            assert results[1]["title"] == ""  # Missing title should default to empty string
            assert results[2]["url"] == ""    # Missing href should default to empty string
            assert results[2]["snippet"] == "" # Missing body should default to empty string