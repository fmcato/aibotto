"""
Fact-checking utilities for AI responses.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class FactChecker:
    """Fact-checking utilities for AI responses."""
    
    # Keywords that suggest the response might be uncertain or made up
    UNCERTAIN_KEYWORDS = [
        "probably",
        "maybe",
        "might be",
        "could be",
        "I think",
        "I believe",
        "approximately",
        "around",
        "about",
        "roughly",
        "seems like",
        "likely",
        "possibly",
        "potentially",
        "perhaps",
    ]
    
    # Factual query indicators
    FACTUAL_INDICATORS = [
        "time",
        "date",
        "when",
        "what day",
        "what time",
        "current",
        "weather",
        "temperature",
        "files",
        "directory",
        "system",
        "computer",
        "os",
        "version",
        "ip",
        "address",
        "memory",
        "storage",
        "disk",
        "cpu",
        "processor",
        "kernel",
    ]
    
    @classmethod
    def needs_factual_verification(cls, response_content: str, original_message: str) -> bool:
        """Check if the response might need factual verification."""
        response_lower = response_content.lower()
        message_lower = original_message.lower()
        
        # Check if the original message asks for factual information
        has_factual_query = any(
            indicator in message_lower for indicator in cls.FACTUAL_INDICATORS
        )
        
        # Check if the response contains uncertain language
        has_uncertain_language = any(
            keyword in response_lower for keyword in cls.UNCERTAIN_KEYWORDS
        )
        
        # Check if the response is making claims without sources
        has_unsourced_claims = "is " in response_lower and not any(
            tool_word in response_lower
            for tool_word in ["command", "tool", "executed", "current"]
        )
        
        # For certain responses, we should not trigger fact-checking
        # Only trigger if there's uncertainty OR if it's a factual query
        # with unsourced claims
        should_trigger = (
            has_uncertain_language and has_factual_query
        ) or (
            has_factual_query
            and has_unsourced_claims
            and not any(
                certain_word in response_lower
                for certain_word in ["current", "exact", "precise", "specific"]
            )
        )
        
        return should_trigger
    
    @classmethod
    async def get_factual_commands_info(cls) -> str:
        """Get information about available factual commands."""
        return (
            "I can help with factual information like date/time, weather, "
            "system info, and web content."
        )
    
    @classmethod
    async def fact_check_response(cls, query: str, response: str) -> str:
        """Fact-check a response using available tools."""
        return "I'll help verify this information using available tools."