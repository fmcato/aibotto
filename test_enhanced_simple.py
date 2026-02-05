#!/usr/bin/env python3
"""
Simple test to verify enhanced tool calling functionality.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


async def test_enhanced_tool_calling():
    """Test enhanced tool calling functionality."""
    
    # Create mock database operations
    mock_db_ops = MagicMock()
    mock_db_ops.get_conversation_history = AsyncMock(return_value=[])
    mock_db_ops.save_message = AsyncMock()
    
    # Create mock LLM client and CLI executor
    mock_llm_client = MagicMock()
    mock_cli_executor = MagicMock()
    
    # Mock the specific methods that will be called
    mock_llm_client.chat_completion = AsyncMock()
    mock_cli_executor.execute_command = AsyncMock(return_value="Command executed successfully")
    
    # Patch the methods in the actual module
    with patch('src.aibotto.ai.tool_calling.LLMClient') as mock_llm_client_class:
        with patch('src.aibotto.ai.tool_calling.CLIExecutor') as mock_cli_executor_class:
            # Configure the classes to return our mocks
            mock_llm_client_class.return_value = mock_llm_client
            mock_cli_executor_class.return_value = mock_cli_executor
            
            # Import and create the manager
            from src.aibotto.ai.tool_calling import ToolCallingManager
            
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
            mock_llm_client.chat_completion.side_effect = [mock_response, final_response]
            
            # Create manager
            manager = ToolCallingManager()
            
            # Execute
            result = await manager.process_user_request(
                user_id=1, chat_id=1, message="What day is today?", db_ops=mock_db_ops
            )
            
            # Verify
            print(f"Result: {result}")
            print(f"LLM client calls: {mock_llm_client.chat_completion.call_count}")
            print(f"CLI executor calls: {mock_cli_executor.execute_command.call_count}")
            
            # Assertions
            assert result == "The current date is 2024-01-15"
            assert mock_llm_client.chat_completion.call_count == 2
            assert mock_cli_executor.execute_command.call_count == 1
            
            print("✅ Test passed! Enhanced tool calling works correctly.")


if __name__ == "__main__":
    asyncio.run(test_enhanced_tool_calling())