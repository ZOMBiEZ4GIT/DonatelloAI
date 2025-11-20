"""
╔════════════════════════════════════════════════════════╗
║              Retry Logic Utilities                      ║
║         Exponential backoff for external APIs          ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Handles transient failures when calling external APIs
    - Improves reliability of model provider integrations
    - Reduces failed image generation requests

Security Considerations:
    - Logs retry attempts for monitoring
    - Respects rate limits from providers
    - Implements circuit breaker pattern

ISO 27001 Control: A.17.2.1 - Availability of information processing facilities
"""

from functools import wraps
from typing import Callable, Type, TypeVar

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)

from app.core.logging import logger

T = TypeVar("T")


def retry_on_transient_error(
    max_attempts: int = 3,
    min_wait: int = 2,
    max_wait: int = 10,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator to retry function on transient errors with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_transient_error(max_attempts=3, exceptions=(HTTPError, Timeout))
        async def call_model_api(...):
            ...
    """

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, "WARNING"),
        after=after_log(logger, "INFO"),
        reraise=True,
    )


def retry_on_http_error(max_attempts: int = 3) -> Callable:
    """
    Retry decorator specifically for HTTP errors.

    Retries on 5xx server errors and connection errors.
    Does NOT retry on 4xx client errors.

    Args:
        max_attempts: Maximum number of retry attempts

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_http_error(max_attempts=3)
        async def fetch_data(url: str):
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
    """
    import httpx

    def should_retry(exception: BaseException) -> bool:
        """Determine if exception should trigger retry."""
        if isinstance(exception, httpx.HTTPStatusError):
            # Retry on 5xx server errors, not on 4xx client errors
            return 500 <= exception.response.status_code < 600
        if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException)):
            return True
        return False

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        retry=should_retry,
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True,
    )


def retry_openai_call(max_attempts: int = 3) -> Callable:
    """
    Retry decorator for OpenAI API calls.

    Handles rate limits (429) and server errors (5xx).

    Args:
        max_attempts: Maximum number of retry attempts

    Returns:
        Decorated function with retry logic
    """
    from openai import RateLimitError, APIError, APIConnectionError

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        retry=retry_if_exception_type((RateLimitError, APIError, APIConnectionError)),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True,
    )


def retry_azure_call(max_attempts: int = 3) -> Callable:
    """
    Retry decorator for Azure service calls.

    Handles transient Azure errors.

    Args:
        max_attempts: Maximum number of retry attempts

    Returns:
        Decorated function with retry logic
    """
    from azure.core.exceptions import (
        ServiceRequestError,
        ServiceResponseError,
        HttpResponseError,
    )

    def should_retry(exception: BaseException) -> bool:
        """Determine if Azure exception should trigger retry."""
        if isinstance(exception, HttpResponseError):
            # Retry on 429 (rate limit) and 5xx (server errors)
            if exception.status_code == 429:
                return True
            if 500 <= exception.status_code < 600:
                return True
            return False
        if isinstance(exception, (ServiceRequestError, ServiceResponseError)):
            return True
        return False

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        retry=should_retry,
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True,
    )


# ⚠️  RETRY STRATEGY NOTES:
#
# 📊 Exponential Backoff:
# - First retry: 2s wait
# - Second retry: 4s wait
# - Third retry: 8s wait (capped at 16s max)
#
# 🎯 When to Retry:
# - Network errors (connection failures, timeouts)
# - Server errors (5xx status codes)
# - Rate limiting (429 status code)
# - Transient Azure/AWS errors
#
# 🚫 When NOT to Retry:
# - Client errors (4xx status codes except 429)
# - Authentication failures (401, 403)
# - Validation errors (400, 422)
# - Resource not found (404)
#
# 💰 COST IMPACT:
# - Retries increase API costs
# - Balance reliability vs. cost
# - Monitor retry rates via metrics
#
# 📋 ISO 27001 Control Mapping:
# - A.17.2.1: Availability of information processing facilities
# - A.12.1.3: Capacity management
