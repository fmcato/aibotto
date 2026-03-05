"""Unit tests for subagent web search invocation and result processing."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from aibotto.ai.subagent.base import SubAgent


class TestSubAgentWebSearchInvocation:
    """Test that subagent correctly invokes web search and handles results."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Register subagent before each test."""
        from aibotto.ai.subagent import init_subagents
        init_subagents()

    @pytest.mark.asyncio
    async def test_config_driven_subagent_invokes_search_web_correctly(self):
        """Test that config-driven subagent calls search_web with correct parameters."""
        from aibotto.config.subagent_config import LLMProviderConfig, SubAgentDefinition
        from aibotto.ai.subagent.base import SubAgent as ConfigDrivenSubAgent
        from pathlib import Path

        provider = LLMProviderConfig(api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com/v1")
        definition = SubAgentDefinition(
            name="web_research",
            description="Web research agent",
            provider="test",
            model="gpt-3.5-turbo",
            prompt_file="prompt.md",
            system_prompt="You are a web research assistant",
            base_dir=None,
            tools=["search_web"],
            max_iterations=5
        )

        agent = ConfigDrivenSubAgent(definition=definition, provider=provider)

        # Mock LLM response that requests web search
        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "choices": [{
                    "message": {
                        "content": "I'll search for information on this topic.",
                        "tool_calls": [{
                            "id": "call_search_1",
                            "function": {
                                "name": "search_web",
                                "arguments": '{"query": "artificial intelligence", "num_results": 5}'
                            }
                        }]
                    }
                }]
            }

            # Mock web search tool executor
            mock_search_executor = MagicMock()
            mock_search_executor.execute = AsyncMock(return_value="""
Found 5 results for "artificial intelligence":
1. Recent AI Advances (https://example.com/ai-advances) - Explores breakthrough LLMs with improved reasoning capabilities
2. AI Research 2024 (https://example.com/ai-research) - Comprehensive overview of machine learning progress
3. Future of AI (https://example.com/ai-future) - Expert predictions on AGI timeline
4. AI Ethics (https://example.com/ai-ethics) - Discusses responsible AI development
5. AI Applications (https://example.com/ai-apps) - Real-world AI use cases in healthcare
""")

            # Mock the toolset to return our mock executor
            with patch.object(agent._toolset, 'get_executor', return_value=mock_search_executor):
                # Second call: LLM synthesizes from search results
                mock_llm.side_effect = [
                    mock_llm.return_value,
                    {
                        "choices": [{
                            "message": {
                                "content": "Based on my research, recent AI advances include improved LLM reasoning [Recent AI Advances](https://example.com/ai-advances) and comprehensive ML progress [AI Research 2024](https://example.com/ai-research).",
                                "tool_calls": None
                            }
                        }]
                    }
                ]

                result = await agent.execute_task("artificial intelligence", user_id=123, chat_id=456)

                # Verify search_web was called
                mock_search_executor.execute.assert_called_once()
                call_args = mock_search_executor.execute.call_args
                assert call_args[0][0] == '{"query": "artificial intelligence", "num_results": 5}'

    @pytest.mark.asyncio
    async def test_config_driven_web_search_result_format_validation(self):
        """Test that config-driven subagent properly validates and uses web search results."""
        from aibotto.config.subagent_config import LLMProviderConfig, SubAgentDefinition
        from aibotto.ai.subagent.base import SubAgent as ConfigDrivenSubAgent

        provider = LLMProviderConfig(api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com/v1")
        definition = SubAgentDefinition(
            name="web_research",
            description="Web research agent",
            provider="test",
            model="gpt-3.5-turbo",
            prompt_file="prompt.md",
            system_prompt="You are a web research assistant",
            base_dir=None,
            tools=["search_web", "fetch_webpage"],
            max_iterations=5
        )

        agent = ConfigDrivenSubAgent(definition=definition, provider=provider)

        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_llm:
            # Call sequence: search_web, then fetch_webpage
            search_call = {
                "id": "call_search",
                "function": {
                    "name": "search_web",
                    "arguments": '{"query": "test", "num_results": 2}'
                }
            }

            fetch_call = {
                "id": "call_fetch",
                "function": {
                    "name": "fetch_webpage",
                    "arguments": '{"url": "https://example.com/article"}'
                }
            }

            mock_llm.side_effect = [
                {"choices": [{"message": {"content": "Searching...", "tool_calls": [search_call]}}]},
                {"choices": [{"message": {"content": "Fetching article...", "tool_calls": [fetch_call]}}]},
                {"choices": [{"message": {"content": "Article discusses AI developments [Article Title](https://example.com/article).", "tool_calls": None}}]}
            ]

            # Mock tool executors
            mock_search_executor = MagicMock()
            mock_search_executor.execute = AsyncMock(return_value="Results: 1. Test Article (https://example.com/article) - Summary")

            mock_fetch_executor = MagicMock()
            mock_fetch_executor.execute = AsyncMock(return_value="# Test Article\nThis is the full content about AI developments.")

            # Mock the toolset to return appropriate executors
            def mock_get_executor(tool_name):
                if tool_name == "search_web":
                    return mock_search_executor
                elif tool_name == "fetch_webpage":
                    return mock_fetch_executor
                return None

            with patch.object(agent._toolset, 'get_executor', side_effect=mock_get_executor):
                result = await agent.execute_task("test", user_id=100, chat_id=200)

                # Verify both tools were called
                mock_search_executor.execute.assert_called_once()
                mock_fetch_executor.execute.assert_called_once()

                # Verify tool call parameters
                search_call_args = mock_search_executor.execute.call_args
                assert '"query": "test"' in search_call_args[0][0]
                assert '"num_results": 2' in search_call_args[0][0]

                fetch_call_args = mock_fetch_executor.execute.call_args
                assert '"url": "https://example.com/article"' in fetch_call_args[0][0]

                # Verify citations in result
                assert "[Article Title]" in result or "https://example.com/article" in result

    @pytest.mark.asyncio
    async def test_subagent_duplicate_search_prevention(self):
        """Test that subagent prevents duplicate search_web calls."""
        from aibotto.config.subagent_config import LLMProviderConfig, SubAgentDefinition
        from aibotto.ai.subagent.base import SubAgent as ConfigDrivenSubAgent

        provider = LLMProviderConfig(api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com/v1")
        definition = SubAgentDefinition(
            name="web_research",
            description="Web research agent",
            provider="test",
            model="gpt-3.5-turbo",
            prompt_file="prompt.md",
            system_prompt="You are a web research assistant",
            base_dir=None,
            tools=["search_web"],
            max_iterations=5
        )
        
        agent = ConfigDrivenSubAgent(definition=definition, provider=provider)

        # Check first call is not a duplicate
        is_duplicate_first = agent._tracker.is_duplicate_tool_call(
            "search_web", '{"query": "duplicate test", "num_results": 3}',
            user_id=999, chat_id=888
        )
        assert not is_duplicate_first

        # Check second call is detected as duplicate
        is_duplicate_second = agent._tracker.is_duplicate_tool_call(
            "search_web", '{"query": "duplicate test", "num_results": 3}',
            user_id=999, chat_id=888
        )
        assert is_duplicate_second

        # Verify subagent namespace
        namespace_key = agent._tracker.get_namespace_key(
            "search_web", '{"query": "duplicate test", "num_results": 3}',
            user_id=999, chat_id=888
        )
        assert f"subagent_{agent._instance_id}" in namespace_key
        assert "999_888" in namespace_key

    @pytest.mark.asyncio
    async def test_subagent_citation_format(self):
        """Test that subagent generates proper citation format."""
        from aibotto.config.subagent_config import LLMProviderConfig, SubAgentDefinition
        from aibotto.ai.subagent.base import SubAgent as ConfigDrivenSubAgent

        provider = LLMProviderConfig(api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com/v1")
        definition = SubAgentDefinition(
            name="web_research",
            description="Web research agent",
            provider="test",
            model="gpt-3.5-turbo",
            prompt_file="prompt.md",
            system_prompt="You are a web research assistant",
            base_dir=None,
            tools=["search_web"],
            max_iterations=5
        )
        
        agent = ConfigDrivenSubAgent(definition=definition, provider=provider)

        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "choices": [{
                    "message": {
                        "content": "Based on research, the key finding is documented in [Important Paper](https://example.com/paper). Additional context from [Related Work](https://example.com/work) supports this.",
                        "tool_calls": None
                    }
                }]
            }

            result = await agent.execute_task("test topic", user_id=1, chat_id=1)

            # Verify citation format
            assert "[Important Paper](https://example.com/paper)" in result
            assert "[Related Work](https://example.com/work)" in result

    @pytest.mark.asyncio
    async def test_subagent_empty_search_results(self):
        """Test subagent handling of empty search results."""
        from aibotto.config.subagent_config import LLMProviderConfig, SubAgentDefinition
        from aibotto.ai.subagent.base import SubAgent as ConfigDrivenSubAgent

        provider = LLMProviderConfig(api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com/v1")
        definition = SubAgentDefinition(
            name="web_research",
            description="Web research agent",
            provider="test",
            model="gpt-3.5-turbo",
            prompt_file="prompt.md",
            system_prompt="You are a web research assistant",
            base_dir=None,
            tools=["search_web"],
            max_iterations=5
        )
        
        agent = ConfigDrivenSubAgent(definition=definition, provider=provider)

        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_llm:
            search_call = {
                "id": "call_search",
                "function": {
                    "name": "search_web",
                    "arguments": '{"query": "obscure topic", "num_results": 5}'
                }
            }

            mock_llm.side_effect = [
                {"choices": [{"message": {"content": "Searching...", "tool_calls": [search_call]}}]},
                {"choices": [{"message": {"content": "I couldn't find any results for this topic. Please try a different search query.", "tool_calls": None}}]}
            ]

            mock_search_executor = MagicMock()
            mock_search_executor.execute = AsyncMock(return_value="No results found.")

            with patch.object(agent._toolset, 'get_executor', return_value=mock_search_executor):
                result = await agent.execute_task("obscure topic", user_id=5, chat_id=10)

                assert "find" in result.lower() and "results" in result.lower()
