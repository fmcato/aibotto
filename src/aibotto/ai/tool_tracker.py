"""
Tool call tracking and deduplication functionality.
"""

import hashlib
import logging

logger = logging.getLogger(__name__)

# Global tracking for tool call deduplication
_tool_call_tracker: dict[str, set[str]] = {}  # user_chat_id -> set of tool call hashes


class ToolTracker:
    """Tracks tool calls to prevent duplicates and excessive retries."""

    def __init__(self) -> None:
        self._iteration_count = 0  # Track current iteration number
        self._recent_tool_calls: set[str] = set()  # Track calls in recent iterations

    def _generate_tool_call_hash(self, function_name: str, arguments: str) -> str:
        """Generate a unique hash for a tool call to detect duplicates."""
        # Create a deterministic hash of function name and arguments
        # Using usedforsecurity=False since this is not for cryptographic purposes
        call_data = f"{function_name}:{arguments}"
        return hashlib.md5(call_data.encode(), usedforsecurity=False).hexdigest()

    def is_duplicate_tool_call(
        self, function_name: str, arguments: str, user_id: int, chat_id: int = 0
    ) -> bool:
        """Check if this tool call has been executed before in this conversation."""
        call_hash = self._generate_tool_call_hash(function_name, arguments)

        # Check global tracker for this user
        user_key = f"{user_id}_{chat_id}" if chat_id else f"user_{user_id}"
        if user_key not in _tool_call_tracker:
            _tool_call_tracker[user_key] = set()

        # Check if this exact call has been made before
        is_duplicate = call_hash in _tool_call_tracker[user_key]

        if is_duplicate:
            logger.warning(
                f"DUPLICATE TOOL CALL DETECTED: {function_name} with "
                f"arguments {arguments[:100]}... "
                f"User: {user_id}, Chat: {chat_id}, "
                f"Iteration: {self._iteration_count}"
            )
        else:
            _tool_call_tracker[user_key].add(call_hash)
            logger.info(
                f"New tool call: {function_name}, Arguments: {arguments[:100]}..., "
                f"User: {user_id}, Chat: {chat_id}, Iteration: {self._iteration_count}"
            )

        return is_duplicate

    def is_similar_tool_call(
        self, function_name: str, arguments: str, user_id: int, chat_id: int = 0
    ) -> bool:
        """Check if this tool call is similar to a previous one (same function,
        different args)."""
        # Check for similar function calls that might indicate retry logic issues
        user_key = f"{user_id}_{chat_id}" if chat_id else f"user_{user_id}"

        if user_key not in _tool_call_tracker:
            return False

        existing_calls = _tool_call_tracker[user_key]

        # Check if we have calls to the same function with different arguments
        for call_hash in existing_calls:
            try:
                # Parse the hash to extract function name
                # Format: function_name:arguments_hash
                if ":" in call_hash:
                    existing_func_name = call_hash.split(":", 1)[0]
                    if existing_func_name == function_name:
                        logger.info(
                            f"Similar tool call detected: {function_name} "
                            f"(may indicate retry logic issue)"
                        )
                        return True
            except Exception:
                continue

        return False

    def should_prevent_retry(
        self, function_name: str, arguments: str, user_id: int, chat_id: int = 0
    ) -> bool:
        """Intelligently determine if a tool call should be prevented based on
        retry patterns."""
        user_key = f"{user_id}_{chat_id}" if chat_id else f"user_{user_id}"

        if user_key not in _tool_call_tracker:
            return False

        existing_calls = _tool_call_tracker[user_key]

        # Count calls to the same function
        same_function_calls = 0
        for call_hash in existing_calls:
            try:
                if ":" in call_hash:
                    existing_func_name = call_hash.split(":", 1)[0]
                    if existing_func_name == function_name:
                        same_function_calls += 1
            except Exception:
                continue

        # Prevent retry if:
        # 1. Same function called more than 3 times (excessive)
        # 2. Complex calculations called more than once (unnecessary retry)
        # 3. Simple commands called more than 5 times (clearly stuck)
        if same_function_calls > 3:
            logger.warning(
                f"Excessive function calls detected: {function_name} called "
                f"{same_function_calls} times"
            )
            return True

        # Special handling for different types of tools
        if "python3" in arguments.lower():
            # Complex calculations shouldn't be retried
            if same_function_calls > 1:
                logger.warning(
                    f"Preventing retry of complex calculation: {function_name}"
                )
                return True
        elif function_name == "execute_cli_command":
            # Other CLI commands shouldn't be retried excessively
            if same_function_calls > 5:
                logger.warning(f"Excessive CLI command retries: {function_name}")
                return True

        return False

    def track_tool_call(self, function_name: str, arguments: str) -> None:
        """Track this call in recent calls (keep last 10 calls)."""
        call_hash = self._generate_tool_call_hash(function_name, arguments)
        self._recent_tool_calls.add(call_hash)
        if len(self._recent_tool_calls) > 10:
            self._recent_tool_calls.pop()

    def increment_iteration(self) -> None:
        """Increment the iteration counter."""
        self._iteration_count += 1

    def reset_tracking(self) -> None:
        """Reset tracking for new request."""
        self._iteration_count = 0

    def reset_stateless_tracking(self) -> None:
        """Reset tracking for stateless processing - this is critical for CLI usage."""
        self._iteration_count = 0
        
        # Also reset the global tracker to prevent cross-session duplicates
        global _tool_call_tracker
        user_key = "user_cli_session"
        if user_key in _tool_call_tracker:
            _tool_call_tracker[user_key].clear()

    def cleanup_old_entries(self, max_age_hours: int = 24) -> None:
        """Clean up old entries from the global tracker to prevent memory leaks.

        Args:
            max_age_hours: Maximum age of entries to keep (default: 24 hours)
        """
        # Simple cleanup: remove empty user entries to prevent memory growth
        global _tool_call_tracker
        empty_users = [
            user_key for user_key, calls in _tool_call_tracker.items()
            if len(calls) == 0
        ]
        for user_key in empty_users:
            del _tool_call_tracker[user_key]

    @staticmethod
    def clear_global_tracker() -> None:
        """Clear the entire global tracker - useful for tests."""
        global _tool_call_tracker
        _tool_call_tracker.clear()
        logger.debug("Cleared global tool call tracker")