#!/usr/bin/env python3
"""
Test script to verify SearXNG web search functionality.
"""

import asyncio
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aibotto.tools.web_search import WebSearchTool


async def test_searxng_search():
    """Test SearXNG search functionality."""
    print("Testing SearXNG web search...")
    
    # Create web search tool instance
    tool = WebSearchTool(base_url="https://search.disroot.org")  # Public SearXNG instance
    
    try:
        # Test basic search
        print("\n1. Testing basic search...")
        results = await tool.search("Python programming", num_results=3)
        print(f"Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Source: {result['source']}")
            print(f"   Snippet: {result['snippet'][:100]}...")
            print()
        
        # Test search with content extraction
        print("2. Testing search with content extraction...")
        results_with_content = await tool.search_with_content("Python programming", num_results=2)
        print(f"Found {len(results_with_content)} results with content")
        
        for i, result in enumerate(results_with_content, 1):
            print(f"{i}. {result['title']}")
            print(f"   Content length: {len(result.get('content', ''))}")
            print()
        
        print("✅ SearXNG search test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing SearXNG: {e}")
        return False
    
    finally:
        await tool.close()
    
    return True


async def test_searxng_error_handling():
    """Test SearXNG error handling."""
    print("\nTesting error handling...")
    
    tool = WebSearchTool(base_url="https://search.disroot.org")
    
    try:
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
        
        print("✅ Error handling test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in error handling test: {e}")
        return False
    
    finally:
        await tool.close()
    
    return True


async def main():
    """Main test function."""
    print("Starting SearXNG web search tests...")
    
    success = await test_searxng_search()
    if not success:
        return False
    
    success = await test_searxng_error_handling()
    if not success:
        return False
    
    print("\n🎉 All tests passed! SearXNG integration is working correctly.")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)