"""
Exponential backoff with jitter for rate limiting.

This component provides proper exponential backoff calculation with jitter
to handle rate limiting effectively and avoid thundering herd problems.
"""

import random


class ExponentialBackoffHandler:
    """Handler for exponential backoff with jitter calculations.

    Implements true exponential backoff with ±25% jitter to spread out
    retry attempts and prevent synchronized requests during rate limiting.

    Behaviors:
    - Exponential growth: base_delay * (2 ** retry_count)
    - Maximum delay cap to prevent excessive waits
    - ±25% jitter for load distribution
    - Reset counter on successful requests
    """

    def __init__(self) -> None:
        self.retry_count: int = 0
        self.reset_on_success: bool = True

    def calculate_backoff(self) -> float:
        """Calculate backoff delay with exponential growth and jitter.

        Returns:
            Delay in seconds with jitter applied
        """
        # Configuration constants
        base_delay = 1.0  # Base delay in seconds
        max_delay = 60.0  # Maximum delay cap in seconds

        # Calculate exponential delay
        exponential_delay = base_delay * (2 ** self.retry_count)
        wait_time = min(exponential_delay, max_delay)

        # Add jitter (±25%) to avoid thundering herd
        jitter_factor = random.uniform(0.75, 1.25)
        final_wait_time: float = wait_time * float(jitter_factor)

        return final_wait_time

    def record_success(self) -> None:
        """Record successful request and reset retry counter.

        Resetting the counter ensures proper exponential behavior
        across different rate limit events rather than cumulative
        retry counts.
        """
        if self.reset_on_success:
            self.retry_count = 0

    def record_retry(self) -> None:
        """Record retry attempt and increment counter.

        Call this method when a rate limit error occurs to
        prepare for the next retry attempt.
        """
        self.retry_count += 1

    def get_retry_count(self) -> int:
        """Get current retry count for logging or testing purposes.

        Returns:
            Current number of consecutive retry attempts
        """
        return self.retry_count

    def set_reset_on_success(self, reset: bool) -> None:
        """Configure whether to reset counter on successful requests.

        Args:
            reset: True to reset on success, False to maintain counter
        """
        self.reset_on_success = reset
