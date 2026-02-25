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
        """Test initial backoff calculation (no retries yet)."""
        handler = ExponentialBackoffHandler()
        
        delay = handler.calculate_backoff()
        
        # Should be around 1.0s with jitter
        assert 0.5 <= delay <= 1.5  # ±50% tolerance for initial jitter

    def test_exponential_progression(self) -> None:
        """Test that delays follow exponential progression."""
        handler = ExponentialBackoffHandler()
        
        # Test progression: 1s → 2s → 4s → 8s → 16s → 32s → 60s (capped)
        expected_base_delays = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 60.0]
        actual_delays = []
        
        # Record retries to trigger progression
        for _ in expected_base_delays:
            actual_delays.append(handler.calculate_backoff())
            handler.record_retry()
        
        # Verify each delay is within reasonable range of expected
        for actual, expected in zip(actual_delays, expected_base_delays):
            # Allow ±25% tolerance for jitter
            assert expected * 0.75 <= actual <= expected * 1.25

    def test_max_delay_cap(self) -> None:
        """Test that maximum delay is properly capped."""
        handler = ExponentialBackoffHandler()
        
        # Force many retries to trigger cap
        for _ in range(10):  # More than enough to exceed 60s
            handler.record_retry()
        
        delay = handler.calculate_backoff()
        
        # Should be capped at 60s with jitter
        assert delay <= 60.0 * 1.25  # Upper bound with jitter
        assert delay >= 60.0 * 0.75  # Lower bound with jitter

    def test_jitter_distribution(self) -> None:
        """Test that jitter provides proper distribution."""
        handler = ExponentialBackoffHandler()
        handler.record_retry()  # Set to first retry (base 2.0s)
        
        delays = []
        sample_size = 1000
        
        # Collect many samples to verify distribution
        for _ in range(sample_size):
            delay = handler.calculate_backoff()
            delays.append(delay)
        
        # All delays should be within 25% range of base (2.0s)
        min_expected = 2.0 * 0.75
        max_expected = 2.0 * 1.25
        
        for delay in delays:
            assert min_expected <= delay <= max_expected
        
        # Verify we actually have variation (not all the same)
        assert max(delays) - min(delays) > 0.1  # Should have meaningful variation

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
        handler.record_retry()  # Set to 2.0s base
        
        # Use fixed seed for reproducible test
        with patch('random.seed', return_value=None):
            with patch('random.uniform') as mock_uniform:
                # Mock uniform to return predictable values
                mock_uniform.side_effect = [0.8, 1.2, 0.9, 1.1, 1.0]
                
                delays = []
                for _ in range(5):
                    delays.append(handler.calculate_backoff())
                
                # Verify jitter is applied
                expected_delays = [2.0 * 0.8, 2.0 * 1.2, 2.0 * 0.9, 2.0 * 1.1, 2.0 * 1.0]
                assert delays == expected_delays
                
                # Verify random.uniform was called correctly
                assert mock_uniform.call_count == 5
                mock_uniform.assert_any_call(0.75, 1.25)

    def test_integration_workflow(self) -> None:
        """Test typical workflow of handler usage."""
        handler = ExponentialBackoffHandler()
        
        # Simulate successful request
        handler.record_success()
        assert handler.get_retry_count() == 0
        
        # Simulate rate limiting - first retry
        delay1 = handler.calculate_backoff()
        handler.record_retry()
        assert handler.get_retry_count() == 1
        
        # Simulate rate limiting - second retry
        delay2 = handler.calculate_backoff()
        handler.record_retry()
        assert handler.get_retry_count() == 2
        
        # Verify exponential progression
        assert delay2 > delay1  # Should increase
        
        # Simulate successful request after retries
        handler.record_success()
        assert handler.get_retry_count() == 0
        
        # Back to initial state
        delay3 = handler.calculate_backoff()
        # Both should be in the same ballpark (with jitter variation)
        assert 0.75 <= delay3 <= 1.25  # Should be in initial range

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