import asyncio
import aiohttp
import json

async def test_duckduckgo_api():
    """Test the DuckDuckGo API directly to see what we get."""
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
                print(f"Status code: {response.status}")
                print(f"Content type: {response.headers.get('content-type', 'Unknown')}")
                print(f"Headers: {dict(response.headers)}")
                
                # Try different ways to parse the response
                content_type = response.headers.get('content-type', '').lower()
                
                if 'json' in content_type:
                    print("\nTrying to parse as JSON...")
                    try:
                        data = await response.json()
                        print(f"Successfully parsed as JSON")
                        print(f"Keys: {list(data.keys())}")
                        if 'AbstractText' in data:
                            print(f"AbstractText: {data['AbstractText'][:100]}...")
                        if 'RelatedTopics' in data:
                            print(f"RelatedTopics count: {len(data['RelatedTopics'])}")
                            if data['RelatedTopics']:
                                print(f"First topic: {data['RelatedTopics'][0]}")
                    except Exception as e:
                        print(f"JSON parsing failed: {e}")
                else:
                    print("\nContent type is not JSON, trying text...")
                    try:
                        text = await response.text()
                        print(f"Response text (first 500 chars): {text[:500]}...")
                        
                        # Try to find JSON in the text
                        start_idx = text.find('{')
                        end_idx = text.rfind('}') + 1
                        if start_idx != -1 and end_idx != -1:
                            json_str = text[start_idx:end_idx]
                            print(f"\nFound JSON object (first 500 chars): {json_str[:500]}...")
                            try:
                                data = json.loads(json_str)
                                print(f"Successfully parsed extracted JSON")
                                print(f"Keys: {list(data.keys())}")
                            except json.JSONDecodeError as e:
                                print(f"Failed to parse extracted JSON: {e}")
                        else:
                            print("No JSON object found in response")
                    except Exception as e:
                        print(f"Text parsing failed: {e}")
                        
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_duckduckgo_api())