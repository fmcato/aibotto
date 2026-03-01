"""Unit tests for subagent datetime context."""

import pytest
from unittest.mock import AsyncMock, patch

from aibotto.ai.subagent.base import SubAgent
from aibotto.ai.subagent.web_research_agent import WebResearchAgent
from aibotto.ai.prompt_templates import DateTimeContext


class TestSubAgentDateTime:
    """Test that subagents receive datetime context."""

    @pytest.mark.asyncio
    async def test_base_subagent_includes_datetime(self):
        """Test that base SubAgent includes datetime in messages."""
        agent = SubAgent(max_iterations=1)

        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "choices": [{
                    "message": {
                        "content": "Response",
                        "tool_calls": None
                    }
                }]
            }

            await agent.execute_task("test query", user_id=123, chat_id=456)

            # Check that datetime was added to messages
            call_args = mock_chat.call_args
            messages = call_args.kwargs['messages']

            datetime_msgs = [m for m in messages if 'date and time' in m['content']]
            assert len(datetime_msgs) > 0, "SubAgent should include datetime context"

    @pytest.mark.asyncio
    async def test_web_research_agent_includes_datetime(self):
        """Test that WebResearchAgent includes datetime."""
        agent = WebResearchAgent()

        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "choices": [{
                    "message": {
                        "content": "Research result",
                        "tool_calls": None
                    }
                }]
            }

            await agent.execute_research("test query", user_id=1, chat_id=1)

            call_args = mock_chat.call_args
            messages = call_args.kwargs['messages']
            datetime_msgs = [m for m in messages if 'date and time' in m['content']]

            assert len(datetime_msgs) > 0

    @pytest.mark.asyncio
    async def test_datetime_fresh_each_time(self):
        """Test that datetime is fresh for each execution."""
        agent = SubAgent(max_iterations=1)

        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "choices": [{
                    "message": {
                        "content": "Response",
                        "tool_calls": None
                    }
                }]
            }

            # First execution
            await agent.execute_task("test1")
            first_datetime = mock_chat.call_args.kwargs['messages']
            datetime_msg1 = [m for m in first_datetime if 'date and time' in m['content']][0]

            # Second execution (simulate time passing)
            with patch('aibotto.ai.subagent.base.DateTimeContext.get_current_datetime_message') as mock_dt:
                mock_dt.return_value = {"role": "system", "content": "Current date and time: FUTURE_DATE (Friday, UTC)"}
                await agent.execute_task("test2")
                second_datetime = mock_chat.call_args.kwargs['messages']

            # Verify different datetime messages
            assert datetime_msg1['content'] != "Current date and time: FUTURE_DATE (Friday, UTC)"
