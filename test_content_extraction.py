import asyncio
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aibotto.tools.web_search import WebSearchTool

async def test_content_extraction():
    """Test that we're actually getting substantial content from web pages."""
    tool = WebSearchTool()
    
    try:
        # Test with a query that should return good content
        print("Testing web search with content extraction...")
        results = await tool.search_with_content("machine learning basics", num_results=2)
        
        print(f"\nFound {len(results)} results:")
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Title: {result.get('title', 'No title')}")
            print(f"URL: {result.get('url', 'No URL')}")
            print(f"Snippet: {result.get('snippet', 'No snippet')[:200]}...")
            print(f"Content length: {len(result.get('content', ''))} characters")
            print(f"Content preview: {result.get('content', '')[:500]}...")
            
            # Check if we have substantial content
            content = result.get('content', '')
            if len(content) > 1000:
                print("✅ Substantial content extracted (>1000 chars)")
            elif len(content) > 100:
                print("⚠️  Some content extracted (>100 chars)")
            else:
                print("❌ Very little content extracted (<100 chars)")
        
        # Also test the search_web function which is what the LLM would use
        print("\n" + "="*50)
        print("Testing search_web function (LLM integration)...")
        from aibotto.tools.web_search import search_web
        llm_result = await search_web("python programming", num_results=1)
        print(f"LLM result length: {len(llm_result)} characters")
        print(f"LLM result preview: {llm_result[:800]}...")
        
        if "Content:" in llm_result and len(llm_result) > 500:
            print("✅ LLM result contains substantial content")
        else:
            print("❌ LLM result may not contain substantial content")
            
    finally:
        await tool.close()

if __name__ == "__main__":
    asyncio.run(test_content_extraction())