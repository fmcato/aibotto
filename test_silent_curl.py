#!/usr/bin/env python3
"""
Test to verify that curl commands now include -s for silent output.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations
from unittest.mock import AsyncMock, MagicMock


async def test_silent_curl_commands():
    """Test that all curl commands now include -s flag."""
    print("=== Testing Silent Curl Commands ===")
    
    manager = ToolCallingManager()
    
    # Test queries that should generate curl commands
    test_queries = [
        "what's the weather like",
        "grab front page from cnn",
        "get cnn.com",
        "fetch nytimes.com",
        "get website content"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        
        # Mock a tool call response
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "execute_cli_command"
        
        # Let the bot generate the command
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        
        manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
        manager.cli_executor.execute_command = AsyncMock(return_value="Content")
        
        db_ops = DatabaseOperations()
        
        try:
            await manager.process_user_request(123, 456, query, db_ops)
            
            # Check what command was generated
            if mock_tool_call.function.arguments:
                import json
                command_args = json.loads(mock_tool_call.function.arguments)
                command = command_args.get("command", "")
                
                print(f"  Generated command: {command}")
                
                if "-s" in command and "curl" in command:
                    print("  ✅ Includes -s flag (silent mode)")
                elif "curl" in command:
                    print("  ❌ Missing -s flag")
                else:
                    print("  ❌ Not a curl command")
                    
        except Exception as e:
            print(f"  Error: {e}")


async def test_command_suggestions():
    """Test that command suggestions include -s flag."""
    print("\n=== Testing Command Suggestions ===")
    
    from src.aibotto.cli.enhanced_executor import EnhancedCLIExecutor
    
    executor = EnhancedCLIExecutor()
    
    # Test weather suggestions
    weather_suggestions = executor.command_suggestions.get("weather", [])
    print("Weather command suggestions:")
    for suggestion in weather_suggestions:
        print(f"  - {suggestion.command}")
        if "-s" in suggestion.command:
            print("    ✅ Includes -s flag")
        else:
            print("    ❌ Missing -s flag")
    
    # Test news suggestions
    news_suggestions = executor.command_suggestions.get("news", [])
    print("\nNews command suggestions:")
    for suggestion in news_suggestions:
        print(f"  - {suggestion.command}")
        if "-s" in suggestion.command:
            print("    ✅ Includes -s flag")
        else:
            print("    ❌ Missing -s flag")
    
    # Test web suggestions
    web_suggestions = executor.command_suggestions.get("web", [])
    print("\nWeb command suggestions:")
    for suggestion in web_suggestions:
        print(f"  - {suggestion.command}")
        if "-s" in suggestion.command:
            print("    ✅ Includes -s flag")
        else:
            print("    ❌ Missing -s flag")


async def test_direct_suggestions():
    """Test direct command suggestions."""
    print("\n=== Testing Direct Suggestions ===")
    
    from src.aibotto.cli.enhanced_executor import EnhancedCLIExecutor
    
    executor = EnhancedCLIExecutor()
    
    test_cases = [
        ("what's the weather like", "weather"),
        ("get cnn news", "news"),
        ("fetch a website", "web"),
        ("grab front page from cnn", "news")
    ]
    
    for query, expected_type in test_cases:
        suggestion = executor.suggest_command(query)
        if suggestion:
            print(f"Query: '{query}'")
            print(f"  Suggestion: {suggestion.command}")
            print(f"  Expected type: {expected_type}")
            
            if "-s" in suggestion.command:
                print("  ✅ Includes -s flag")
            else:
                print("  ❌ Missing -s flag")
        else:
            print(f"Query: '{query}' - No suggestion")


async def main():
    """Run all tests."""
    await test_silent_curl_commands()
    await test_command_suggestions()
    await test_direct_suggestions()
    
    print("\n=== Summary ===")
    print("Testing that all curl commands now include -s for silent output.")
    print("This prevents progress meters and keeps output clean.")


if __name__ == "__main__":
    asyncio.run(main())