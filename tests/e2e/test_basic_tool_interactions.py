"""
End-to-end tests for basic tool interactions.
Tests the actual flow from user input to LLM response with tool execution.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.cli.enhanced_executor import EnhancedCLIExecutor
from src.aibotto.config.settings import Config


class TestBasicToolInteractions:
    """Test basic tool interactions with actual implementations."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock(spec=Config)
        settings.OPENAI_API_KEY = "test_key"
        settings.OPENAI_BASE_URL = "https://api.openai.com/v1"
        settings.OPENAI_MODEL = "gpt-3.5-turbo"
        settings.MAX_COMMAND_LENGTH = 1000
        settings.BLOCKED_COMMANDS = "rm -rf,sudo,dd,mkfs,fdisk,format,shutdown,reboot,poweroff,halt"
        settings.ALLOWED_COMMANDS = ""
        settings.MAX_HISTORY_LENGTH = 20
        return settings

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client that returns realistic responses."""
        mock_client = Mock()
        
        # Create a mock response object
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        
        # Create mock tool call objects
        mock_tool_call = Mock()
        mock_function = Mock()
        
        # Mock responses for different query types
        responses = {
            "What day is today?": {
                "content": "Today is Monday, February 3, 2025.",
                "tool_calls": None
            },
            "What's the weather in London?": {
                "content": "The weather in London is partly cloudy with a temperature of 15°C.",
                "tool_calls": [mock_tool_call]
            },
            "Show system information": {
                "content": "System information displayed successfully.",
                "tool_calls": [mock_tool_call]
            },
            "List files in current directory": {
                "content": "Files listed successfully.",
                "tool_calls": [mock_tool_call]
            },
            "What is the capital of France?": {
                "content": "The capital of France is Paris.",
                "tool_calls": None
            },
            "Tell me the current time and weather in London": {
                "content": "I'll get both the time and weather for you.",
                "tool_calls": [mock_tool_call, mock_tool_call]
            }
        }
        
        call_counts = {}
        
        async def mock_completion(messages, **kwargs):
            # Extract the last user message
            user_message = messages[-1]["content"] if messages else ""
            
            # Track call count for this query
            call_key = user_message.lower().strip()
            call_counts[call_key] = call_counts.get(call_key, 0) + 1
            call_num = call_counts[call_key]
            
            # Find matching response
            for query, response in responses.items():
                if query.lower() in user_message.lower():
                    # Set up the mock response structure
                    mock_message.content = response["content"]
                    tool_calls_data = response["tool_calls"]
                    
                    # For multiple tool calls, first call should return tool_calls, second should not
                    if tool_calls_data and call_num == 1:
                        # Create separate tool call objects for each tool call
                        tool_calls = []
                        for i, _ in enumerate(tool_calls_data):
                            tool_call = Mock()
                            function = Mock()
                            function.name = "execute_cli_command"
                            function.arguments = '{"command": "test_command"}'
                            tool_call.function = function
                            tool_call.id = f"test_tool_call_{i}"
                            tool_calls.append(tool_call)
                        mock_message.tool_calls = tool_calls
                    else:
                        mock_message.tool_calls = None
                    
                    mock_choice.message = mock_message
                    mock_response.choices = [mock_choice]
                    return mock_response
            
            # Default response
            mock_message.content = "I understand your request."
            mock_message.tool_calls = None
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response
        
        mock_client.chat_completion = AsyncMock(side_effect=mock_completion)
        return mock_client

    @pytest.fixture
    def enhanced_executor(self, mock_settings):
        """Create enhanced CLI executor with mocked dependencies."""
        executor = EnhancedCLIExecutor()
        return executor

    @pytest.fixture
    def tool_calling_manager(self, mock_settings, mock_llm_client, enhanced_executor):
        """Create tool calling manager with mocked dependencies."""
        with patch('src.aibotto.ai.tool_calling.LLMClient', return_value=mock_llm_client):
            manager = ToolCallingManager()
            manager.cli_executor = enhanced_executor
            return manager

    @pytest.fixture
    def mock_db_ops(self):
        """Create mock database operations."""
        db_ops = Mock()
        db_ops.get_conversation_history = AsyncMock(return_value=[])
        db_ops.save_message = AsyncMock()
        return db_ops

    @pytest.mark.asyncio
    async def test_time_query_uses_date_command(self, tool_calling_manager, mock_db_ops):
        """Test that time queries use the date command."""
        user_query = "What day is today?"
        
        # Mock the CLI executor to simulate successful command execution
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = "Today is Monday, February 3, 2025."
            
            # Mock the LLM client to return a response that uses tools
            with patch.object(tool_calling_manager.llm_client, 'chat_completion') as mock_llm:
                # Create a mock response that indicates tool usage
                mock_response1 = Mock()
                mock_choice1 = Mock()
                mock_message1 = Mock()
                mock_tool_call = Mock()
                mock_function = Mock()
                
                mock_message1.content = "I need to get the current time."
                mock_function.name = "execute_cli_command"
                mock_function.arguments = '{"command": "date"}'
                mock_tool_call.function = mock_function
                mock_tool_call.id = "test_tool_call"
                mock_message1.tool_calls = [mock_tool_call]
                mock_choice1.message = mock_message1
                mock_response1.choices = [mock_choice1]
                
                # Create a mock response for the second call (after tool execution)
                mock_response2 = Mock()
                mock_choice2 = Mock()
                mock_message2 = Mock()
                
                mock_message2.content = "Today is Monday, February 3, 2025."
                mock_choice2.message = mock_message2
                mock_response2.choices = [mock_choice2]
                
                # Set up the mock to return different responses for different calls
                mock_llm.side_effect = [mock_response1, mock_response2]
                
                response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
                
                # Verify the response contains factual information
                assert "Monday" in response
                assert "February" in response
                assert "2025" in response
                
                # Verify that execute_command was called
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_weather_query_uses_curl_command(self, tool_calling_manager, mock_db_ops):
        """Test that weather queries use curl command."""
        user_query = "What's the weather in London?"
        
        # Mock the CLI executor to simulate successful weather API call
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = "The weather in London is partly cloudy with a temperature of 15°C."
            
            # Mock the LLM client to return a response that uses tools
            with patch.object(tool_calling_manager.llm_client, 'chat_completion') as mock_llm:
                # Create a mock response that indicates tool usage
                mock_response1 = Mock()
                mock_choice1 = Mock()
                mock_message1 = Mock()
                mock_tool_call = Mock()
                mock_function = Mock()
                
                mock_message1.content = "I need to get the weather information."
                mock_function.name = "execute_cli_command"
                mock_function.arguments = '{"command": "curl weather"}'
                mock_tool_call.function = mock_function
                mock_tool_call.id = "test_tool_call"
                mock_message1.tool_calls = [mock_tool_call]
                mock_choice1.message = mock_message1
                mock_response1.choices = [mock_choice1]
                
                # Create a mock response for the second call (after tool execution)
                mock_response2 = Mock()
                mock_choice2 = Mock()
                mock_message2 = Mock()
                
                mock_message2.content = "The weather in London is partly cloudy with a temperature of 15°C."
                mock_choice2.message = mock_message2
                mock_response2.choices = [mock_choice2]
                
                # Set up the mock to return different responses for different calls
                mock_llm.side_effect = [mock_response1, mock_response2]
                
                response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
                
                # Verify the response contains weather information
                assert "weather" in response.lower()
            assert "London" in response
            assert "15°C" in response
            
            # Verify that execute_with_suggestion was called
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_info_query_uses_uname_command(self, tool_calling_manager, mock_db_ops):
        """Test that system info queries use uname command."""
        user_query = "Show system information"
        
        # Mock the CLI executor to simulate successful system info call
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = "Linux hostname 5.4.0-42-generic #46-Ubuntu SMP Fri Jul 10 00:24:01 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux"
            
            # Mock the LLM client to return a response that uses tools
            with patch.object(tool_calling_manager.llm_client, 'chat_completion') as mock_llm:
                # Create a mock response that indicates tool usage
                mock_response1 = Mock()
                mock_choice1 = Mock()
                mock_message1 = Mock()
                mock_tool_call = Mock()
                mock_function = Mock()
                
                mock_message1.content = "I need to get the system information."
                mock_function.name = "execute_cli_command"
                mock_function.arguments = '{"command": "uname -a"}'
                mock_tool_call.function = mock_function
                mock_tool_call.id = "test_tool_call"
                mock_message1.tool_calls = [mock_tool_call]
                mock_choice1.message = mock_message1
                mock_response1.choices = [mock_choice1]
                
                # Create a mock response for the second call (after tool execution)
                mock_response2 = Mock()
                mock_choice2 = Mock()
                mock_message2 = Mock()
                
                mock_message2.content = "Linux hostname 5.4.0-42-generic #46-Ubuntu SMP Fri Jul 10 00:24:01 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux"
                mock_choice2.message = mock_message2
                mock_response2.choices = [mock_choice2]
                
                # Set up the mock to return different responses for different calls
                mock_llm.side_effect = [mock_response1, mock_response2]
                
                response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
                
                # Verify the response contains system information
                assert "Linux" in response
            assert "x86_64" in response
            
            # Verify that execute_with_suggestion was called
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_list_query_uses_ls_command(self, tool_calling_manager, mock_db_ops):
        """Test that file list queries use ls command."""
        user_query = "List files in current directory"
        
        # Mock the CLI executor to simulate successful file listing
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = "total 16\ndrwxr-xr-x 2 user user 4096 Feb  3 10:00 .\ndrwxr-xr-x 3 user user 4096 Feb  3 10:00 ..\n-rw-r--r-- 1 user user  123 Feb  3 10:00 test.txt"
            
            # Mock the LLM client to return a response that uses tools
            with patch.object(tool_calling_manager.llm_client, 'chat_completion') as mock_llm:
                # Create a mock response that indicates tool usage
                mock_response1 = Mock()
                mock_choice1 = Mock()
                mock_message1 = Mock()
                mock_tool_call = Mock()
                mock_function = Mock()
                
                mock_message1.content = "I need to get the file listing."
                mock_function.name = "execute_cli_command"
                mock_function.arguments = '{"command": "ls -la"}'
                mock_tool_call.function = mock_function
                mock_tool_call.id = "test_tool_call"
                mock_message1.tool_calls = [mock_tool_call]
                mock_choice1.message = mock_message1
                mock_response1.choices = [mock_choice1]
                
                # Create a mock response for the second call (after tool execution)
                mock_response2 = Mock()
                mock_choice2 = Mock()
                mock_message2 = Mock()
                
                mock_message2.content = "total 16\ndrwxr-xr-x 2 user user 4096 Feb  3 10:00 .\ndrwxr-xr-x 3 user user 4096 Feb  3 10:00 ..\n-rw-r--r-- 1 user user  123 Feb  3 10:00 test.txt"
                mock_choice2.message = mock_message2
                mock_response2.choices = [mock_choice2]
                
                # Set up the mock to return different responses for different calls
                mock_llm.side_effect = [mock_response1, mock_response2]
                
                response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
                
                # Verify the response contains file information
                assert "total" in response
            assert "test.txt" in response
            
            # Verify that execute_with_suggestion was called
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_general_knowledge_no_tool_calls(self, tool_calling_manager, mock_db_ops):
        """Test that general knowledge queries don't use tools."""
        user_query = "What is the capital of France?"
        
        response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
        
        # Verify the response contains factual information without tool execution
        assert "Paris" in response
        assert "capital" in response.lower()
        assert "France" in response

    @pytest.mark.asyncio
    async def test_uncertainty_detection(self, tool_calling_manager, mock_db_ops):
        """Test that uncertain queries trigger fact verification."""
        user_query = "I'm not sure about this, but what time is it really?"
        
        # Mock the CLI executor to simulate fact verification
        with patch.object(tool_calling_manager.cli_executor, 'execute_with_suggestion') as mock_execute:
            mock_execute.return_value = "Today is Monday, February 3, 2025."
            
            # Mock the LLM client to return a response that triggers uncertainty detection
            with patch.object(tool_calling_manager.llm_client, 'chat_completion') as mock_llm:
                # Create a mock response with uncertain language
                mock_response1 = Mock()
                mock_choice1 = Mock()
                mock_message1 = Mock()
                
                mock_message1.content = "I think it might be Monday, but I'm not sure."
                mock_message1.tool_calls = None
                mock_choice1.message = mock_message1
                mock_response1.choices = [mock_choice1]
                
                # Create a mock response for the second call (after auto-suggestion)
                mock_response2 = Mock()
                mock_choice2 = Mock()
                mock_message2 = Mock()
                
                mock_message2.content = "Today is Monday, February 3, 2025."
                mock_choice2.message = mock_message2
                mock_response2.choices = [mock_choice2]
                
                # Set up the mock to return different responses for different calls
                mock_llm.side_effect = [mock_response1, mock_response2]
                
                response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
                
                # Verify the response contains factual information
                assert "Monday" in response
                assert "February" in response
                
                # Verify that execute_with_suggestion was called for fact verification
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_execution_error_handling(self, tool_calling_manager, mock_db_ops):
        """Test handling of command execution errors."""
        user_query = "Show non-existent file"
        
        # Mock the CLI executor to simulate command error
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = "Error: No such file or directory"
            
            # Mock the LLM client to return a response that uses tools
            with patch.object(tool_calling_manager.llm_client, 'chat_completion') as mock_llm:
                # Create a mock response that indicates tool usage
                mock_response1 = Mock()
                mock_choice1 = Mock()
                mock_message1 = Mock()
                mock_tool_call = Mock()
                mock_function = Mock()
                
                mock_message1.content = "I need to get the file information."
                mock_function.name = "execute_cli_command"
                mock_function.arguments = '{"command": "cat non_existent_file.txt"}'
                mock_tool_call.function = mock_function
                mock_tool_call.id = "test_tool_call"
                mock_message1.tool_calls = [mock_tool_call]
                mock_choice1.message = mock_message1
                mock_response1.choices = [mock_choice1]
                
                # Create a mock response for the second call (after tool execution)
                mock_response2 = Mock()
                mock_choice2 = Mock()
                mock_message2 = Mock()
                
                mock_message2.content = "Error: No such file or directory"
                mock_choice2.message = mock_message2
                mock_response2.choices = [mock_choice2]
                
                # Set up the mock to return different responses for different calls
                mock_llm.side_effect = [mock_response1, mock_response2]
                
                response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
                
                # Verify the response acknowledges the error
                assert "error" in response.lower() or "sorry" in response.lower()
            
            # Verify that execute_with_suggestion was called
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self, tool_calling_manager, mock_db_ops):
        """Test handling of multiple tool calls in a single response."""
        user_query = "Tell me the current time and weather in London"
        
        # Mock the CLI executor to simulate multiple command executions
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.side_effect = [
                "Today is Monday, February 3, 2025.",
                "The weather in London is partly cloudy with a temperature of 15°C."
            ]
            
            # Mock the LLM client to return a response with multiple tool calls
            with patch.object(tool_calling_manager.llm_client, 'chat_completion') as mock_llm:
                # Create a mock response that indicates multiple tool usage
                mock_response1 = Mock()
                mock_choice1 = Mock()
                mock_message1 = Mock()
                mock_tool_call1 = Mock()
                mock_tool_call2 = Mock()
                mock_function1 = Mock()
                mock_function2 = Mock()
                
                mock_message1.content = "I'll get both the time and weather for you."
                mock_function1.name = "execute_cli_command"
                mock_function1.arguments = '{"command": "date"}'
                mock_tool_call1.function = mock_function1
                mock_tool_call1.id = "test_tool_call_1"
                
                mock_function2.name = "execute_cli_command"
                mock_function2.arguments = '{"command": "curl weather"}'
                mock_tool_call2.function = mock_function2
                mock_tool_call2.id = "test_tool_call_2"
                
                mock_message1.tool_calls = [mock_tool_call1, mock_tool_call2]
                mock_choice1.message = mock_message1
                mock_response1.choices = [mock_choice1]
                
                # Create a mock response for the second call (after tool execution)
                mock_response2 = Mock()
                mock_choice2 = Mock()
                mock_message2 = Mock()
                
                mock_message2.content = "Today is Monday, February 3, 2025. The weather in London is partly cloudy with a temperature of 15°C."
                mock_choice2.message = mock_message2
                mock_response2.choices = [mock_choice2]
                
                # Set up the mock to return different responses for different calls
                mock_llm.side_effect = [mock_response1, mock_response2]
                
                response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
                
                # Verify the response contains information from both tools
                assert "Monday" in response
                assert "weather" in response.lower()
                assert "London" in response
                
                # Verify that execute_command was called twice
                assert mock_execute.call_count == 2

    @pytest.mark.asyncio
    async def test_tool_calling_manager_initialization(self, tool_calling_manager):
        """Test that the tool calling manager initializes correctly."""
        assert tool_calling_manager is not None
        assert tool_calling_manager.cli_executor is not None
        assert hasattr(tool_calling_manager, 'process_user_request')

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, tool_calling_manager, mock_db_ops):
        """Test handling of empty or very short queries."""
        user_query = ""
        
        response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
        
        # Verify the response handles empty input gracefully
        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_long_query_handling(self, tool_calling_manager, mock_db_ops):
        """Test handling of very long queries."""
        user_query = "What is the current time and date and weather and system information and file listing and user information and process information and memory information and disk information and network information and everything else you can tell me about this system?"
        
        response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)
        
        # Verify the response handles long input gracefully
        assert response is not None
        assert len(response) > 0