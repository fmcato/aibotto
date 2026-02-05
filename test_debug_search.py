import asyncio
import sys
import os
import logging

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aibotto.tools.web_search import WebSearchTool

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_search():
    tool = WebSearchTool()
    
    try:
        # Test with a simple query
        query = "python programming"
        logger.info(f"Testing search with query: {query}")
        
        # Get the session manually to test the API call
        session = await tool._get_session()
        
        # Build DuckDuckGo API URL
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        
        logger.info(f"API URL: {tool.base_url}")
        logger.info(f"API params: {params}")
        
        # Make API request
        async with session.get(tool.base_url, params=params) as response:
            logger.info(f"Response status: {response.status}")
            logger.info(f"Response headers: {response.headers}")
            
            response.raise_for_status()
            
            # Handle different content types
            content_type = response.headers.get('content-type', '').lower()
            logger.info(f"Content type: {content_type}")
            
            if 'json' in content_type:
                data = await response.json()
                logger.info(f"Successfully parsed as JSON")
            else:
                # Try to parse as JSON anyway, or handle as text
                try:
                    data = await response.json()
                    logger.info(f"Successfully parsed as JSON (second attempt)")
                except Exception as e:
                    logger.error(f"JSON parsing failed: {e}")
                    # If JSON parsing fails, try to get text and extract manually
                    text = await response.text()
                    logger.info(f"Response text (first 500 chars): {text[:500]}...")
                    
                    # Try to find JSON object in the response
                    start_idx = text.find('{')
                    end_idx = text.rfind('}') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = text[start_idx:end_idx]
                        logger.info(f"Found JSON object (first 500 chars): {json_str[:500]}...")
                        try:
                            data = json.loads(json_str)
                            logger.info(f"Successfully parsed extracted JSON")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse extracted JSON: {e}")
                            raise RuntimeError(f"Unable to parse JSON response: {text[:200]}...")
                    else:
                        raise RuntimeError(f"Unable to parse JSON response: {text[:200]}...")
            
            logger.info(f"Data keys: {list(data.keys())}")
            logger.info(f"AbstractText: {data.get('AbstractText', 'Not found')}")
            logger.info(f"RelatedTopics count: {len(data.get('RelatedTopics', []))}")
            
            # Extract basic search results
            results = []
            if data.get("AbstractText"):
                logger.info("Found AbstractText, adding result")
                results.append({
                    "title": data.get("Heading", ""),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", ""),
                    "source": "DuckDuckGo"
                })

            # Add related topics as additional results
            related_topics = data.get("RelatedTopics", [])
            logger.info(f"Processing {len(related_topics)} related topics")
            
            for topic in related_topics[:5]:  # Limit to first 5 for debugging
                logger.info(f"Topic: {topic}")
                if "Text" in topic and "FirstURL" in topic:
                    logger.info("Found topic with Text and FirstURL")
                    # Extract title from text - handle different formats
                    text = topic.get("Text", "")
                    title = text
                    if " - " in text:
                        title = text.split(" - ")[0]
                    elif text.startswith("http"):
                        # If text starts with URL, extract title differently
                        title = text.replace("https://", "").replace("http://", "").split("/")[0]
                    
                    results.append({
                        "title": title,
                        "url": topic.get("FirstURL", ""),
                        "snippet": text,
                        "source": "DuckDuckGo"
                    })
                else:
                    logger.info("Topic missing Text or FirstURL")
            
            logger.info(f"Total results: {len(results)}")
            for i, result in enumerate(results):
                logger.info(f"Result {i}: {result}")
            
    finally:
        await tool.close()

if __name__ == "__main__":
    import json
    asyncio.run(debug_search())