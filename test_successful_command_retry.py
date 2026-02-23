"""
Test to reproduce the actual duplicate tool calls scenario where commands complete successfully
but the LLM retries because it wants to provide better answers.
"""

import asyncio
import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.insert(0, 'src')

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TestSuccessfulCommandRetry:
    """Test scenario where commands complete successfully but LLM retries."""

    def __init__(self):
        self.tool_manager = ToolCallingManager()
        self.setup_mocks()

    def setup_mocks(self):
        """Set up mock objects for testing."""
        # Mock LLM client to simulate LLM wanting to retry successful commands
        self.tool_manager.llm_client = MagicMock()

        # Mock CLI executor to simulate successful prime calculation
        mock_cli_executor = MagicMock()
        
        async def successful_prime_calculation(arguments, user_id, db_ops, chat_id):
            logger.info("Prime calculation completed successfully")
            # Return a simple result that might make the LLM want to retry
            result = "15458637"
            logger.info(f"Calculation result: {result}")
            return result

        mock_cli_executor.execute = AsyncMock(side_effect=successful_prime_calculation)
        
        # Replace the CLI executor in the registry
        from src.aibotto.tools.tool_registry import tool_registry
        tool_registry.register_executor("execute_cli_command", mock_cli_executor)

        # Mock database operations
        self.mock_db = AsyncMock()
        self.mock_db.get_conversation_history.return_value = []
        self.mock_db.save_message.return_value = None

    def create_mock_llm_responses_retry_scenario(self):
        """Create mock LLM responses that simulate successful command retry."""
        
        # First response: LLM calculates the prime
        first_response = {
            "choices": [{
                "message": {
                    "content": "I need to calculate the 1 millionth prime number.",
                    "tool_calls": [
                        {
                            "id": "tool_call_1",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "python3 -c \"print(calc_nth_prime(1000000))\""}'
                            }
                        }
                    ]
                }
            }]
        }

        # Second response: LLM retries with same command (this is the problem!)
        # The LLM got the result but wants to provide more explanation or verify
        second_response = {
            "choices": [{
                "message": {
                    "content": "Let me verify this result and provide more details about the prime number.",
                    "tool_calls": [
                        {
                            "id": "tool_call_2",
                            "type": "function",
                            "function": {
                                "name": "execute_cli_command",
                                "arguments": '{"command": "python3 -c \"print(calc_nth_prime(1000000))\""}'
                            }
                        }
                    ]
                }
            }]
        }

        # Third response: LLM finally gives final answer
        final_response = {
            "choices": [{
                "message": {
                    "content": "After calculating and verifying, the 1,000,000th prime number is 15,485,863. This is a large prime number that took significant computational resources to identify.",
                    "tool_calls": []
                }
            }]
        }

        return [first_response, second_response, final_response]

    async def test_successful_command_retry_scenario(self):
        """Test that reproduces LLM retrying successful commands."""
        logger.info("=== STARTING SUCCESSFUL COMMAND RETRY TEST ===")
        
        # Set up the mock LLM responses
        mock_responses = self.create_mock_llm_responses_retry_scenario()
        self.tool_manager.llm_client.chat_completion = AsyncMock(side_effect=mock_responses)

        # Test the exact query that causes the issue
        query = "what's the 1 millionth prime number?"
        
        logger.info(f"Testing query: '{query}'")
        logger.info("This should show LLM retrying a successful command...")

        try:
            # Process the user request
            result = await self.tool_manager.process_user_request(
                user_id=12345,
                chat_id=67890,
                message=query,
                db_ops=self.mock_db
            )

            logger.info(f"Final result: {result}")
            logger.info("=== TEST COMPLETED ===")

            # Analyze the results
            self.analyze_results()

        except Exception as e:
            logger.error(f"Test failed with error: {e}")
            raise

    def analyze_results(self):
        """Analyze the test results to understand LLM retry behavior."""
        logger.info("=== ANALYZING LLM RETRY BEHAVIOR ===")
        
        # Check total LLM calls made
        total_llm_calls = self.tool_manager.llm_client.chat_completion.call_count
        logger.info(f"Total LLM calls made: {total_llm_calls}")
        
        # Check if we detected duplicate calls
        from src.aibotto.ai.tool_calling import _tool_call_tracker
        
        for user_key, tool_calls in _tool_call_tracker.items():
            logger.info(f"User {user_key} executed {len(tool_calls)} unique tool calls:")
            for call_hash in tool_calls:
                logger.info(f"  - Tool call hash: {call_hash}")
        
        # Check if duplicate calls were prevented
        if total_llm_calls > 2:
            logger.warning("🚨 LLM made more calls than expected - indicates retry behavior")
            logger.warning("This suggests the LLM is not satisfied with simple results and wants to retry")
        
        # Check if our duplicate detection worked
        expected_calls = 1  # Should only execute the command once
        actual_calls = len(next(iter(_tool_call_tracker.values()), set()))
        
        if actual_calls == expected_calls:
            logger.info("✅ Duplicate call detection prevented redundant execution")
        else:
            logger.warning(f"⚠️ More calls executed than expected: {actual_calls} vs {expected_calls}")


async def main():
    """Main function to run the retry behavior test."""
    logger.info("Testing successful command retry behavior...")
    
    test = TestSuccessfulCommandRetry()
    
    try:
        await test.test_successful_command_retry_scenario()
        logger.info("✅ Test completed successfully")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())