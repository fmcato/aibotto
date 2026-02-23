"""
Test script to reproduce the duplicate tool calls issue with prime number calculation.
This script simulates the exact scenario that causes duplicate tool calls.
"""

import asyncio
import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.insert(0, 'src')

from src.aibotto.ai.tool_calling import ToolCallingManager
from src.aibotto.db.operations import DatabaseOperations

# Set up logging to see the duplicate call detection
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TestPrimeNumberCalculation:
    """Test class to reproduce prime number calculation duplicate calls."""

    def __init__(self):
        self.tool_manager = ToolCallingManager()
        self.setup_mocks()

    def setup_mocks(self):
        """Set up mock objects for testing."""
        # Mock LLM client to simulate the prime number calculation scenario
        self.tool_manager.llm_client = MagicMock()

        # Mock CLI executor to simulate slow/hanging prime calculation
        mock_cli_executor = MagicMock()
        
        # Simulate a very slow prime number calculation that might cause timeout
        async def slow_prime_calculation(arguments, user_id, db_ops, chat_id):
            logger.info("Starting slow prime number calculation...")
            await asyncio.sleep(2)  # Simulate slow calculation
            
            # Simulate a Python script that calculates the 1 millionth prime
            # This would typically be something like:
            # "python3 -c \"print(calc_nth_prime(1000000))\""
            
            # Return a fake result that looks like it came from a calculation
            fake_result = "The 1,000,000th prime number is 15,485,863"
            logger.info(f"Prime calculation completed: {fake_result}")
            return fake_result

        mock_cli_executor.execute = AsyncMock(side_effect=slow_prime_calculation)
        
        # Replace the CLI executor in the registry
        from src.aibotto.tools.tool_registry import tool_registry
        tool_registry.register_executor("execute_cli_command", mock_cli_executor)

        # Mock database operations
        self.mock_db = AsyncMock()
        self.mock_db.get_conversation_history.return_value = []
        self.mock_db.save_message.return_value = None

    def create_mock_llm_responses(self):
        """Create mock LLM responses that simulate the prime number scenario."""
        
        # First response: LLM decides to use Python to calculate the prime
        first_response = {
            "choices": [{
                "message": {
                    "content": "I need to calculate the 1 millionth prime number using Python.",
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

        # Second response: LLM retries with a slightly different approach (this is where duplicates happen)
        second_response = {
            "choices": [{
                "message": {
                    "content": "Let me try a different approach to calculate the prime number.",
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

        # Third response: Final response after successful calculation
        final_response = {
            "choices": [{
                "message": {
                    "content": "The 1,000,000th prime number is 15,485,863.",
                    "tool_calls": []
                }
            }]
        }

        return [first_response, second_response, final_response]

    async def test_prime_number_calculation_reproduction(self):
        """Test that reproduces the duplicate tool call issue."""
        logger.info("=== STARTING PRIME NUMBER CALCULATION TEST ===")
        
        # Set up the mock LLM responses
        mock_responses = self.create_mock_llm_responses()
        self.tool_manager.llm_client.chat_completion = AsyncMock(side_effect=mock_responses)

        # Test the exact query that causes the issue
        query = "what's the 1 millionth prime number?"
        
        logger.info(f"Testing query: '{query}'")
        logger.info("This should demonstrate duplicate tool call detection...")

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
        """Analyze the test results to identify duplicate calls."""
        logger.info("=== ANALYZING RESULTS ===")
        
        # Check if duplicate calls were detected
        from src.aibotto.ai.tool_calling import _tool_call_tracker
        
        for user_key, tool_calls in _tool_call_tracker.items():
            logger.info(f"User {user_key} executed {len(tool_calls)} unique tool calls:")
            for call_hash in tool_calls:
                logger.info(f"  - Tool call hash: {call_hash}")
        
        # Check total LLM calls made
        total_llm_calls = self.tool_manager.llm_client.chat_completion.call_count
        logger.info(f"Total LLM calls made: {total_llm_calls}")
        
        if total_llm_calls > 3:
            logger.warning(f"⚠️  More LLM calls than expected (expected: 3, actual: {total_llm_calls})")
        else:
            logger.info(f"✅ Expected number of LLM calls: {total_llm_calls}")

        # Check if duplicate calls were detected by looking at our global tracker
        duplicate_detected = False
        for user_key, tool_calls in _tool_call_tracker.items():
            if len(tool_calls) < total_llm_calls:
                duplicate_detected = True
                break
        
        if duplicate_detected:
            logger.warning("🚨 DUPLICATE TOOL CALLS DETECTED!")
        else:
            logger.info("✅ No duplicate tool calls detected")


async def main():
    """Main function to run the reproduction test."""
    logger.info("Starting prime number calculation reproduction test...")
    
    test = TestPrimeNumberCalculation()
    
    try:
        await test.test_prime_number_calculation_reproduction()
        logger.info("✅ Test completed successfully")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())