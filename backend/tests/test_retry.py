"""
Tests for retry utilities.
"""

import pytest
from app.utils.retry import retry_on_transient_error


class TestRetryLogic:
    """Tests for retry logic utilities."""

    def test_retry_on_success(self):
        """Test that successful calls don't retry."""
        call_count = 0

        @retry_on_transient_error(max_attempts=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()

        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self):
        """Test that failed calls retry."""
        call_count = 0

        @retry_on_transient_error(max_attempts=3, exceptions=(ValueError,))
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = failing_function()

        assert result == "success"
        assert call_count == 3

    def test_retry_exhaustion(self):
        """Test that retries are exhausted and exception is raised."""
        call_count = 0

        @retry_on_transient_error(max_attempts=3, exceptions=(ValueError,))
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            always_failing()

        assert call_count == 3
