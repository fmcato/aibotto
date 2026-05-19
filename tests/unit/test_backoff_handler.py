"""
Tests for exponential backoff handler.

These tests verify the exponential progression, jitter range,
and counter reset behavior of the ExponentialBackoffHandler.
"""

from unittest.mock import patch

from aibotto.ai.backoff_handler import ExponentialBackoffHandler


class TestExponentialBackoffHandler:
    """Test suite for ExponentialBackoffHandler."""

    def test_initial_state(self) -> None:
        """Test that handler starts in correct initial state."""
        handler = ExponentialBackoffHandler()

        assert handler.retry_count == 0
        assert handler.reset_on_success is True

    def test_calculate_backoff_initial(self) -> None:
        """Test initial backoff calculation (first retry, no retries recorded yet)."""
        handler = ExponentialBackoffHandler()

        delay = handler.calculate_backoff()

        assert 0.8 <= delay <= 1.2

    def test_exponential_progression(self) -> None:
        """Test that delays follow fixed interval progression (1s, 10s, 30s)."""
        handler = ExponentialBackoffHandler()

        handler.record_retry()
        delay1 = handler.calculate_backoff()

        handler.record_retry()
        delay2 = handler.calculate_backoff()

        handler.record_retry()
        delay3 = handler.calculate_backoff()

        handler.record_retry()
        delay4 = handler.calculate_backoff()

        assert 0.8 <= delay1 <= 1.2
        assert 8.0 <= delay2 <= 12.0
        assert 24.0 <= delay3 <= 36.0
        assert 48.0 <= delay4 <= 72.0

    def test_max_delay_cap(self) -> None:
        """Test that maximum delay is properly capped."""
        handler = ExponentialBackoffHandler()

        for _ in range(10):
            handler.record_retry()

        delay = handler.calculate_backoff()

        assert delay <= 60.0 * 1.2
        assert delay >= 60.0 * 0.8

    def test_jitter_distribution(self) -> None:
        """Test that jitter provides proper distribution."""
        handler = ExponentialBackoffHandler()
        handler.record_retry()

        delays = []
        sample_size = 1000

        for _ in range(sample_size):
            delay = handler.calculate_backoff()
            delays.append(delay)

        min_expected = 1.0 * 0.8
        max_expected = 1.0 * 1.2

        for delay in delays:
            assert min_expected <= delay <= max_expected

        assert max(delays) - min(delays) > 0.05

    def test_counter_reset_on_success(self) -> None:
        """Test that counter resets on successful requests."""
        handler = ExponentialBackoffHandler()

        handler.record_retry()
        handler.record_retry()
        handler.record_retry()

        assert handler.retry_count == 3

        handler.record_success()

        assert handler.retry_count == 0
        assert handler.reset_on_success is True

    def test_counter_no_reset_when_disabled(self) -> None:
        """Test that counter doesn't reset when disabled."""
        handler = ExponentialBackoffHandler()
        handler.reset_on_success = False

        handler.record_retry()
        handler.record_retry()

        assert handler.retry_count == 2

        handler.record_success()

        assert handler.retry_count == 2

    def test_retry_increment(self) -> None:
        """Test that retry counter increments correctly."""
        handler = ExponentialBackoffHandler()

        assert handler.retry_count == 0

        handler.record_retry()
        assert handler.retry_count == 1

        handler.record_retry()
        assert handler.retry_count == 2

        handler.record_retry()
        assert handler.retry_count == 3

    def test_calculate_without_recording_retry(self) -> None:
        """Test that calculate_backoff works without recording retry."""
        handler = ExponentialBackoffHandler()

        delay1 = handler.calculate_backoff()
        delay2 = handler.calculate_backoff()

        assert 0.75 <= delay1 <= 1.25
        assert 0.75 <= delay2 <= 1.25

    def test_pseudo_random_jitter(self) -> None:
        """Test that jitter provides pseudo-random distribution."""
        handler = ExponentialBackoffHandler()
        handler.record_retry()

        with patch('random.seed', return_value=None):
            with patch('random.uniform') as mock_uniform:
                mock_uniform.side_effect = [0.8, 1.2, 0.9, 1.1, 1.0]

                delays = []
                for _ in range(5):
                    delays.append(handler.calculate_backoff())

                expected_delays = [1.0 * 0.8, 1.0 * 1.2, 1.0 * 0.9, 1.0 * 1.1, 1.0 * 1.0]
                assert delays == expected_delays

                assert mock_uniform.call_count == 5
                mock_uniform.assert_any_call(0.8, 1.2)

    def test_integration_workflow(self) -> None:
        """Test typical workflow of handler usage."""
        handler = ExponentialBackoffHandler()

        handler.record_success()
        assert handler.retry_count == 0

        handler.record_retry()
        delay1 = handler.calculate_backoff()
        assert handler.retry_count == 1

        handler.record_retry()
        delay2 = handler.calculate_backoff()
        assert handler.retry_count == 2

        assert delay2 > delay1 * 5

        handler.record_success()
        assert handler.retry_count == 0

        delay3 = handler.calculate_backoff()
        assert 0.8 <= delay3 <= 1.2

    def test_edge_cases(self) -> None:
        """Test edge cases and boundary conditions."""
        handler = ExponentialBackoffHandler()

        delay = handler.calculate_backoff()
        assert delay > 0

        handler.retry_count = 100
        delay = handler.calculate_backoff()
        assert delay <= 60.0 * 1.25

        handler.retry_count = -1
        delay = handler.calculate_backoff()
        assert delay > 0
