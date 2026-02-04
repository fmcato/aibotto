"""
Debug test to reproduce security and tool call exposure issues.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.cli.security import SecurityManager
from src.aibotto.db.operations import DatabaseOperations


async def test_security_manager():
    """Test if curl is being blocked."""
    print("=== Testing Security Manager ===")
    
    security_manager = SecurityManager()
    
    # Test curl command
    curl_command = "curl 'https://wttr.in/London?format=3'"
    result = await security_manager.validate_command(curl_command)
    print(f"Curl command validation: {result}")
    
    # Test other safe commands
    safe_commands = [
        "date",
        "ls -la",
        "pwd",
        "uname -a"
    ]
    
    for cmd in safe_commands:
        result = await security_manager.validate_command(cmd)
        print(f"'{cmd}' validation: {result}")


async def test_tool_call_exposure():
    """Test if tool calls are being exposed to users."""
    print("\n=== Testing Tool Call Exposure ===")
    
    # Create a mock response that includes tool calls
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "execute_cli_command"
    mock_tool_call.function.arguments = '{"command": "curl wttr.in"}'
    mock_tool_call.id = "tool_call_123"
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Let me get the weather information for you."
    mock_response.choices[0].message.tool_calls = [mock_tool_call]
    
    # Mock the CLI executor to return a successful result
    mock_executor = MagicMock()
    mock_executor.execute_command = AsyncMock(return_value="Weather: 15°C, partly cloudy")
    
    # Create the manager with mocked dependencies
    manager = ToolCallingManager()
    manager.llm_client = MagicMock()
    manager.cli_executor = mock_executor
    
    # Mock the second LLM response (after tool execution)
    mock_final_response = MagicMock()
    mock_final_response.choices = [MagicMock()]
    mock_final_response.choices[0].message = MagicMock()
    mock_final_response.choices[0].message.content = "The weather in London is 15°C with partly cloudy skies."
    
    # Set up the LLM client to return different responses
    manager.llm_client.chat_completion = AsyncMock(
        side_effect=[mock_response, mock_final_response]
    )
    
    # Use a real database
    db_ops = DatabaseOperations()
    
    try:
        result = await manager.process_user_request(
            user_id=123,
            chat_id=456,
            message="What's the weather in London?",
            db_ops=db_ops
        )
        
        print(f"Final result: {result}")
        
        # Check if tool call information is exposed
        if "tool_call" in result.lower() or "execute_cli_command" in result:
            print("❌ TOOL CALL INFORMATION EXPOSED TO USER!")
        else:
            print("✅ Tool call information properly hidden from user")
            
        # Check if the result is user-friendly
        if "Error:" in result and "blocked" in result:
            print("❌ COMMAND UNNECESSARILY BLOCKED!")
        else:
            print("✅ Command executed successfully")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    await test_security_manager()
    await test_tool_call_exposure()


if __name__ == "__main__":
    asyncio.run(main())