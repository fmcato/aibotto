#!/usr/bin/env python3
"""
Test script to verify SearXNG web search functionality with mocked responses.
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aibotto.tools.web_search import WebSearchTool


async def test_searxng_with_mock():
    """Test SearXNG search functionality with mocked responses."""
    print("Testing SearXNG web search with mocked responses...")
    
    # Mock response data
    mock_response_data = {
        "results": [
            {
                "title": "Python Programming Tutorial",
                "url": "https://example.com/python-tutorial",
                "content": "Learn Python programming with this comprehensive tutorial covering basics and advanced topics.",
                "engine": "wikipedia",
                "publishedDate": "2023-12-01"
            },
            {
                "title": "Python Documentation",
                "url": "https://docs.python.org",
                "content": "Official Python documentation with detailed information about the language.",
                "engine": "duckduckgo",
                "publishedDate": "2023-11-15"
            }
        ]
    }
    
    # Create web search tool instance
    tool = WebSearchTool(base_url="http://localhost:8080")
    
    try:
        # Mock the session and response
        with patch.object(tool, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.get.return_value.__aexit__.return_value = None
            mock_get_session.return_value = mock_session
            
            # Test basic search
            print("\n1. Testing basic search...")
            results = await tool.search("Python programming", num_results=2)
            print(f"Found {len(results)} results")
            
            assert len(results) == 2
            assert results[0]["title"] == "Python Programming Tutorial"
            assert results[0]["url"] == "https://example.com/python-tutorial"
            assert results[0]["source"] == "wikipedia"
            assert results[1]["title"] == "Python Documentation"
            assert results[1]["url"] == "https://docs.python.org"
            assert results[1]["source"] == "duckduckgo"
            
            print("✅ Basic search test passed!")
            
            # Test search with content extraction
            print("\n2. Testing search with content extraction...")
            with patch.object(tool, 'extract_content') as mock_extract:
                mock_extract.return_value = "This is the extracted content from the webpage."
                
                results_with_content = await tool.search_with_content("Python programming", num_results=2)
                print(f"Found {len(results_with_content)} results with content")
                
                assert len(results_with_content) == 2
                assert "content" in results_with_content[0]
                assert results_with_content[0]["content"] == "This is the extracted content from the webpage."
                assert "content" in results_with_content[1]
                assert results_with_content[1]["content"] == "This is the extracted content from the webpage."
                
                print("✅ Content extraction test passed!")
            
            # Test error handling
            print("\n3. Testing error handling...")
            
            # Test empty query
            try:
                await tool.search("")
                print("❌ Should have raised ValueError for empty query")
                return False
            except ValueError:
                print("✅ Correctly handled empty query")
            
            # Test invalid number of results
            try:
                await tool.search("test", num_results=0)
                print("❌ Should have raised ValueError for invalid num_results")
                return False
            except ValueError:
                print("✅ Correctly handled invalid num_results")
            
            print("✅ Error handling test passed!")
        
        print("\n🎉 All tests passed! SearXNG integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing SearXNG: {e}")
        return False
    
    finally:
        await tool.close()


async def main():
    """Main test function."""
    print("Starting SearXNG web search tests with mocked responses...")
    
    success = await test_searxng_with_mock()
    if not success:
        return False
    
    print("\n🎉 All tests passed! SearXNG integration is working correctly.")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)