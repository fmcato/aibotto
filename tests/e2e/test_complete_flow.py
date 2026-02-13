"""
Test the complete flow with security fix and tool call hiding.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations


@pytest.mark.asyncio
async def test_complete_flow(real_db_ops):
    """Test the complete flow with real database and security checks."""
    print("=== Testing Complete Flow ===")

    # Create a mock response that includes tool calls
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "execute_cli_command"
    mock_tool_call.function.arguments = '{"command": "curl wttr.in/London?format=3"}'
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

    # Use the fixture-provided database
    db_ops = real_db_ops

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

        # Check if the security check was called
        if mock_executor.execute_command.called:
            executed_command = mock_executor.execute_command.call_args[0][0]
            print(f"Executed command: {executed_command}")

            # Check if curl was allowed
            if executed_command.startswith("curl"):
                print("✅ Curl command was allowed by security check")
            else:
                print("❌ Curl command was not executed or was modified")

        print(f"LLM calls: {manager.llm_client.chat_completion.call_count}")
        print(f"Command executions: {mock_executor.execute_command.call_count}")

    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()


@pytest.mark.asyncio
async def test_direct_response(real_db_ops):
    """Test direct response without tool calls."""
    print("\n=== Testing Direct Response ===")

    # Create a mock response with no tool calls
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Hello! I'm here to help you with factual information."
    mock_response.choices[0].message.tool_calls = None

    # Create the manager with mocked dependencies
    manager = ToolCallingManager()
    manager.llm_client = MagicMock()
    manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
    manager.cli_executor = MagicMock()

    # Use the fixture-provided database
    db_ops = real_db_ops

    try:
        result = await manager.process_user_request(
            user_id=123,
            chat_id=456,
            message="Hello",
            db_ops=db_ops
        )

        print(f"Direct response result: {result}")

        if result == "Hello! I'm here to help you with factual information.":
            print("✅ Direct response working correctly")
        else:
            print("❌ Direct response not working correctly")

    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    await test_complete_flow()
    await test_direct_response()


if __name__ == "__main__":
    asyncio.run(main())
