"""
╔════════════════════════════════════════════════════════╗
║              Context Management for Logging             ║
║         Correlation IDs and Request Context            ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Propagates request context through async operations
    - Enables distributed tracing
    - Correlates logs across services

Security Considerations:
    - Context is request-scoped
    - No sensitive data in context
    - Cleared after request completes

ISO 27001 Control: A.12.4.1 - Event logging
"""

from contextvars import ContextVar
from typing import Optional

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
department_id_var: ContextVar[Optional[int]] = ContextVar("department_id", default=None)


def set_request_context(
    request_id: str,
    user_id: Optional[str] = None,
    department_id: Optional[int] = None,
) -> None:
    """
    Set request context for logging correlation.

    Args:
        request_id: Unique request identifier
        user_id: Optional user identifier
        department_id: Optional department identifier
    """
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if department_id:
        department_id_var.set(department_id)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()


def get_user_id() -> Optional[str]:
    """Get current user ID from context."""
    return user_id_var.get()


def get_department_id() -> Optional[int]:
    """Get current department ID from context."""
    return department_id_var.get()


def clear_request_context() -> None:
    """Clear all request context variables."""
    request_id_var.set(None)
    user_id_var.set(None)
    department_id_var.set(None)


def get_log_context() -> dict:
    """
    Get all context variables for logging.

    Returns:
        Dictionary with request context for log enrichment
    """
    context = {}

    request_id = get_request_id()
    if request_id:
        context["request_id"] = request_id

    user_id = get_user_id()
    if user_id:
        context["user_id"] = user_id

    department_id = get_department_id()
    if department_id:
        context["department_id"] = department_id

    return context
