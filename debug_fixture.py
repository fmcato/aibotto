import pytest
from unittest.mock import Mock

# Test the fixture directly
def test_mock_llm_client_with_responses():
    from tests.conftest import mock_llm_client_with_responses
    
    client = mock_llm_client_with_responses()
    
    # Test the query detection
    import asyncio
    
    async def test_query():
        call_count = 0
        
        # Patch the chat_completion method to track calls
        original_method = client.chat_completion
        
        async def tracking_chat_completion(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            
            user_message = messages[-1]["content"] if messages else ""
            print(f"Call {call_count}: User message: '{user_message}'")
            
            # Call the original method
            result = await original_method(messages, **kwargs)
            
            # Check if system query is detected
            if call_count == 1 and ("system" in user_message.lower() or "uname" in user_message.lower()):
                print("System query detected in fixture!")
            
            return result
        
        client.chat_completion = tracking_chat_completion
        
        # Test query
        messages = [{"role": "user", "content": "What system information do you have?"}]
        
        result = await client.chat_completion(messages)
        print(f"Result: {result}")
        print(f"Call count: {call_count}")
    
    asyncio.run(test_query())

if __name__ == "__main__":
    test_mock_llm_client_with_responses()