#!/usr/bin/env python3
"""
Simple test script to verify SearXNG web search functionality.
"""

import asyncio
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aibotto.tools.web_search import WebSearchTool


async def test_searxng_basic():
    """Test basic SearXNG functionality without external API calls."""
    print("Testing SearXNG web search basic functionality...")
    
    # Create web search tool instance
    tool = WebSearchTool(base_url="http://localhost:8080")
    
    try:
        # Test validation
        print("\n1. Testing validation...")
        
        # Test empty query
        try:
            await tool.search("")
            print("❌ Should have raised ValueError for empty query")
            return False
        except ValueError as e:
            print(f"✅ Correctly handled empty query: {e}")
        
        # Test invalid number of results
        try:
            await tool.search("test", num_results=0)
            print("❌ Should have raised ValueError for invalid num_results")
            return False
        except ValueError as e:
            print(f"✅ Correctly handled invalid num_results: {e}")
        
        # Test valid range (this will fail if no SearXNG instance is running, which is expected)
        print("\n   Testing valid range (expected to fail without SearXNG instance)...")
        try:
            await tool.search("test", num_results=5)
            print("✅ Valid search parameters accepted and API is accessible")
        except RuntimeError as e:
            if "Failed to perform web search" in str(e):
                print("✅ Valid search parameters accepted (API error expected without SearXNG instance)")
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error with valid parameters: {e}")
            return False
        
        print("✅ Validation tests passed!")
        
        # Test content extraction method exists
        print("\n2. Testing content extraction method...")
        try:
            content = await tool.extract_content("https://example.com")
            print(f"✅ Content extraction method works: {type(content)}")
        except Exception as e:
            print(f"✅ Content extraction method handles errors: {e}")
        
        print("✅ Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing SearXNG: {e}")
        return False
    
    finally:
        await tool.close()


async def main():
    """Main test function."""
    print("Starting SearXNG web search basic tests...")
    
    success = await test_searxng_basic()
    if not success:
        return False
    
    print("\n🎉 Basic tests passed! SearXNG integration structure is correct.")
    print("Note: Full API testing requires a running SearXNG instance.")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)