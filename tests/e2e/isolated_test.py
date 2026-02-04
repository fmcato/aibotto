"""
Isolated test to find the exact issue.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.ai.tool_calling import ToolCallingManager


async def test_isolated():
    """Test the exact issue in isolation."""
    print("=== Testing ToolCallingManager.process_user_request ===")
    
    # Create a minimal mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Hello! I'm here to help you."
    mock_response.choices[0].message.tool_calls = None  # No tool calls
    
    # Mock the database operations completely
    mock_db_ops = AsyncMock()
    mock_db_ops.get_conversation_history = AsyncMock(return_value=[])
    mock_db_ops.save_message = AsyncMock()
    
    # Create the manager and mock its dependencies
    with patch('src.aibotto.ai.tool_calling.LLMClient') as mock_llm_class:
        with patch('src.aibotto.ai.tool_calling.EnhancedCLIExecutor') as mock_executor_class:
            manager = ToolCallingManager()
            
            # Mock the LLM client
            manager.llm_client = MagicMock()
            manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
            
            # Mock the CLI executor
            manager.cli_executor = MagicMock()
            
            print("Calling process_user_request...")
            result = await manager.process_user_request(
                user_id=123,
                chat_id=456,
                message="Hello",
                db_ops=mock_db_ops
            )
            
            print(f"Result: {result}")
            print(f"LLM calls: {manager.llm_client.chat_completion.call_count}")
            print(f"DB save calls: {mock_db_ops.save_message.call_count}")
            
            # Check what was saved to DB
            if mock_db_ops.save_message.called:
                for call in mock_db_ops.save_message.call_args_list:
                    print(f"DB save: {call}")


if __name__ == "__main__":
    asyncio.run(test_isolated())