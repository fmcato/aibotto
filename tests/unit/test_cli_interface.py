"""
Unit tests for CLI interface.
"""

import pytest
from unittest.mock import AsyncMock, patch

from aibotto.cli_interface import parse_args, run_prompt, main
from aibotto.ai.tool_calling import ToolCallingManager


class TestCLIInterface:
    """Tests for CLI interface functionality."""

    def test_parse_args_single_word(self) -> None:
        """Test parsing single word prompt."""
        with patch("sys.argv", ["aibotto-cli", "hello"]):
            args = parse_args()
            assert args.prompt == ["hello"]
            assert args.verbose is False

    def test_parse_args_multiple_words(self) -> None:
        """Test parsing multi-word prompt."""
        with patch("sys.argv", ["aibotto-cli", "what", "time", "is", "it"]):
            args = parse_args()
            assert args.prompt == ["what", "time", "is", "it"]
            assert args.verbose is False

    def test_parse_args_with_verbose(self) -> None:
        """Test parsing with verbose flag."""
        with patch("sys.argv", ["aibotto-cli", "-v", "test"]):
            args = parse_args()
            assert args.prompt == ["test"]
            assert args.verbose is True

    def test_parse_args_verbose_long(self) -> None:
        """Test parsing with long verbose flag."""
        with patch("sys.argv", ["aibotto-cli", "--verbose", "test"]):
            args = parse_args()
            assert args.verbose is True

    @pytest.mark.asyncio
    async def test_run_prompt_returns_response(self) -> None:
        """Test run_prompt returns the response from ToolCallingManager."""
        mock_response = "The current time is 12:00 PM"

        with patch.object(
            ToolCallingManager,
            "process_prompt_stateless",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await run_prompt("what time is it")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_run_prompt_with_tool_call(self) -> None:
        """Test run_prompt handles tool calls correctly."""
        mock_response = "Today is Monday, January 1st"

        with patch.object(
            ToolCallingManager,
            "process_prompt_stateless",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await run_prompt("what day is today")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_run_prompt_propagates_error(self) -> None:
        """Test run_prompt propagates exceptions to caller."""
        with patch.object(
            ToolCallingManager,
            "process_prompt_stateless",
            new_callable=AsyncMock,
            side_effect=Exception("API error"),
        ):
            with pytest.raises(Exception, match="API error"):
                await run_prompt("test prompt")

    def test_main_config_validation_failure(self, capsys: pytest.CaptureFixture) -> None:
        """Test main exits on config validation failure."""
        with (
            patch("sys.argv", ["aibotto-cli", "test"]),
            patch(
                "aibotto.cli_interface.Config.validate_config",
                return_value=False,
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Configuration validation failed" in captured.err

    def test_main_successful_response(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """Test main prints response on success."""
        mock_response = "Hello! How can I help you?"

        with (
            patch("sys.argv", ["aibotto-cli", "hello"]),
            patch(
                "aibotto.cli_interface.Config.validate_config",
                return_value=True,
            ),
            patch(
                "aibotto.cli_interface.run_prompt",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            main()

        captured = capsys.readouterr()
        assert mock_response in captured.out

    def test_main_verbose_mode(self, capsys: pytest.CaptureFixture) -> None:
        """Test verbose mode prints prompt to stderr."""
        mock_response = "Response"

        with (
            patch("sys.argv", ["aibotto-cli", "-v", "test", "prompt"]),
            patch(
                "aibotto.cli_interface.Config.validate_config",
                return_value=True,
            ),
            patch(
                "aibotto.cli_interface.run_prompt",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            main()

        captured = capsys.readouterr()
        assert "test prompt" in captured.err

    def test_main_keyboard_interrupt(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """Test main handles keyboard interrupt."""
        with (
            patch("sys.argv", ["aibotto-cli", "test"]),
            patch(
                "aibotto.cli_interface.Config.validate_config",
                return_value=True,
            ),
            patch(
                "aibotto.cli_interface.run_prompt",
                side_effect=KeyboardInterrupt(),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 130
        captured = capsys.readouterr()
        assert "Cancelled" in captured.err

    def test_main_exception_handling(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """Test main handles exceptions."""
        with (
            patch("sys.argv", ["aibotto-cli", "test"]),
            patch(
                "aibotto.cli_interface.Config.validate_config",
                return_value=True,
            ),
            patch(
                "aibotto.cli_interface.run_prompt",
                side_effect=RuntimeError("Something went wrong"),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Something went wrong" in captured.err


class TestToolCallingManagerStateless:
    """Tests for stateless tool calling functionality."""

    @pytest.mark.asyncio
    async def test_process_prompt_stateless_simple(self) -> None:
        """Test stateless processing returns response."""
        manager = ToolCallingManager()
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "Hello! How can I assist you today?",
                    }
                }
            ]
        }

        with patch.object(
            manager.llm_client,
            "chat_completion",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await manager.process_prompt_stateless("Hello")
            assert result == "Hello! How can I assist you today?"

    @pytest.mark.asyncio
    async def test_process_prompt_stateless_with_tool_call(self) -> None:
        """Test stateless processing with tool call."""
        manager = ToolCallingManager()

        # First response has tool call, second has final answer
        responses = [
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call_123",
                                    "function": {
                                        "name": "execute_cli_command",
                                        "arguments": '{"command": "date"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "content": "The current date is January 1, 2024.",
                        }
                    }
                ]
            },
        ]

        with patch.object(
            manager.llm_client,
            "chat_completion",
            new_callable=AsyncMock,
            side_effect=responses,
        ):
            with patch.object(
                manager.cli_executor,
                "execute_command",
                new_callable=AsyncMock,
                return_value="Mon Jan 1 12:00:00 UTC 2024",
            ):
                result = await manager.process_prompt_stateless("What day is it?")
                assert "January 1, 2024" in result

    @pytest.mark.asyncio
    async def test_process_prompt_stateless_web_search(self) -> None:
        """Test stateless processing with web search tool."""
        manager = ToolCallingManager()

        responses = [
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call_456",
                                    "function": {
                                        "name": "search_web",
                                        "arguments": '{"query": "latest news"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "content": "Here are the latest news headlines...",
                        }
                    }
                ]
            },
        ]

        with patch.object(
            manager.llm_client,
            "chat_completion",
            new_callable=AsyncMock,
            side_effect=responses,
        ):
            with patch(
                "aibotto.ai.tool_calling.search_web",
                new_callable=AsyncMock,
                return_value="News results here",
            ):
                result = await manager.process_prompt_stateless("What's the news?")
                assert "latest news" in result

    @pytest.mark.asyncio
    async def test_process_prompt_stateless_error_handling(self) -> None:
        """Test stateless processing handles errors."""
        manager = ToolCallingManager()

        with patch.object(
            manager.llm_client,
            "chat_completion",
            new_callable=AsyncMock,
            side_effect=Exception("API connection failed"),
        ):
            result = await manager.process_prompt_stateless("Hello")
            assert "Error" in result
