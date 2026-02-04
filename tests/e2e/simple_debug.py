"""
Simple debug test to isolate the issue.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations


async def test_simple_flow():
    """Test the simplest possible flow."""
    print("Creating ToolCallingManager...")
    manager = ToolCallingManager()
    
    print("Creating mock LLM response...")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Hello! I'm here to help you."
    
    print("Setting up mocks...")
    manager.llm_client = MagicMock()
    manager.llm_client.chat_completion = AsyncMock(return_value=mock_response)
    
    manager.cli_executor = MagicMock()
    
    print("Creating database...")
    db_ops = DatabaseOperations()
    
    print("Processing request...")
    try:
        result = await manager.process_user_request(
            user_id=123,
            chat_id=456,
            message="Hello",
            db_ops=db_ops
        )
        print(f"SUCCESS: Result = {result}")
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"LLM calls: {manager.llm_client.chat_completion.call_count}")


if __name__ == "__main__":
    asyncio.run(test_simple_flow())