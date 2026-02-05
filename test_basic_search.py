import asyncio
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aibotto.tools.web_search import WebSearchTool

async def test_basic_search():
    """Test the basic search method to see what's happening."""
    tool = WebSearchTool()
    
    try:
        # Test basic search first
        print("Testing basic search...")
        basic_results = await tool.search("machine learning basics", num_results=2)
        print(f"Basic search results: {len(basic_results)}")
        
        if basic_results:
            print("Basic search results:")
            for i, result in enumerate(basic_results, 1):
                print(f"  {i}. {result.get('title', 'No title')} - {result.get('url', 'No URL')}")
        
        # Now try content extraction on the results
        if basic_results:
            print("\nTesting content extraction on existing results...")
            content_tasks = []
            for result in basic_results:
                print(f"  Extracting content from: {result.get('url', 'No URL')}")
                content_tasks.append(tool.extract_content(result["url"]))
            
            contents = await asyncio.gather(*content_tasks, return_exceptions=True)
            
            for i, (result, content) in enumerate(zip(basic_results, contents)):
                print(f"  Result {i+1} content length: {len(content) if not isinstance(content, Exception) else 'ERROR'}")
                if isinstance(content, Exception):
                    print(f"    Error: {str(content)}")
                else:
                    print(f"    Content preview: {content[:200]}...")
        
    finally:
        await tool.close()

if __name__ == "__main__":
    asyncio.run(test_basic_search())