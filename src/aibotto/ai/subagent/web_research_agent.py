"""Web research subagent with specialized research capabilities."""

import logging
from typing import Any

from aibotto.ai.subagent.base import SubAgent
from aibotto.ai.prompt_templates import ToolDescriptions

logger = logging.getLogger(__name__)


class WebResearchAgent(SubAgent):
    """Specialized subagent for comprehensive web research."""

    def __init__(self):
        super().__init__(max_iterations=5)

    def _get_system_prompt(self) -> str:
        """Get research-specialized system prompt."""
        return """You are a specialized research assistant focused on finding, evaluating, and synthesizing web information.

Your capabilities:
- Search the web for relevant information
- Fetch and read webpage content
- Evaluate source credibility (prioritize .gov, .edu, established news)
- Synthesize information from multiple sources
- Provide inline citations in format [Title](URL)
- Handle research strategy refinement
- Execute multiple tools in parallel for maximum efficiency

Research guidelines:
1. Start with broad search, refine based on results
2. Evaluate credibility before using sources
3. Fetch multiple sources (3-5 recommended) - you can fetch them ALL at once using parallel tool calls
4. Cross-check when sources disagree
5. Synthesize into coherent answer with citations
6. Be transparent about limitations

Efficiency strategy:
- When you have multiple URLs to fetch, call fetch_webpage for ALL of them in parallel
- Use efficient search with appropriate num_results (5-10 for comprehensive research)
- Max iterations: 10 - use them efficiently for search, fetch, and synthesis

Output format:
Provide a comprehensive, well-sourced summary. Include inline citations:
- Direct quotes: "Quote text" [Source Title](URL)
- Information: Information [Source Title](URL)"""

    def _get_tool_definitions(self) -> list[dict[str, Any]]:
        """Subagent only has access to web tools."""
        return [
            ToolDescriptions.WEB_SEARCH_TOOL_DESCRIPTION,
            ToolDescriptions.WEB_FETCH_TOOL_DESCRIPTION,
        ]

    def _register_tools(self) -> None:
        """Register web tools for this subagent instance."""
        from aibotto.tools.executors.web_search_executor import WebSearchExecutor
        from aibotto.tools.executors.web_fetch_executor import WebFetchExecutor

        # Register web search tool
        search_executor = WebSearchExecutor()
        self._toolset.register_tool("search_web", search_executor)

        # Register web fetch tool
        fetch_executor = WebFetchExecutor()
        self._toolset.register_tool("fetch_webpage", fetch_executor)

        logger.info(
            f"WebResearchAgent {self._instance_id}: Registered tools: {self._toolset.get_registered_tools()}"
        )

    async def execute_research(
        self,
        query: str,
        num_results: int = 5,
        user_id: int = 0,
        chat_id: int = 0,
    ) -> str:
        """
        Execute comprehensive research on a topic.

        Args:
            query: Research question or topic
            num_results: Number of search results to consider
            user_id: User ID for proper tracking
            chat_id: Chat ID for proper tracking

        Returns:
            Comprehensive summary with inline citations
        """
        logger.info(
            f"WebResearchAgent {self._instance_id}: Starting research "
            f"(query: {query[:50]}..., user_id: {user_id}, chat_id: {chat_id})"
        )

        task_instructions = (
            f"Research this topic thoroughly. "
            f"Use search_web to find {num_results} relevant sources, "
            f"then fetch_webpage to read and evaluate each source. "
            f"Synthesize your findings into a comprehensive answer "
            f"with inline citations in [Title](URL) format."
        )

        try:
            result = await self.execute_task(
                initial_message=query,
                task_instructions=task_instructions,
                user_id=user_id,
                chat_id=chat_id,
            )
            logger.info(
                f"WebResearchAgent {self._instance_id}: Research completed "
                f"(user_id: {user_id}, chat_id: {chat_id})"
            )
            return result
        except Exception as e:
            logger.error(f"Research subagent error: {e}")
            return f"Research encountered an error: {str(e)}"
