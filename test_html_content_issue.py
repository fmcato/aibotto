#!/usr/bin/env python3
"""
Test to reproduce the HTML content processing issue.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations


async def test_html_content_issue():
    """Test that reproduces the HTML content processing issue."""
    
    # Mock the database operations
    mock_db_ops = AsyncMock(spec=DatabaseOperations)
    mock_db_ops.get_conversation_history.return_value = []
    mock_db_ops.save_message = AsyncMock()
    
    # Create tool calling manager
    tool_manager = ToolCallingManager()
    
    # Mock the LLM client to simulate a proper response
    with patch.object(tool_manager.llm_client, 'chat_completion') as mock_chat:
        
        # First call - LLM wants to use tools
        first_response = AsyncMock()
        first_response.choices = [AsyncMock()]
        first_response.choices[0].message = AsyncMock()
        first_response.choices[0].message.tool_calls = [AsyncMock()]
        first_response.choices[0].message.tool_calls[0].function = AsyncMock()
        first_response.choices[0].message.tool_calls[0].function.name = "execute_cli_command"
        first_response.choices[0].message.tool_calls[0].function.arguments = '{"command": "curl -s https://www.bbc.com"}'
        first_response.choices[0].message.tool_calls[0].id = "test_tool_call_id"
        
        # Second call - LLM returns HTML content as if user pasted it
        second_response = AsyncMock()
        second_response.choices = [AsyncMock()]
        second_response.choices[0].message = AsyncMock()
        second_response.choices[0].message.content = """I see you've shared a lot of HTML and JavaScript content from a BBC webpage. This appears to be the BBC homepage with various news articles, videos, and sections about different topics like news, technology, culture, travel, and more.

The code includes:
- Navigation menus for different sections (News, Sport, Business, Technology, etc.)
- Featured news articles with headlines and images
- Video content sections
- Audio/podcast recommendations
- Various interactive elements
- Footer with links and social media options

Is there something specific you'd like me to help you with regarding this webpage? For example, are you looking to:
- Extract specific information from the page?
- Understand how certain features work?
- Make modifications to the code?
- Analyze the content structure?

Please let me know what you need assistance with!"""
        
        mock_chat.side_effect = [first_response, second_response]
        
        # Mock CLI executor to return HTML content
        with patch.object(tool_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = """<!DOCTYPE html>
<html>
<head>
    <title>BBC News</title>
</head>
<body>
    <div class="news-item">
        <h2>Trump announces new policy initiative</h2>
        <p>Former President Trump has announced a new policy initiative focused on economic growth...</p>
    </div>
    <div class="news-item">
        <h2>Markets react to political developments</h2>
        <p>Stock markets are showing volatility following recent political announcements...</p>
    </div>
</body>
</html>"""
            
            # Process the user request
            result = await tool_manager.process_user_request(
                user_id=1,
                chat_id=1,
                message="what are the current news on donald trump",
                db_ops=mock_db_ops
            )
            
            # Print debug information
            print(f"Final result: {result}")
            
            # Check what was saved to the database
            print("\nDatabase calls:")
            for call in mock_db_ops.save_message.call_args_list:
                print(f"Saved message: {call}")
            
            # Check if CLI executor was called
            print(f"\nCLI executor called: {mock_execute.called}")
            if mock_execute.called:
                print(f"CLI executor call args: {mock_execute.call_args}")
            
            # Check if the result contains HTML processing instead of news summary
            if "HTML and JavaScript content" in result:
                print("\n❌ ISSUE REPRODUCED: Bot is treating HTML as user-pasted content instead of extracting news")
            elif "Trump announces new policy initiative" in result:
                print("\n✅ Bot correctly extracted and summarized news from HTML")
            else:
                print("\n⚠️  Unexpected response format")


if __name__ == "__main__":
    asyncio.run(test_html_content_issue())