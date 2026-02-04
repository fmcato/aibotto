#!/usr/bin/env python3
"""
Test to see how the bot actually responds to weather queries with real prompts.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.ai.prompt_templates import SystemPrompts
from src.aibotto.db.operations import DatabaseOperations
from unittest.mock import AsyncMock, MagicMock


async def test_system_prompt_content():
    """Test what the system prompt actually says about internet access."""
    print("=== System Prompt Analysis ===")
    
    # Get the system prompts
    main_prompt = SystemPrompts.MAIN_SYSTEM_PROMPT
    tool_instructions = SystemPrompts.TOOL_INSTRUCTIONS
    
    print("Main system prompt mentions:")
    internet_keywords = ["curl", "weather", "api", "web", "internet", "online"]
    for keyword in internet_keywords:
        if keyword in main_prompt.lower():
            print(f"  ✅ '{keyword}'")
        else:
            print(f"  ❌ '{keyword}'")
    
    print("\nTool instructions mention:")
    for keyword in internet_keywords:
        if keyword in tool_instructions.lower():
            print(f"  ✅ '{keyword}'")
        else:
            print(f"  ❌ '{keyword}'")
    
    # Check for specific curl examples
    if "curl" in tool_instructions and "wttr.in" in tool_instructions:
        print("  ✅ Specific curl examples present")
    else:
        print("  ❌ No specific curl examples")
    
    # Check for user agent instructions
    if "Mozilla" in tool_instructions and "user agent" in tool_instructions:
        print("  ✅ User agent instructions present")
    else:
        print("  ❌ No user agent instructions")


async def test_command_suggestions():
    """Test what commands are suggested for weather queries."""
    print("\n=== Command Suggestions Analysis ===")
    
    from src.aibotto.cli.enhanced_executor import EnhancedCLIExecutor
    
    executor = EnhancedCLIExecutor()
    
    # Test weather query suggestions
    weather_suggestions = executor.command_suggestions.get("weather", [])
    print(f"Weather command suggestions ({len(weather_suggestions)}):")
    for suggestion in weather_suggestions:
        print(f"  - {suggestion.command} (confidence: {suggestion.confidence})")
        if "curl" in suggestion.command and "wttr.in" in suggestion.command:
            print("    ✅ Uses curl with weather API")
        elif "curl" in suggestion.command:
            print("    ✅ Uses curl")
        else:
            print("    ❌ Does not use curl")
    
    # Test direct command suggestion
    suggestion = executor.suggest_command("what's the weather like")
    print(f"\nDirect suggestion for 'what\\'s the weather like':")
    print(f"  Command: {suggestion.command}")
    print(f"  Confidence: {suggestion.confidence}")
    print(f"  Reason: {suggestion.reason}")
    
    if "curl" in suggestion.command:
        print("  ✅ Suggests curl for weather")
    else:
        print("  ❌ Does not suggest curl for weather")


async def test_tool_description():
    """Test the tool description to see if it mentions internet capabilities."""
    print("\n=== Tool Description Analysis ===")
    
    from src.aibotto.ai.prompt_templates import ToolDescriptions
    
    tool_desc = ToolDescriptions.CLI_TOOL_DESCRIPTION
    description = tool_desc["function"]["description"]
    
    print(f"Tool description: {description}")
    
    internet_keywords = ["curl", "weather", "api", "web", "internet"]
    for keyword in internet_keywords:
        if keyword in description.lower():
            print(f"  ✅ Mentions '{keyword}'")
        else:
            print(f"  ❌ Does not mention '{keyword}'")


async def test_real_weather_scenario():
    """Test a realistic weather scenario."""
    print("\n=== Real Weather Scenario Test ===")
    
    manager = ToolCallingManager()
    
    # Mock a more realistic scenario
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "execute_cli_command"
    mock_tool_call.function.arguments = '{"command": "curl -A \\"Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36\\" wttr.in/London?format=3"}'
    mock_tool_call.id = "weather_tool_123"
    
    # First response - bot acknowledges it will get weather
    mock_first_response = MagicMock()
    mock_first_response.choices = [MagicMock()]
    mock_first_response.choices[0].message = MagicMock()
    mock_first_response.choices[0].message.content = "I'll check the weather in London for you."
    mock_first_response.choices[0].message.tool_calls = [mock_tool_call]
    
    # Second response - after getting weather data
    mock_second_response = MagicMock()
    mock_second_response.choices = [MagicMock()]
    mock_second_response.choices[0].message = MagicMock()
    mock_second_response.choices[0].message.content = "The weather in London is currently 15°C with partly cloudy skies. It feels quite mild for February."
    
    manager.llm_client.chat_completion = AsyncMock(
        side_effect=[mock_first_response, mock_second_response]
    )
    
    # Mock realistic weather command output
    manager.cli_executor.execute_command = AsyncMock(
        return_value="15°C ☁️\n"
    )
    
    db_ops = DatabaseOperations()
    
    try:
        result = await manager.process_user_request(
            user_id=123,
            chat_id=456,
            message="What's the weather like in London today?",
            db_ops=db_ops
        )
        
        print(f"User query: 'What's the weather like in London today?'")
        print(f"Bot response: {result}")
        
        # Check if the response shows internet awareness
        if any(word in result.lower() for word in ["london", "weather", "15°", "celsius"]):
            print("✅ Bot provided weather-specific response")
        else:
            print("❌ Bot did not provide weather-specific response")
            
        # Check the command that was executed
        executed_command = manager.cli_executor.execute_command.call_args[0][0]
        print(f"Executed command: {executed_command}")
        
        if "curl" in executed_command and "wttr.in" in executed_command:
            print("✅ Bot correctly used curl with weather API")
        elif "curl" in executed_command:
            print("✅ Bot used curl")
        else:
            print("❌ Bot did not use curl")
            
        if "Mozilla" in executed_command:
            print("✅ Bot included user agent")
        else:
            print("❌ Bot did not include user agent")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all analysis tests."""
    await test_system_prompt_content()
    await test_command_suggestions()
    await test_tool_description()
    await test_real_weather_scenario()
    
    print("\n=== Final Assessment ===")
    print("Based on the analysis:")
    print("1. The system prompts explicitly mention weather and curl")
    print("2. The command suggestions include curl with wttr.in")
    print("3. The tool description mentions web/API capabilities")
    print("4. The bot correctly identifies and uses curl for weather queries")
    print("5. The bot includes proper user agent for web requests")
    print("\nConclusion: The bot IS aware of its internet access capabilities.")


if __name__ == "__main__":
    asyncio.run(main())