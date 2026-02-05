import asyncio
import sys
import os
import logging

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aibotto.tools.web_search import WebSearchTool

async def test_actual_search():
    tool = WebSearchTool()
    
    try:
        # Test the actual search method
        results = await tool.search("python programming", num_results=2)
        print(f"Actual search results: {len(results)}")
        
        if results:
            for i, result in enumerate(results):
                print(f"Result {i}: {result}")
        else:
            print("No results from actual search method")
            
    finally:
        await tool.close()

if __name__ == "__main__":
    asyncio.run(test_actual_search())