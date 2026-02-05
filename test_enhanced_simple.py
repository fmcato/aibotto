#!/usr/bin/env python3
"""
Simple test to verify enhanced tool calling functionality works.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock


async def test_enhanced_simple():
    """Test enhanced tool calling functionality."""
    
    # Create mock database operations
    mock_db_ops = MagicMock()
    mock_db_ops.get_conversation_history = AsyncMock(return_value=[])
    mock_db_ops.save_message = AsyncMock()
    
    # Import the module
    from src.aibotto.ai.tool_calling import ToolCallingManager
    
    # Create manager
    manager = ToolCallingManager()
    
    # Setup LLM to return a tool call
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.tool_calls = [
        MagicMock(
            id="tool_1",
            function=MagicMock(
                name="execute_cli_command",
                arguments='{"command": "date"}'
            )
        )
    ]
    
    # Setup final response
    final_response = MagicMock()
    final_response.choices = [MagicMock()]
    final_response.choices[0].message = MagicMock()
    final_response.choices[0].message.content = "The current date is 2024-01-15"
    
    # Configure the mock to return different responses for different calls
    manager.llm_client.chat_completion = AsyncMock(side_effect=[mock_response, final_response])
    manager.cli_executor.execute_command = AsyncMock(return_value="Command executed successfully")
    
    # Execute
    result = await manager.process_user_request(
        user_id=1, chat_id=1, message="What day is today?", db_ops=mock_db_ops
    )
    
    # Verify
    print(f"Result: {result}")
    print(f"LLM client calls: {manager.llm_client.chat_completion.call_count}")
    print(f"CLI executor calls: {manager.cli_executor.execute_command.call_count}")
    
    # Assertions
    assert result == "The current date is 2024-01-15"
    assert manager.llm_client.chat_completion.call_count == 2
    assert manager.cli_executor.execute_command.call_count == 1
    
    print("✅ Enhanced tool calling test passed! Tool calls work correctly.")


if __name__ == "__main__":
    asyncio.run(test_enhanced_simple())