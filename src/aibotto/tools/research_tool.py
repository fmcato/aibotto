"""Research tool that delegates to WebResearchAgent."""

import json
import logging
from typing import Any

from aibotto.ai.subagent.subagent_executor import SubAgentExecutor, SubAgentConfig
from aibotto.tools.base import ToolExecutor

logger = logging.getLogger(__name__)


class ResearchExecutor(ToolExecutor):
    """Executor for research_topic tool using subagent system."""

    async def execute(
        self,
        arguments: str,
        user_id: int = 0,
        db_ops: Any = None,
        chat_id: int = 0,
    ) -> str:
        """Execute research using the web research subagent."""
        try:
            args = json.loads(arguments)
            query = args.get("query", "")
            num_results = args.get("num_results", 5)

            if not query or not query.strip():
                return "Error: Query cannot be empty"

            # Configure subagent execution
            config = SubAgentConfig(
                subagent_name="web_research",
                method="execute_research",
                method_kwargs={"query": query, "num_results": num_results},
                user_id=user_id,
                chat_id=chat_id,
            )

            executor = SubAgentExecutor(config)
            result = await executor.run()

            logger.info(f"Web research subagent completed for query: {query}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in research_tool arguments: {e}")
            return "Error: Invalid arguments format. Expected JSON."
        except Exception as e:
            logger.error(f"Research tool error: {e}")
            return f"Error executing research: {str(e)}"


async def research_topic(
    query: str,
    num_results: int = 5,
) -> str:
    """
    Comprehensive web research using a specialized subagent.

    Finds, evaluates, and synthesizes information from multiple web sources.
    Includes source credibility assessment and inline citations.

    Args:
        query: Research topic or question
        num_results: Number of search results to fetch (default: 5)

    Returns:
        Comprehensive summary with inline citations
    """
    config = SubAgentConfig(
        subagent_name="web_research",
        method="execute_research",
        method_kwargs={"query": query, "num_results": num_results},
    )
    executor = SubAgentExecutor(config)
    return await executor.run()
