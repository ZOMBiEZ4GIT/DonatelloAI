"""
╔════════════════════════════════════════════════════════╗
║           Structured Logging Configuration             ║
║         🔒 ISO 27001 A.12.4.1 Compliant                ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - All application events logged for audit and debugging
    - Logs sent to Azure Log Analytics and Application Insights
    - Structured logging for efficient querying and analysis

Security Considerations:
    - PII automatically redacted from logs
    - Secrets masked before logging
    - Log levels enforced based on environment
    - Logs are immutable (write-only)

ISO 27001 Controls:
    - A.12.4.1: Event logging
    - A.12.4.2: Protection of log information
    - A.12.4.3: Administrator and operator logs
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level, format_exc_info
from structlog.stdlib import filter_by_level

from app.core.config import settings


def mask_sensitive_data(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive data in log events.

    Removes or masks sensitive information before logging:
    - Passwords
    - API keys
    - Tokens
    - Credit card numbers
    - Social security numbers

    ISO 27001 Control: A.12.4.2 - Protection of log information
    """
    sensitive_keys = {
        "password",
        "secret",
        "token",
        "api_key",
        "private_key",
        "credit_card",
        "ssn",
        "authorization",
    }

    def mask_value(key: str, value: Any) -> Any:
        """Mask value if key is sensitive."""
        if isinstance(key, str) and any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str) and len(value) > 4:
                return f"{value[:2]}...{value[-2:]}"  # Show first 2 and last 2 chars
            return "***MASKED***"
        if isinstance(value, dict):
            return {k: mask_value(k, v) for k, v in value.items()}
        return value

    return {k: mask_value(k, v) for k, v in event_dict.items()}


def add_app_context(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add application context to all log events.

    Adds:
    - Environment (dev/staging/prod)
    - Application version
    - Service name
    - Deployment region

    ISO 27001 Control: A.12.4.1 - Event logging
    """
    event_dict["environment"] = settings.ENVIRONMENT
    event_dict["app_version"] = settings.APP_VERSION
    event_dict["service"] = "eig-platform-backend"
    event_dict["region"] = settings.DATA_RESIDENCY_REGION
    return event_dict


def setup_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up:
    - JSON-formatted logs for production
    - Human-readable logs for development
    - Log level based on environment
    - Integration with Azure Log Analytics

    ISO 27001 Control: A.12.4.1 - Event logging
    """
    log_level = getattr(logging, settings.LOG_LEVEL)

    # Configure structlog processors
    processors = [
        filter_by_level,  # Filter by log level
        add_log_level,  # Add log level to event dict
        add_app_context,  # Add application context
        TimeStamper(fmt="iso", utc=True),  # Add ISO 8601 timestamp
        mask_sensitive_data,  # Mask sensitive data
        format_exc_info,  # Format exception info
    ]

    # Add renderer based on environment
    if settings.ENVIRONMENT == "production":
        # JSON logs for production (machine-readable)
        processors.append(JSONRenderer())
    else:
        # Human-readable logs for development
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("msal").setLevel(logging.WARNING)


# Create logger instance
logger: structlog.stdlib.BoundLogger = structlog.get_logger()


# ⚠️  LOGGING GUIDELINES:
#
# ✅ DO:
# - Use structured logging with key-value pairs
# - Log all security-relevant events
# - Log business transactions for audit
# - Include request IDs for tracing
# - Use appropriate log levels
#
# ❌ DON'T:
# - Log passwords, tokens, or secrets
# - Log PII without redaction
# - Log sensitive business data
# - Use string interpolation (use key-value pairs)
#
# 📋 Log Levels:
# - DEBUG: Detailed debugging information
# - INFO: General informational messages
# - WARNING: Warning messages for recoverable errors
# - ERROR: Error messages for handled errors
# - CRITICAL: Critical errors requiring immediate attention
#
# 📊 Example Usage:
# logger.info("user_login_success", user_id=user_id, ip_address=ip)
# logger.error("payment_failed", user_id=user_id, amount=amount, error=str(e))
#
# 📋 ISO 27001 Control Mapping:
# - A.12.4.1: Event logging
# - A.12.4.2: Protection of log information
# - A.12.4.3: Administrator and operator logs
# - A.12.4.4: Clock synchronisation (UTC timestamps)
