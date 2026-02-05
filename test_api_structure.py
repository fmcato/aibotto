import asyncio
import aiohttp
import json

async def test_api_structure():
    """Test the DuckDuckGo API structure to understand the response."""
    base_url = "https://api.duckduckgo.com/"
    params = {
        "q": "python programming",
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(base_url, params=params) as response:
                response.raise_for_status()
                
                # Handle different content types
                content_type = response.headers.get('content-type', '').lower()
                if 'json' in content_type:
                    data = await response.json()
                else:
                    # Try to parse as JSON anyway, or handle as text
                    try:
                        data = await response.json()
                    except Exception:
                        # If JSON parsing fails, try to get text and extract manually
                        text = await response.text()
                        # Try to find JSON object in the response
                        start_idx = text.find('{')
                        end_idx = text.rfind('}') + 1
                        if start_idx != -1 and end_idx != -1:
                            json_str = text[start_idx:end_idx]
                            data = json.loads(json_str)
                        else:
                            raise RuntimeError(f"Unable to parse JSON response: {text[:200]}...")
                
                print(f"API Response Keys: {list(data.keys())}")
                
                # Check for AbstractText
                if 'AbstractText' in data and data['AbstractText']:
                    print(f"\nAbstractText found: {data['AbstractText'][:200]}...")
                    print(f"AbstractURL: {data.get('AbstractURL', 'Not found')}")
                    print(f"Heading: {data.get('Heading', 'Not found')}")
                
                # Check RelatedTopics
                if 'RelatedTopics' in data:
                    topics = data['RelatedTopics']
                    print(f"\nRelatedTopics count: {len(topics)}")
                    
                    # Print first few topics
                    for i, topic in enumerate(topics[:3]):
                        print(f"\nTopic {i+1}:")
                        print(f"  Type: {topic.get('Type', 'Unknown')}")
                        print(f"  FirstURL: {topic.get('FirstURL', 'Not found')}")
                        print(f"  Text: {topic.get('Text', 'Not found')[:100]}...")
                
                # Check Results
                if 'Results' in data:
                    results = data['Results']
                    print(f"\nResults count: {len(results)}")
                    for i, result in enumerate(results[:2]):
                        print(f"\nResult {i+1}:")
                        print(f"  Title: {result.get('title', 'Not found')}")
                        print(f"  URL: {result.get('url', 'Not found')}")
                        print(f"  Text: {result.get('text', 'Not found')[:100]}...")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_structure())