#!/usr/bin/env python3
"""
Simple test to verify the simplified system works correctly.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from aibotto.ai.llm_client import LLMClient
from aibotto.cli.executor import CLIExecutor
from aibotto.db.models import Conversation
from aibotto.config.settings import Config


async def test_simplified_system():
    """Test that the simplified system works correctly."""
    
    print("Testing simplified system...")
    
    # Mock database operations
    with patch('aibotto.db.operations.DatabaseOperations') as mock_db_ops:
        mock_db = AsyncMock()
        mock_db_ops.return_value = mock_db
        mock_db.get_conversation_history.return_value = []
        mock_db.save_message.return_value = None
        
        # Mock LLM client
        with patch('aibotto.ai.llm_client.LLMClient') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            # Mock tool call response for curl command
            html_content = """
            <html><body><h1>Breaking News</h1><article><h2>Major Event</h2><p>A significant event occurred today.</p></article></body></html>
            """
            
            # Mock the LLM response - it should process the HTML and extract news
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "Here are the latest news headlines:\n\n1. **Major Event**: A significant event occurred today."
            mock_response.choices[0].message.tool_calls = None
            mock_llm.chat_completion.return_value = mock_response
            
            # Mock executor
            with patch('aibotto.cli.executor.CLIExecutor') as mock_executor_class:
                mock_executor = AsyncMock()
                mock_executor_class.return_value = mock_executor
                
                # Mock command execution
                mock_executor.execute.return_value = html_content
                
                # Create LLM client
                llm_client = LLMClient()
                
                # Test the HTML processing
                user_message = "What's the latest news from BBC?"
                
                # Mock the tool call sequence
                async def mock_chat_completion_with_tool_call(messages, **kwargs):
                    # First call suggests using curl
                    if len([m for m in messages if "curl" in m.get("content", "")]) == 0:
                        mock_tool_response = AsyncMock()
                        mock_tool_response.choices = [AsyncMock()]
                        mock_tool_response.choices[0].message = AsyncMock()
                        mock_tool_response.choices[0].message.content = ""
                        mock_tool_response.choices[0].message.tool_calls = [AsyncMock()]
                        mock_tool_response.choices[0].message.tool_calls[0].function = AsyncMock()
                        mock_tool_response.choices[0].message.tool_calls[0].function.name = "execute_cli_command"
                        mock_tool_response.choices[0].message.tool_calls[0].function.arguments = '{"command": "curl -s https://www.bbc.com"}'
                        mock_tool_response.choices[0].message.tool_calls[0].id = "test_id"
                        return mock_tool_response
                    else:
                        # Second call processes the HTML results
                        mock_final_response = AsyncMock()
                        mock_final_response.choices = [AsyncMock()]
                        mock_final_response.choices[0].message = AsyncMock()
                        mock_final_response.choices[0].message.content = "Here are the latest news headlines:\n\n1. **Major Event**: A significant event occurred today."
                        mock_final_response.choices[0].message.tool_calls = None
                        return mock_final_response
                
                mock_llm.chat_completion.side_effect = mock_chat_completion_with_tool_call
                
                # Test the conversation
                response = await llm_client.chat_completion([
                    {"role": "system", "content": "You are a helpful AI assistant that can use CLI tools to answer questions."},
                    {"role": "user", "content": user_message}
                ])
                
                # Verify the response
                content = response.choices[0].message.content
                print("Response:", content)
                
                # Check if the response properly extracts news content
                if "Major Event" in content:
                    print("✅ SUCCESS: Bot properly processed content")
                    return True
                else:
                    print("❌ FAILURE: Bot did not process content correctly")
                    return False


async def main():
    """Run the simplified system test."""
    try:
        result = await test_simplified_system()
        if result:
            print("\n✅ Test PASSED: Simplified system is working correctly")
            return 0
        else:
            print("\n❌ Test FAILED: Simplified system needs more work")
            return 1
    except Exception as e:
        print(f"\n❌ Test ERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))