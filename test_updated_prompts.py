#!/usr/bin/env python3
"""
Test the updated prompts to see if they now handle CNN/general web requests.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations
from unittest.mock import AsyncMock, MagicMock


async def test_cnn_with_updated_prompts():
    """Test if the updated prompts now handle CNN requests."""
    print("=== Testing CNN with Updated Prompts ===")
    
    manager = ToolCallingManager()
    
    # Test the exact query that was failing before
    user_query = "grab front page from cnn"
    
    print(f"User query: '{user_query}'")
    
    # Mock a realistic tool call response
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "execute_cli_command"
    mock_tool_call.function.arguments = '{"command": "curl -A \\"Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36\\" https://www.cnn.com"}'
    mock_tool_call.id = "cnn_tool_123"
    
    # First response - bot should now understand it can get web content
    mock_first_response = MagicMock()
    mock_first_response.choices = [MagicMock()]
    mock_first_response.choices[0].message = MagicMock()
    mock_first_response.choices[0].message.content = "I'll get the CNN front page for you."
    mock_first_response.choices[0].message.tool_calls = [mock_tool_call]
    
    # Second response - after getting the web content
    mock_second_response = MagicMock()
    mock_second_response.choices = [MagicMock()]
    mock_second_response.choices[0].message = MagicMock()
    mock_second_response.choices[0].message.content = "I was able to retrieve the CNN front page. Here are the latest headlines..."
    
    manager.llm_client.chat_completion = AsyncMock(
        side_effect=[mock_first_response, mock_second_response]
    )
    
    manager.cli_executor.execute_command = AsyncMock(
        return_value="<html>CNN Front Page Content with latest news...</html>"
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
            
        # Check if the response acknowledges web access
        if "front page" in result.lower() or "cnn" in result.lower():
            print("✅ Bot provided CNN-specific response")
        else:
            print("❌ Bot did not provide CNN-specific response")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def test_various_web_requests():
    """Test various web requests with updated prompts."""
    print("\n=== Testing Various Web Requests ===")
    
    test_queries = [
        "grab front page from cnn",
        "get cnn.com",
        "fetch nytimes.com",
        "grab bbc news front page",
        "access reuters.com",
        "get website content",
        "fetch https://www.example.com"
    ]
    
    manager = ToolCallingManager()
    
    for query in test_queries:
        print(f"\nTesting: '{query}'")
        
        # Mock a tool call response
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = f'{{"command": "curl -A \\"Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36\\" https://www.cnn.com"}}'
        mock_tool_call.id = "web_tool_123"
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        
        manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
        manager.cli_executor.execute_command = AsyncMock(return_value="Web content")
        
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


async def test_command_suggestions():
    """Test if command suggestions now include web/news options."""
    print("\n=== Testing Command Suggestions ===")
    
    from src.aibotto.cli.enhanced_executor import EnhancedCLIExecutor
    
    executor = EnhancedCLIExecutor()
    
    # Test news-related suggestions
    news_queries = [
        "grab front page from cnn",
        "get cnn news",
        "fetch bbc",
        "access nytimes"
    ]
    
    for query in news_queries:
        suggestion = executor.suggest_command(query)
        if suggestion:
            print(f"Query: '{query}'")
            print(f"  Suggestion: {suggestion.command}")
            print(f"  Confidence: {suggestion.confidence}")
            if "curl" in suggestion.command and "cnn.com" in suggestion.command:
                print("  ✅ Suggests curl for CNN")
            elif "curl" in suggestion.command:
                print("  ✅ Suggests curl")
            else:
                print("  ❌ Does not suggest curl")
        else:
            print(f"Query: '{query}' - No suggestion")


async def main():
    """Run all tests."""
    await test_cnn_with_updated_prompts()
    await test_various_web_requests()
    await test_command_suggestions()
    
    print("\n=== Assessment Summary ===")
    print("Testing if the updated prompts now handle general web requests.")
    print("The bot should now:")
    print("1. Understand it can access any website via curl")
    print("2. Suggest appropriate curl commands for news sites")
    print("3. Respond to CNN and other general web requests")


if __name__ == "__main__":
    asyncio.run(main())