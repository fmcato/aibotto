"""Unit tests for subagent datetime context."""

import pytest
from unittest.mock import AsyncMock, patch

from aibotto.ai.subagent.base import SubAgent


class TestSubAgentDateTime:
    """Test that subagents receive datetime context."""

    @pytest.mark.asyncio
    async def test_subagent_includes_datetime(self):
        """Test that SubAgent includes datetime in messages."""
        from aibotto.config.subagent_config import LLMProviderConfig, SubAgentDefinition

        provider = LLMProviderConfig(api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com/v1")
        definition = SubAgentDefinition(
            name="test_agent",
            description="Test agent",
            provider="test",
            model="gpt-3.5-turbo",
            prompt_file="prompt.md",
            system_prompt="You are a test agent",
            base_dir=None,
            tools=[]
        )

        agent = SubAgent(definition=definition, provider=provider)

        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "choices": [{
                    "message": {
                        "content": "Test result",
                        "tool_calls": None
                    }
                }]
            }

            await agent.execute_task("test query", user_id=1, chat_id=1)

            call_args = mock_chat.call_args
            messages = call_args.kwargs['messages']
            datetime_msgs = [m for m in messages if 'date and time' in m['content']]

            assert len(datetime_msgs) > 0
