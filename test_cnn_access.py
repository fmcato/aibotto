#!/usr/bin/env python3
"""
Test to check if the bot can access CNN front page.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations
from unittest.mock import AsyncMock, MagicMock


async def test_cnn_front_page():
    """Test if the bot can handle CNN front page requests."""
    print("=== Testing CNN Front Page Access ===")
    
    manager = ToolCallingManager()
    
    # Test the user's exact query
    user_query = "grab front page from cnn"
    
    print(f"User query: '{user_query}'")
    
    # Mock the LLM response - this will show us what the bot thinks it can do
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "I don't have access to the specific tools needed to provide this information."
    mock_response.choices[0].message.tool_calls = None
    
    manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
    
    db_ops = DatabaseOperations()
    
    try:
        result = await manager.process_user_request(
            user_id=123,
            chat_id=456,
            message=user_query,
            db_ops=db_ops
        )
        
        print(f"Bot response: {result}")
        
        # Check if it mentions not having access
        if "no access" in result.lower() or "don't have" in result.lower() or "cannot" in result.lower():
            print("❌ Bot claims it has no internet access")
        else:
            print("✅ Bot acknowledges it can access the internet")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def test_cnn_with_curl():
    """Test if the bot can use curl to get CNN."""
    print("\n=== Testing CNN with Curl Command ===")
    
    manager = ToolCallingManager()
    
    user_query = "get cnn front page using curl"
    
    print(f"User query: '{user_query}'")
    
    # Mock a tool call response
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "execute_cli_command"
    mock_tool_call.function.arguments = '{"command": "curl https://www.cnn.com"}'
    mock_tool_call.id = "cnn_tool_123"
    
    mock_first_response = MagicMock()
    mock_first_response.choices = [MagicMock()]
    mock_first_response.choices[0].message = MagicMock()
    mock_first_response.choices[0].message.content = "I'll get the CNN front page for you."
    mock_first_response.choices[0].message.tool_calls = [mock_tool_call]
    
    mock_second_response = MagicMock()
    mock_second_response.choices = [MagicMock()]
    mock_second_response.choices[0].message = MagicMock()
    mock_second_response.choices[0].message.content = "I was able to retrieve the CNN front page. Here's the latest news..."
    
    manager.llm_client.chat_completion = AsyncMock(
        side_effect=[mock_first_response, mock_second_response]
    )
    
    manager.cli_executor.execute_command = AsyncMock(
        return_value="<html><body>CNN Front Page Content</body></html>"
    )
    
    db_ops = DatabaseOperations()
    
    try:
        result = await manager.process_user_request(
            user_id=123,
            chat_id=456,
            message=user_query,
            db_ops=db_ops
        )
        
        print(f"Bot response: {result}")
        
        # Check what command was executed
        executed_command = manager.cli_executor.execute_command.call_args[0][0]
        print(f"Executed command: {executed_command}")
        
        if "curl" in executed_command and "cnn.com" in executed_command:
            print("✅ Bot correctly used curl to get CNN")
        else:
            print("❌ Bot did not use curl for CNN")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def test_various_news_sites():
    """Test various news site requests."""
    print("\n=== Testing Various News Sites ===")
    
    test_queries = [
        "get cnn.com",
        "fetch nytimes.com",
        "grab bbc news",
        "access reuters.com",
        "get news from cnn"
    ]
    
    manager = ToolCallingManager()
    
    for query in test_queries:
        print(f"\nTesting: '{query}'")
        
        # Mock a tool call response
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = f'{{"command": "curl https://www.cnn.com"}}'
        mock_tool_call.id = "news_tool_123"
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        
        manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
        manager.cli_executor.execute_command = AsyncMock(return_value="News content")
        
        db_ops = DatabaseOperations()
        
        try:
            await manager.process_user_request(123, 456, query, db_ops)
            
            executed_command = manager.cli_executor.execute_command.call_args[0][0]
            print(f"  Command: {executed_command}")
            
            if "curl" in executed_command:
                print("  ✅ Uses curl")
            else:
                print("  ❌ Does not use curl")
                
        except Exception as e:
            print(f"  Error: {e}")


async def test_system_prompt_for_news():
    """Check what the system prompt says about news/general web access."""
    print("\n=== System Prompt Analysis for News/Web Access ===")
    
    from src.aibotto.ai.prompt_templates import SystemPrompts
    
    main_prompt = SystemPrompts.MAIN_SYSTEM_PROMPT
    tool_instructions = SystemPrompts.TOOL_INSTRUCTIONS
    
    print("Checking for news-related keywords in prompts:")
    
    news_keywords = ["news", "website", "webpage", "front page", "html", "http", "https", "cnn", "nytimes", "bbc"]
    
    for keyword in news_keywords:
        in_main = keyword in main_prompt.lower()
        in_tools = keyword in tool_instructions.lower()
        print(f"  {keyword}: main={in_main}, tools={in_tools}")
        
        if not in_main and not in_tools:
            print(f"    ❌ '{keyword}' not mentioned in prompts")


async def main():
    """Run all tests."""
    await test_cnn_front_page()
    await test_cnn_with_curl()
    await test_various_news_sites()
    await test_system_prompt_for_news()
    
    print("\n=== Analysis Summary ===")
    print("This test reveals whether the bot can handle general web requests")
    print("or if it's limited to only specific weather APIs.")


if __name__ == "__main__":
    asyncio.run(main())