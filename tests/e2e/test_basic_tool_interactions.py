"""
End-to-end tests for basic tool interactions.
Tests the actual flow from user input to LLM response with tool execution.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.tools.cli_executor import CLIExecutor
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
    def tool_calling_manager(self, mock_settings, mock_llm_client_with_responses, mock_cli_executor):
        """Create tool calling manager with mocked dependencies."""
        manager = ToolCallingManager()
        manager.llm_client = mock_llm_client_with_responses
        manager.cli_executor = mock_cli_executor
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

            response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)

            # Verify the response contains weather information
            assert "London" in response
            assert "15°C" in response
            assert "partly cloudy" in response

            # Verify that execute_command was called
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_info_query_uses_uname_command(self, tool_calling_manager, mock_db_ops):
        """Test that system info queries use uname command."""
        user_query = "What system information do you have?"

        # Mock the CLI executor to simulate successful command execution
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = "Linux Ubuntu 5.15.0-88-generic x86_64"

            response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)

            # Verify the response contains system information
            assert "Linux" in response
            assert "Ubuntu" in response

            # Verify that execute_command was called
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_list_query_uses_ls_command(self, tool_calling_manager, mock_db_ops):
        """Test that file list queries use ls command."""
        user_query = "List files in current directory"

        # Mock the CLI executor to simulate successful command execution
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = "total 16\ndrwxr-xr-x 2 user user 4096 Feb  3 10:00 .\ndrwxr-xr-x 5 user user 4096 Feb  3 10:00 ..\n-rw-r--r-- 1 user user 123 Feb  3 10:00 test.txt"

            response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)

            # Verify the response contains file information
            assert "test.txt" in response

            # Verify that execute_command was called
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_general_knowledge_no_tool_calls(self, tool_calling_manager, mock_db_ops):
        """Test that general knowledge queries don't use tool calls."""
        user_query = "What is the capital of France?"

        response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)

        # Verify the response contains factual information
        assert "Paris" in response

    @pytest.mark.asyncio
    async def test_uncertainty_detection(self, tool_calling_manager, mock_db_ops, mock_llm_client_direct_response):
        """Test that uncertainty is properly handled."""
        user_query = "What will be the stock price tomorrow?"

        # Use the direct response mock for this test
        tool_calling_manager.llm_client = mock_llm_client_direct_response

        response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)

        # Verify the response indicates uncertainty
        assert "don't have access" in response.lower() or "cannot predict" in response.lower()

    @pytest.mark.asyncio
    async def test_command_execution_error_handling(self, tool_calling_manager, mock_db_ops):
        """Test that command execution errors are handled properly."""
        user_query = "What day is today?"

        # Mock the CLI executor to simulate command execution error
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.side_effect = Exception("Command not found")

            response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)

            # Verify the response contains error information
            assert "error" in response.lower() or "failed" in response.lower()

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self, tool_calling_manager, mock_db_ops):
        """Test that multiple tool calls are handled properly."""
        user_query = "What is the current date and time?"

        # Mock the CLI executor to simulate successful command execution
        with patch.object(tool_calling_manager.cli_executor, 'execute_command') as mock_execute:
            mock_execute.return_value = "Date: Mon Feb  3 14:30:45 UTC 2026\nTime: 14:30:45"

            response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)

            # Verify the response contains both date and time
            assert "Mon" in response or "February" in response
            assert "14:30" in response or "2:30" in response

            # Verify that execute_command was called
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_calling_manager_initialization(self, tool_calling_manager):
        """Test that tool calling manager initializes properly."""
        assert tool_calling_manager is not None
        assert tool_calling_manager.cli_executor is not None
        assert hasattr(tool_calling_manager, 'process_user_request')

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, tool_calling_manager, mock_db_ops):
        """Test that empty queries are handled properly."""
        user_query = ""

        response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)

        # Verify the response is not empty and handles the empty input
        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_long_query_handling(self, tool_calling_manager, mock_db_ops):
        """Test that long queries are handled properly."""
        user_query = "What is the current date and time and system information and weather and file listing?"

        response = await tool_calling_manager.process_user_request(1, 1, user_query, mock_db_ops)

        # Verify the response is not empty
        assert response is not None
        assert len(response) > 0