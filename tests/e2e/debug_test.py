"""
Debug test to understand the tool calling flow.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations


async def debug_direct_response():
    """Debug the direct response flow."""
    tool_manager = ToolCallingManager()
    
    # Mock the LLM response (no tool calls)
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Hello! I'm here to help you with factual information."
    
    tool_manager.llm_client = MagicMock()
    tool_manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
    
    tool_manager.cli_executor = MagicMock()
    tool_manager.cli_executor.execute_with_suggestion = AsyncMock()
    
    db_ops = DatabaseOperations()
    
    # Test the _needs_factual_verification method
    response_content = "Hello! I'm here to help you with factual information."
    original_message = "Hello"
    
    needs_verification = tool_manager._needs_factual_verification(response_content, original_message)
    print(f"Needs factual verification: {needs_verification}")
    
    # Process the user request with error handling
    try:
        result = await tool_manager.process_user_request(
            user_id=12345,
            chat_id=67890,
            message="Hello",
            db_ops=db_ops
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"LLM call count: {tool_manager.llm_client.chat_completion.call_count}")


if __name__ == "__main__":
    asyncio.run(debug_direct_response())