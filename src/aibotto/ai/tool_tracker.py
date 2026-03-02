"""
Tool call tracking and deduplication functionality.
"""

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Global tracking for tool call deduplication
_tool_call_tracker: dict[str, set[str]] = {}  # user_chat_id -> set of tool call hashes


class ToolTracker:
    """Tracks tool calls to prevent duplicates and excessive retries."""

    def __init__(self, instance_id: int | None = None) -> None:
        self._iteration_count = 0  # Track current iteration number
        self._recent_tool_calls: set[str] = set()  # Track calls in recent iterations
        self._instance_id = instance_id  # Optional instance ID for namespacing

        if instance_id:
            logger.info(f"Created namespaced ToolTracker for instance {instance_id}")
        else:
            logger.info("Created global ToolTracker")

    def _generate_tool_call_hash(self, function_name: str, arguments: str) -> str:
        """Generate a unique hash for a tool call to detect duplicates."""
        # Create a deterministic hash of function name and arguments
        # Using usedforsecurity=False since this is not for cryptographic purposes
        call_data = f"{function_name}:{arguments}"
        return hashlib.md5(call_data.encode(), usedforsecurity=False).hexdigest()

    def _get_tracking_key(
        self, function_name: str, user_id: int, chat_id: int = 0
    ) -> str:
        """Get the tracking key for a tool call.

        Args:
            function_name: Name of the function being called
            user_id: User ID
            chat_id: Chat ID

        Returns:
            Tracking key string
        """
        if self._instance_id:
            # Use namespaced key for subagents: subagent_{id}::{user_id}_{chat_id}
            user_key = f"{user_id}_{chat_id}" if chat_id else f"{user_id}"
            return f"subagent_{self._instance_id}::{user_key}"
        else:
            # Use global key for main agent: user_{user_id}_{chat_id}
            user_key = f"{user_id}_{chat_id}" if chat_id else f"user_{user_id}"
            return user_key

    def is_duplicate_tool_call(
        self, function_name: str, arguments: str, user_id: int, chat_id: int = 0
    ) -> bool:
        """Check if this tool call has been executed before in this conversation."""
        call_hash = self._generate_tool_call_hash(function_name, arguments)
        tracking_key = self._get_tracking_key(function_name, user_id, chat_id)

        # Check global tracker for this conversation
        if tracking_key not in _tool_call_tracker:
            _tool_call_tracker[tracking_key] = set()

        # Check if this exact call has been made before
        is_duplicate = call_hash in _tool_call_tracker[tracking_key]

        if is_duplicate:
            prefix = (
                f"SUBAGENT ({self._instance_id})" if self._instance_id else "GLOBAL"
            )
            logger.warning(
                f"{prefix} DUPLICATE TOOL CALL DETECTED: {function_name} with "
                f"arguments {arguments[:100]}... "
                f"Tracking key: {tracking_key}, User: {user_id}, Chat: {chat_id}, "
                f"Iteration: {self._iteration_count}"
            )
        else:
            _tool_call_tracker[tracking_key].add(call_hash)
            prefix = (
                f"SUBAGENT ({self._instance_id})" if self._instance_id else "GLOBAL"
            )
            logger.info(
                f"{prefix} NEW TOOL CALL: {function_name}, Arguments: {arguments[:100]}..., "
                f"Tracking key: {tracking_key}, User: {user_id}, Chat: {chat_id}, "
                f"Iteration: {self._iteration_count}"
            )

        return is_duplicate

    def increment_iteration(self) -> None:
        """Increment the iteration counter."""
        self._iteration_count += 1
        self._recent_tool_calls.clear()
        logger.debug(f"Tracker iteration incremented to {self._iteration_count}")

    def is_similar_tool_call(
        self, function_name: str, arguments: str, user_id: int, chat_id: int = 0
    ) -> bool:
        """Check if this tool call is similar to a previous one (same function,
        different args)."""
        # Check for similar function calls that might indicate retry logic issues
        tracking_key = self._get_tracking_key(function_name, user_id, chat_id)

        if tracking_key not in _tool_call_tracker:
            return False

        existing_calls = _tool_call_tracker[tracking_key]

        # Check if we have calls to the same function with different arguments
        for call_hash in existing_calls:
            try:
                # Parse the hash to extract function name
                # Format: function_name:arguments_hash
                if ":" in call_hash:
                    existing_func_name = call_hash.split(":", 1)[0]
                    if existing_func_name == function_name:
                        prefix = (
                            f"SUBAGENT ({self._instance_id})"
                            if self._instance_id
                            else "GLOBAL"
                        )
                        logger.info(
                            f"{prefix} Similar tool call detected: {function_name} "
                            f"(may indicate retry logic issue)"
                        )
                        return True
            except Exception:
                continue

        return False

    def get_recent_tool_calls(self) -> set[str]:
        """Get the set of tool calls from the most recent iteration."""
        return self._recent_tool_calls.copy()

    def get_call_history(self, user_id: int, chat_id: int = 0) -> list[dict[str, Any]]:
        """Get the complete call history for a user."""
        tracking_key = self._get_tracking_key("dummy", user_id, chat_id)

        if tracking_key not in _tool_call_tracker:
            return []

        return [
            {
                "call_hash": call_hash,
                "function_name": call_hash.split(":", 1)[0]
                if ":" in call_hash
                else "unknown",
            }
            for call_hash in _tool_call_tracker[tracking_key]
        ]

    @classmethod
    def cleanup_old_trackers(cls, max_age_hours: int = 24) -> None:
        """Clean up old tracking data to prevent memory leaks."""
        # This is a placeholder for future implementation
        # In a real system, we would track timestamps and clean old entries
        logger.debug(f"Cleanup of old trackers called (max_age: {max_age_hours}h)")

    @classmethod
    def get_active_tracking_keys(cls) -> list[str]:
        """Get all currently active tracking keys."""
        return list(_tool_call_tracker.keys())

    @classmethod
    def get_tracker_stats(cls) -> dict[str, int]:
        """Get statistics about active trackers."""
        stats = {}
        for key, calls in _tool_call_tracker.items():
            stats[key] = len(calls)
        return stats

    @classmethod
    def clear_user_tracker(cls, user_id: int, chat_id: int = 0) -> None:
        """Clear tracking data for a specific user."""
        # Create a dummy tracker to get the key
        dummy_tracker = ToolTracker()
        tracking_key = dummy_tracker._get_tracking_key("dummy", user_id, chat_id)
        if tracking_key in _tool_call_tracker:
            del _tool_call_tracker[tracking_key]
            logger.info(f"Cleared tracker for user {user_id}, chat {chat_id}")

    @classmethod
    def cleanup_empty_trackers(cls) -> None:
        """Clean up tracking keys that have no calls."""
        empty_users = [
            user_key
            for user_key, calls in _tool_call_tracker.items()
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

    # Additional methods for compatibility with existing code
    def track_tool_call(
        self, function_name: str, arguments: str, user_id: int = 0, chat_id: int = 0
    ) -> None:
        """Track a tool call for deduplication.
        
        This silently tracks the tool call without logging warnings.
        """
        call_hash = self._generate_tool_call_hash(function_name, arguments)
        tracking_key = self._get_tracking_key(function_name, user_id, chat_id)
        
        # Add to global tracker silently
        if tracking_key not in _tool_call_tracker:
            _tool_call_tracker[tracking_key] = set()
        _tool_call_tracker[tracking_key].add(call_hash)
        
        # Also add to recent calls for this iteration
        self._recent_tool_calls.add(call_hash)

    def should_prevent_retry(
        self, function_name: str, arguments: str, user_id: int, chat_id: int = 0
    ) -> bool:
        """Check if a tool call should be prevented due to excessive retries."""
        # Check if this is a duplicate without logging warnings
        call_hash = self._generate_tool_call_hash(function_name, arguments)
        tracking_key = self._get_tracking_key(function_name, user_id, chat_id)
        
        if tracking_key not in _tool_call_tracker:
            return False
            
        return call_hash in _tool_call_tracker[tracking_key]

    def reset_tracking(self) -> None:
        """Reset tracking data for this tracker."""
        self._iteration_count = 0
        self._recent_tool_calls.clear()
        logger.debug("Tracker tracking reset")

    def reset_stateless_tracking(self) -> None:
        """Reset stateless tracking data."""
        self._recent_tool_calls.clear()
        logger.debug("Tracker stateless tracking reset")

    def cleanup_old_entries(self, max_age_hours: int = 24) -> None:
        """Clean up old tracking entries."""
        self.cleanup_old_trackers(max_age_hours)

    def get_namespace_key(
        self, function_name: str, arguments: str, user_id: int, chat_id: int = 0
    ) -> str:
        """Get the namespace key for a tool call.

        Args:
            function_name: Name of the function
            arguments: Function arguments
            user_id: User ID
            chat_id: Chat ID

        Returns:
            Namespace key for tracking
        """
        if self._instance_id:
            # Use subagent namespace: subagent_{instance_id}::user_{user_id}_{chat_id}
            user_key = f"{user_id}_{chat_id}" if chat_id else f"user_{user_id}"
            return f"subagent_{self._instance_id}::{user_key}"
        else:
            # Use global namespace: user_{user_id}_{chat_id}
            user_key = f"{user_id}_{chat_id}" if chat_id else f"user_{user_id}"
            return user_key
