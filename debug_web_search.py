#!/usr/bin/env python3
"""
Debug script to test web search functionality directly.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.aibotto.tools.web_search import WebSearchTool

async def test_basic_search():
    """Test basic web search functionality."""
    print("Testing basic web search...")
    
    tool = WebSearchTool()
    try:
        results = await tool.search("Python programming", num_results=3)
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get('title', 'No title')}")
            print(f"   URL: {result.get('url', 'No URL')}")
            print(f"   Snippet: {result.get('snippet', 'No snippet')[:100]}...")
            print()
        
        return len(results) > 0
    except Exception as e:
        print(f"Error in basic search: {e}")
        return False
    finally:
        await tool.close()

async def test_search_with_content():
    """Test search with content extraction."""
    print("Testing search with content extraction...")
    
    tool = WebSearchTool()
    try:
        results = await tool.search_with_content("Python programming", num_results=2)
        print(f"Found {len(results)} results with content:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get('title', 'No title')}")
            print(f"   URL: {result.get('url', 'No URL')}")
            print(f"   Content: {result.get('content', 'No content')[:200]}...")
            print()
        
        return len(results) > 0
    except Exception as e:
        print(f"Error in search with content: {e}")
        return False
    finally:
        await tool.close()

async def main():
    """Run all tests."""
    print("=== Web Search Debug Tests ===\n")
    
    # Test basic search
    basic_search_success = await test_basic_search()
    print(f"Basic search test: {'✅ PASSED' if basic_search_success else '❌ FAILED'}\n")
    
    # Test search with content
    content_search_success = await test_search_with_content()
    print(f"Search with content test: {'✅ PASSED' if content_search_success else '❌ FAILED'}\n")
    
    if basic_search_success and content_search_success:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)