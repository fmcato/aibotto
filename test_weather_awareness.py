#!/usr/bin/env python3
"""
Simple test to check if the bot is aware of its internet access capabilities.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations
from unittest.mock import AsyncMock, MagicMock, patch


async def test_weather_query():
    """Test how the bot responds to a weather query."""
    print("=== Testing Bot's Weather Query Response ===")
    
    # Create the tool calling manager
    manager = ToolCallingManager()
    
    # Mock the LLM client to return realistic responses
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "execute_cli_command"
    mock_tool_call.function.arguments = '{"command": "curl wttr.in/London?format=3"}'
    mock_tool_call.id = "weather_tool_123"
    
    # First response - indicates it will use tools
    mock_first_response = MagicMock()
    mock_first_response.choices = [MagicMock()]
    mock_first_response.choices[0].message = MagicMock()
    mock_first_response.choices[0].message.content = "Let me get the weather information for you."
    mock_first_response.choices[0].message.tool_calls = [mock_tool_call]
    
    # Second response - after tool execution
    mock_second_response = MagicMock()
    mock_second_response.choices = [MagicMock()]
    mock_second_response.choices[0].message = MagicMock()
    mock_second_response.choices[0].message.content = "The weather in London is 15°C with partly cloudy skies."
    
    # Set up the LLM client to return different responses
    manager.llm_client.chat_completion = AsyncMock(
        side_effect=[mock_first_response, mock_second_response]
    )
    
    # Mock the CLI executor to return weather data
    manager.cli_executor.execute_command = AsyncMock(
        return_value="Weather: 15°C, partly cloudy"
    )
    
    # Use a real database (in-memory)
    db_ops = DatabaseOperations()
    
    try:
        # Test the weather query
        result = await manager.process_user_request(
            user_id=123,
            chat_id=456,
            message="What's the weather in London?",
            db_ops=db_ops
        )
        
        print(f"Bot's response: {result}")
        
        # Check if the bot understands it has internet access
        if "curl" in str(manager.cli_executor.execute_command.call_args):
            print("✅ Bot correctly identified it needs to use curl (internet access)")
        else:
            print("❌ Bot did not identify curl as needed")
            
        # Check if the response is weather-focused
        if "weather" in result.lower():
            print("✅ Bot provided weather information")
        else:
            print("❌ Bot did not provide weather information")
            
        # Check LLM call count (should be 2: one for tool calling, one for final response)
        if manager.llm_client.chat_completion.call_count == 2:
            print("✅ Bot made appropriate LLM calls (tool calling + final response)")
        else:
            print(f"❌ Bot made {manager.llm_client.chat_completion.call_count} LLM calls (expected 2)")
            
        return result
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_internet_awareness():
    """Test if the bot understands it has internet access for various queries."""
    print("\n=== Testing Internet Awareness ===")
    
    test_queries = [
        "What's the weather today?",
        "Check the weather in New York",
        "What's the temperature outside?",
        "Get me the weather forecast"
    ]
    
    manager = ToolCallingManager()
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        
        # Mock a simple tool call response
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        mock_tool_call.function.arguments = '{"command": "curl wttr.in?format=3"}'
        mock_tool_call.id = "tool_123"
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        
        manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
        manager.cli_executor.execute_command = AsyncMock(return_value="Weather data")
        
        db_ops = DatabaseOperations()
        
        try:
            await manager.process_user_request(123, 456, query, db_ops)
            
            # Check if it suggests curl
            last_command = manager.cli_executor.execute_command.call_args[0][0]
            if "curl" in last_command:
                print("  ✅ Uses curl (internet)")
            else:
                print("  ❌ Does not use curl")
                
        except Exception as e:
            print(f"  Error: {e}")


async def main():
    """Run all tests."""
    await test_weather_query()
    await test_internet_awareness()
    
    print("\n=== Test Summary ===")
    print("This test checks if the bot:")
    print("1. Understands it can use curl for weather queries")
    print("2. Makes appropriate tool calls for internet data")
    print("3. Provides weather-focused responses")
    print("4. Uses the correct LLM call pattern")


if __name__ == "__main__":
    asyncio.run(main())