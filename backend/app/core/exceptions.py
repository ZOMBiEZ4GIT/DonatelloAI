"""
╔════════════════════════════════════════════════════════╗
║              Custom Exception Classes                   ║
║         Standardized Error Handling                    ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Consistent error responses across all endpoints
    - User-friendly error messages
    - Detailed logging for debugging
    - ISO 27001 compliant error handling

Security Considerations:
    - Never expose internal system details
    - Sanitize error messages for external consumption
    - Log full details internally for investigation
"""

from typing import Any, Dict, Optional


class EIGPlatformException(Exception):
    """
    Base exception for all EIG Platform errors.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details (for logging, not client)
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# ┌─────────────────────────────────────────────────────────┐
# │ 🔐 Authentication & Authorization Errors                │
# └─────────────────────────────────────────────────────────┘


class AuthenticationError(EIGPlatformException):
    """User authentication failed."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="authentication_failed",
            status_code=401,
            details=details,
        )


class AuthorizationError(EIGPlatformException):
    """User not authorized for this operation."""

    def __init__(self, message: str = "Not authorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="authorization_failed",
            status_code=403,
            details=details,
        )


class MFARequiredError(EIGPlatformException):
    """Multi-factor authentication required."""

    def __init__(self, message: str = "MFA required", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="mfa_required",
            status_code=403,
            details=details,
        )


# ┌─────────────────────────────────────────────────────────┐
# │ 💰 Budget & Cost Management Errors                      │
# └─────────────────────────────────────────────────────────┘


class BudgetExceededError(EIGPlatformException):
    """Department budget exceeded."""

    def __init__(
        self,
        message: str = "Department budget exceeded",
        current_spend: float = 0.0,
        budget_limit: float = 0.0,
    ):
        super().__init__(
            message=message,
            error_code="budget_exceeded",
            status_code=402,  # Payment Required
            details={
                "current_spend_aud": current_spend,
                "budget_limit_aud": budget_limit,
                "overage_aud": current_spend - budget_limit,
            },
        )


class CostLimitExceededError(EIGPlatformException):
    """Single image cost exceeds safety limit."""

    def __init__(self, message: str = "Cost limit exceeded", cost: float = 0.0, limit: float = 0.0):
        super().__init__(
            message=message,
            error_code="cost_limit_exceeded",
            status_code=400,
            details={"cost_aud": cost, "limit_aud": limit},
        )


# ┌─────────────────────────────────────────────────────────┐
# │ 🚨 Security & Compliance Errors                         │
# └─────────────────────────────────────────────────────────┘


class PIIDetectedError(EIGPlatformException):
    """PII detected in prompt (GDPR violation)."""

    def __init__(self, message: str = "PII detected in prompt", pii_types: Optional[list] = None):
        super().__init__(
            message=message,
            error_code="pii_detected",
            status_code=400,
            details={"pii_types": pii_types or []},
        )


class ContentViolationError(EIGPlatformException):
    """Content violates safety policies."""

    def __init__(self, message: str = "Content violates safety policies", reason: str = ""):
        super().__init__(
            message=message,
            error_code="content_violation",
            status_code=400,
            details={"reason": reason},
        )


class RateLimitExceededError(EIGPlatformException):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 3600,
        limit: int = 0,
    ):
        super().__init__(
            message=message,
            error_code="rate_limit_exceeded",
            status_code=429,
            details={"retry_after_seconds": retry_after, "limit": limit},
        )


# ┌─────────────────────────────────────────────────────────┐
# │ 🤖 Model Provider Errors                                │
# └─────────────────────────────────────────────────────────┘


class ModelUnavailableError(EIGPlatformException):
    """AI model temporarily unavailable."""

    def __init__(self, message: str = "Model unavailable", model_name: str = "", retry_after: int = 60):
        super().__init__(
            message=message,
            error_code="model_unavailable",
            status_code=503,
            details={"model_name": model_name, "retry_after_seconds": retry_after},
        )


class GenerationFailedError(EIGPlatformException):
    """Image generation failed."""

    def __init__(self, message: str = "Generation failed", reason: str = ""):
        super().__init__(
            message=message,
            error_code="generation_failed",
            status_code=500,
            details={"reason": reason},
        )


class GenerationTimeoutError(EIGPlatformException):
    """Image generation timed out."""

    def __init__(self, message: str = "Generation timed out", timeout_seconds: int = 60):
        super().__init__(
            message=message,
            error_code="generation_timeout",
            status_code=504,
            details={"timeout_seconds": timeout_seconds},
        )


# ┌─────────────────────────────────────────────────────────┐
# │ 📝 Validation & Input Errors                            │
# └─────────────────────────────────────────────────────────┘


class ValidationError(EIGPlatformException):
    """Input validation failed."""

    def __init__(self, message: str = "Validation failed", field: str = "", reason: str = ""):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=400,
            details={"field": field, "reason": reason},
        )


class ResourceNotFoundError(EIGPlatformException):
    """Requested resource not found."""

    def __init__(self, message: str = "Resource not found", resource_type: str = "", resource_id: str = ""):
        super().__init__(
            message=message,
            error_code="resource_not_found",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


# ┌─────────────────────────────────────────────────────────┐
# │ 💾 Data & Storage Errors                                │
# └─────────────────────────────────────────────────────────┘


class StorageError(EIGPlatformException):
    """Storage operation failed."""

    def __init__(self, message: str = "Storage error", operation: str = ""):
        super().__init__(
            message=message,
            error_code="storage_error",
            status_code=500,
            details={"operation": operation},
        )


class DatabaseError(EIGPlatformException):
    """Database operation failed."""

    def __init__(self, message: str = "Database error", operation: str = ""):
        super().__init__(
            message=message,
            error_code="database_error",
            status_code=500,
            details={"operation": operation},
        )


# ⚠️  ERROR HANDLING GUIDELINES:
#
# ✅ DO:
# - Use specific exception types
# - Provide helpful error messages
# - Include relevant details for debugging
# - Log full error details internally
# - Return sanitized errors to clients
#
# ❌ DON'T:
# - Expose internal system details
# - Include stack traces in API responses
# - Log sensitive data in error messages
# - Use generic Exception class
#
# 📊 Error Response Format:
# {
#   "error": "error_code",
#   "message": "Human-readable message",
#   "request_id": "uuid",
#   "details": {}  # Optional additional context
# }
#
# 📋 ISO 27001 Control Mapping:
# - A.12.4.1: Event logging (all errors logged)
# - A.16.1.2: Reporting information security events
# - A.16.1.4: Assessment of and decision on information security events
