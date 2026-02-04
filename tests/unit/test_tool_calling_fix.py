"""
Test to verify the tool call leakage fix.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations


@pytest.mark.asyncio
async def test_tool_calling_fix():
    """Test that the tool call leakage issue has been fixed."""
    
    # Mock the database operations
    mock_db_ops = AsyncMock(spec=DatabaseOperations)
    mock_db_ops.get_conversation_history.return_value = []
    mock_db_ops.save_message = AsyncMock()
    
    # Create tool calling manager
    tool_manager = ToolCallingManager()
    
    # Mock the LLM client to simulate a proper response
    with patch.object(tool_manager.llm_client, 'chat_completion') as mock_chat:
        
        # First call - LLM wants to use tools
        first_response = AsyncMock()
        first_response.choices = [AsyncMock()]
        first_response.choices[0].message = AsyncMock()
        first_response.choices[0].message.tool_calls = [AsyncMock()]
        first_response.choices[0].message.tool_calls[0].function = AsyncMock()
        first_response.choices[0].message.tool_calls[0].function.name = "execute_cli_command"
        first_response.choices[0].message.tool_calls[0].function.arguments = '{"command": "curl -s -A \\"Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36\\" https://www.cnn.com | grep -i \\"trump\\" | head -10"}'
        first_response.choices[0].message.tool_calls[0].id = "test_tool_call_id"
        
        # Second call - LLM returns a proper response based on tool results
        second_response = AsyncMock()
        second_response.choices = [AsyncMock()]
        second_response.choices[0].message = AsyncMock()
        second_response.choices[0].message.content = 'Here are the current news about Trump: Some fake Trump news content from CNN...'
        
        mock_chat.side_effect = [first_response, second_response]
        
        # Mock CLI executor to return some fake news content
        with patch.object(tool_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = "Some fake Trump news content from CNN..."
            
            # Process the user request
            result = await tool_manager.process_user_request(
                user_id=1,
                chat_id=1,
                message="what are the current news on donald trump",
                db_ops=mock_db_ops
            )
            
            # Check the result
            print(f"Result: {result}")
            
            # Verify the fix: we should get processed content, not raw tool calls
            assert "execute_cli_command" not in result, "Tool call is leaking through instead of being processed"
            assert "Trump" in result, "Response should contain processed news content"
            
            # Verify the calls were made correctly
            mock_chat.assert_called()
            mock_execute.assert_called_once()


if __name__ == "__main__":
    asyncio.run(test_tool_calling_fix())