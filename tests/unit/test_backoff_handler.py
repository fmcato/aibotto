"""
Tests for exponential backoff handler.

These tests verify the exponential progression, jitter range,
and counter reset behavior of the ExponentialBackoffHandler.
"""

import pytest
from unittest.mock import patch
import time

from aibotto.ai.backoff_handler import ExponentialBackoffHandler


class TestExponentialBackoffHandler:
    """Test suite for ExponentialBackoffHandler."""

    def test_initial_state(self) -> None:
        """Test that handler starts in correct initial state."""
        handler = ExponentialBackoffHandler()
        
        assert handler.retry_count == 0
        assert handler.reset_on_success is True
        assert handler.get_retry_count() == 0

    def test_calculate_backoff_initial(self) -> None:
        """Test initial backoff calculation (first retry, no retries recorded yet)."""
        handler = ExponentialBackoffHandler()

        delay = handler.calculate_backoff()

        # Should be 1.0s with jitter (retry_count is 0, so index is 0)
        assert 0.8 <= delay <= 1.2  # ±20% tolerance

    def test_exponential_progression(self) -> None:
        """Test that delays follow fixed interval progression (1s, 10s, 30s)."""
        handler = ExponentialBackoffHandler()

        # Simulate LLM client: record_retry then calculate_backoff
        # retry_count=1 -> index 0 -> 1.0s (first retry)
        # retry_count=2 -> index 1 -> 10.0s (second retry)
        # retry_count=3 -> index 2 -> 30.0s (third retry)
        # retry_count=4+ -> 60.0s (capped)

        handler.record_retry()
        delay1 = handler.calculate_backoff()

        handler.record_retry()
        delay2 = handler.calculate_backoff()

        handler.record_retry()
        delay3 = handler.calculate_backoff()

        handler.record_retry()
        delay4 = handler.calculate_backoff()

        # Verify progression: 1s → 10s → 30s → 60s
        assert 0.8 <= delay1 <= 1.2
        assert 8.0 <= delay2 <= 12.0
        assert 24.0 <= delay3 <= 36.0
        assert 48.0 <= delay4 <= 72.0

    def test_max_delay_cap(self) -> None:
        """Test that maximum delay is properly capped."""
        handler = ExponentialBackoffHandler()

        # Force many retries to trigger cap
        for _ in range(10):  # More than enough to exceed 60s
            handler.record_retry()

        delay = handler.calculate_backoff()

        # Should be capped at 60s with jitter
        assert delay <= 60.0 * 1.2  # Upper bound with jitter
        assert delay >= 60.0 * 0.8  # Lower bound with jitter

    def test_jitter_distribution(self) -> None:
        """Test that jitter provides proper distribution."""
        handler = ExponentialBackoffHandler()
        handler.record_retry()  # retry_count=1 -> index 0 -> 1.0s

        delays = []
        sample_size = 1000

        # Collect many samples to verify distribution
        for _ in range(sample_size):
            delay = handler.calculate_backoff()
            delays.append(delay)

        # All delays should be within 20% range of base (1.0s)
        min_expected = 1.0 * 0.8
        max_expected = 1.0 * 1.2

        for delay in delays:
            assert min_expected <= delay <= max_expected

        # Verify we actually have variation (not all the same)
        assert max(delays) - min(delays) > 0.05  # Should have meaningful variation

    def test_counter_reset_on_success(self) -> None:
        """Test that counter resets on successful requests."""
        handler = ExponentialBackoffHandler()
        
        # Build up some retry count
        handler.record_retry()
        handler.record_retry()
        handler.record_retry()
        
        assert handler.get_retry_count() == 3
        
        # Record success
        handler.record_success()
        
        assert handler.get_retry_count() == 0
        assert handler.reset_on_success is True

    def test_counter_no_reset_when_disabled(self) -> None:
        """Test that counter doesn't reset when disabled."""
        handler = ExponentialBackoffHandler()
        handler.set_reset_on_success(False)
        
        # Build up some retry count
        handler.record_retry()
        handler.record_retry()
        
        assert handler.get_retry_count() == 2
        
        # Record success (should not reset)
        handler.record_success()
        
        assert handler.get_retry_count() == 2  # Should remain unchanged

    def test_retry_increment(self) -> None:
        """Test that retry counter increments correctly."""
        handler = ExponentialBackoffHandler()
        
        assert handler.get_retry_count() == 0
        
        handler.record_retry()
        assert handler.get_retry_count() == 1
        
        handler.record_retry()
        assert handler.get_retry_count() == 2
        
        handler.record_retry()
        assert handler.get_retry_count() == 3

    def test_calculate_without_recording_retry(self) -> None:
        """Test that calculate_backoff works without recording retry."""
        handler = ExponentialBackoffHandler()
        
        # Should still work even without recording retries
        delay1 = handler.calculate_backoff()  # Initial state
        delay2 = handler.calculate_backoff()  # Still initial state
        
        # Both should be in the same ballpark (with jitter variation)
        # Initial delay should be around 1.0s with ±25% jitter
        assert 0.75 <= delay1 <= 1.25
        assert 0.75 <= delay2 <= 1.25

    def test_pseudo_random_jitter(self) -> None:
        """Test that jitter provides pseudo-random distribution."""
        handler = ExponentialBackoffHandler()
        handler.record_retry()  # retry_count=1 -> index 0 -> 1.0s base

        # Use fixed seed for reproducible test
        with patch('random.seed', return_value=None):
            with patch('random.uniform') as mock_uniform:
                # Mock uniform to return predictable values
                mock_uniform.side_effect = [0.8, 1.2, 0.9, 1.1, 1.0]

                delays = []
                for _ in range(5):
                    delays.append(handler.calculate_backoff())

                # Verify jitter is applied (base is 1.0s with retry_count=1)
                expected_delays = [1.0 * 0.8, 1.0 * 1.2, 1.0 * 0.9, 1.0 * 1.1, 1.0 * 1.0]
                assert delays == expected_delays

                # Verify random.uniform was called correctly
                assert mock_uniform.call_count == 5
                mock_uniform.assert_any_call(0.8, 1.2)

    def test_integration_workflow(self) -> None:
        """Test typical workflow of handler usage.

        Note: In LLM client, we call record_retry() BEFORE calculate_backoff().
        """
        handler = ExponentialBackoffHandler()

        # Simulate successful request
        handler.record_success()
        assert handler.get_retry_count() == 0

        # Simulate rate limiting - first retry (LLM client pattern)
        handler.record_retry()  # Now retry_count=1
        delay1 = handler.calculate_backoff()  # Uses wait_times[0] = 1.0s
        assert handler.get_retry_count() == 1

        # Simulate rate limiting - second retry (LLM client pattern)
        handler.record_retry()  # Now retry_count=2
        delay2 = handler.calculate_backoff()  # Uses wait_times[1] = 10.0s
        assert handler.get_retry_count() == 2

        # Verify progression (10s > 1s)
        assert delay2 > delay1 * 5  # Should increase significantly

        # Simulate successful request after retries
        handler.record_success()
        assert handler.get_retry_count() == 0

        # Back to initial state (still uses wait_times[0] when retry_count=0)
        delay3 = handler.calculate_backoff()
        assert 0.8 <= delay3 <= 1.2  # Should be initial range

    def test_edge_cases(self) -> None:
        """Test edge cases and boundary conditions."""
        handler = ExponentialBackoffHandler()
        
        # Test with zero retries
        delay = handler.calculate_backoff()
        assert delay > 0
        
        # Test very high retry count
        handler.retry_count = 100  # Direct modification for testing
        delay = handler.calculate_backoff()
        assert delay <= 60.0 * 1.25  # Should still be capped
        
        # Test negative retry count (should not happen but test robustness)
        handler.retry_count = -1
        delay = handler.calculate_backoff()
        assert delay > 0  # Should still produce positive delay

    def test_configuration_methods(self) -> None:
        """Test configuration methods work correctly."""
        handler = ExponentialBackoffHandler()
        
        # Test changing reset behavior
        assert handler.reset_on_success is True
        handler.set_reset_on_success(False)
        assert handler.reset_on_success is False
        
        # Test changing back
        handler.set_reset_on_success(True)
        assert handler.reset_on_success is True