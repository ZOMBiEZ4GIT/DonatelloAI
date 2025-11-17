"""
╔════════════════════════════════════════════════════════╗
║           Prompt Security Validator                     ║
║         🔐 Comprehensive Input Validation              ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Comprehensive validation of user prompts
    - Combines PII detection and content filtering
    - Prevents security incidents and compliance violations
    - Provides detailed feedback for security audit

Security Considerations:
    - Multi-layer validation approach
    - Fail-safe defaults (reject on error)
    - Detailed logging for security analysis
    - Configurable enforcement modes

ISO 27001 Controls:
    - A.12.2.1: Controls against malware
    - A.12.6.1: Management of technical vulnerabilities
    - A.18.1.4: Privacy and protection of PII
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import PIIDetectedError, ContentViolationError
from app.core.logging import get_logger
from app.services.security.pii_detector import (
    get_pii_detector,
    PIIDetectionResult,
    PIIType,
)
from app.services.security.content_filter import (
    get_content_filter,
    ContentFilterResult,
    ViolationSeverity,
)

logger = get_logger(__name__)


class ValidationAction(str, Enum):
    """Actions to take after validation."""

    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    type: str
    severity: str
    message: str
    details: Optional[dict] = None


@dataclass
class PromptValidationResult:
    """Complete validation result for a prompt."""

    is_valid: bool
    action: ValidationAction
    issues: List[ValidationIssue]
    pii_result: Optional[PIIDetectionResult] = None
    content_result: Optional[ContentFilterResult] = None
    anonymized_prompt: Optional[str] = None
    safe_for_logging: bool = True
    audit_metadata: dict = None

    def __post_init__(self):
        """Initialize audit metadata."""
        if self.audit_metadata is None:
            self.audit_metadata = {}


class PromptSecurityValidator:
    """
    Comprehensive prompt security validator.

    Combines PII detection, content filtering, and other security
    checks into a unified validation pipeline.
    """

    def __init__(self):
        """Initialize the validator with all security services."""
        self.pii_detector = get_pii_detector()
        self.content_filter = get_content_filter()
        self.pii_action = settings.PII_ACTION

    def validate(
        self,
        prompt: str,
        max_length: int = 2000,
        min_length: int = 3,
        strict_mode: bool = False,
    ) -> PromptValidationResult:
        """
        Validate a user prompt for security and compliance.

        Args:
            prompt: The prompt text to validate
            max_length: Maximum allowed prompt length
            min_length: Minimum required prompt length
            strict_mode: If True, applies stricter validation rules

        Returns:
            PromptValidationResult with detailed findings

        Raises:
            PIIDetectedError: If PII is detected and action is "block"
            ContentViolationError: If harmful content detected
        """
        issues: List[ValidationIssue] = []
        action = ValidationAction.ALLOW

        # Basic validation
        basic_issues = self._validate_basic(prompt, min_length, max_length)
        if basic_issues:
            issues.extend(basic_issues)
            action = ValidationAction.BLOCK

        # PII detection
        pii_result = None
        if settings.ENABLE_PII_DETECTION:
            try:
                pii_result = self.pii_detector.detect(prompt)
                if pii_result.contains_pii:
                    pii_issues = self._process_pii_result(pii_result)
                    issues.extend(pii_issues)

                    # Determine action based on config
                    if self.pii_action == "block":
                        action = ValidationAction.BLOCK
                    elif self.pii_action == "warn":
                        action = max(action, ValidationAction.WARN, key=lambda x: x.value)
                    # "anonymize" allows but logs

            except Exception as e:
                logger.error(f"PII detection failed: {e}", exc_info=True)
                if strict_mode:
                    issues.append(
                        ValidationIssue(
                            type="pii_detection_error",
                            severity="high",
                            message="PII detection service failed",
                        )
                    )
                    action = ValidationAction.BLOCK

        # Content filtering
        content_result = None
        try:
            content_result = self.content_filter.filter(prompt, max_length)
            if not content_result.is_safe:
                content_issues = self._process_content_result(content_result)
                issues.extend(content_issues)

                if content_result.action == "block":
                    action = ValidationAction.BLOCK
                elif content_result.action == "warn":
                    action = max(action, ValidationAction.WARN, key=lambda x: x.value)

        except Exception as e:
            logger.error(f"Content filtering failed: {e}", exc_info=True)
            if strict_mode:
                issues.append(
                    ValidationIssue(
                        type="content_filter_error",
                        severity="high",
                        message="Content filtering service failed",
                    )
                )
                action = ValidationAction.BLOCK

        # Determine final validation status
        is_valid = action == ValidationAction.ALLOW

        # Create anonymized version if PII detected
        anonymized_prompt = None
        if pii_result and pii_result.contains_pii:
            anonymized_prompt = pii_result.anonymized_text

        # Determine if safe for logging
        safe_for_logging = (
            pii_result is None or not pii_result.contains_pii
        ) and (content_result is None or content_result.is_safe)

        # Build audit metadata
        audit_metadata = {
            "prompt_length": len(prompt),
            "pii_detected": pii_result.contains_pii if pii_result else False,
            "pii_types": [d.type.value for d in pii_result.detections] if pii_result else [],
            "content_violations": len(content_result.violations) if content_result else 0,
            "risk_score": content_result.risk_score if content_result else 0.0,
            "validation_action": action.value,
            "issue_count": len(issues),
        }

        result = PromptValidationResult(
            is_valid=is_valid,
            action=action,
            issues=issues,
            pii_result=pii_result,
            content_result=content_result,
            anonymized_prompt=anonymized_prompt,
            safe_for_logging=safe_for_logging,
            audit_metadata=audit_metadata,
        )

        # Log validation result
        self._log_validation(result, prompt)

        # Raise exceptions if needed
        if action == ValidationAction.BLOCK:
            if pii_result and pii_result.contains_pii and self.pii_action == "block":
                raise PIIDetectedError(
                    message="Prompt contains personally identifiable information",
                    details={
                        "pii_types": [d.type.value for d in pii_result.detections],
                        "anonymized_prompt": anonymized_prompt,
                    },
                )
            if content_result and not content_result.is_safe:
                raise ContentViolationError(
                    message=content_result.reason or "Prompt contains prohibited content",
                    details={
                        "violations": [v.type.value for v in content_result.violations],
                        "risk_score": content_result.risk_score,
                    },
                )

        return result

    def _validate_basic(
        self, prompt: str, min_length: int, max_length: int
    ) -> List[ValidationIssue]:
        """
        Perform basic validation checks.

        Args:
            prompt: Prompt to validate
            min_length: Minimum length
            max_length: Maximum length

        Returns:
            List of validation issues
        """
        issues = []

        # Empty check
        if not prompt or not prompt.strip():
            issues.append(
                ValidationIssue(
                    type="empty_prompt",
                    severity="medium",
                    message="Prompt cannot be empty",
                )
            )

        # Length checks
        if len(prompt) < min_length:
            issues.append(
                ValidationIssue(
                    type="prompt_too_short",
                    severity="low",
                    message=f"Prompt must be at least {min_length} characters",
                    details={"current_length": len(prompt)},
                )
            )

        if len(prompt) > max_length:
            issues.append(
                ValidationIssue(
                    type="prompt_too_long",
                    severity="medium",
                    message=f"Prompt exceeds maximum length of {max_length} characters",
                    details={"current_length": len(prompt)},
                )
            )

        # Null byte check
        if "\x00" in prompt:
            issues.append(
                ValidationIssue(
                    type="null_bytes",
                    severity="high",
                    message="Prompt contains null bytes",
                )
            )

        # Control character check
        control_chars = [c for c in prompt if ord(c) < 32 and c not in "\n\r\t"]
        if control_chars:
            issues.append(
                ValidationIssue(
                    type="control_characters",
                    severity="medium",
                    message="Prompt contains invalid control characters",
                    details={"count": len(control_chars)},
                )
            )

        return issues

    def _process_pii_result(self, result: PIIDetectionResult) -> List[ValidationIssue]:
        """
        Process PII detection result into validation issues.

        Args:
            result: PII detection result

        Returns:
            List of validation issues
        """
        issues = []

        # Group by PII type
        pii_by_type = {}
        for detection in result.detections:
            if detection.type not in pii_by_type:
                pii_by_type[detection.type] = []
            pii_by_type[detection.type].append(detection)

        # Create issues for each type
        for pii_type, detections in pii_by_type.items():
            # Determine severity based on PII type
            severity = self._get_pii_severity(pii_type)

            issues.append(
                ValidationIssue(
                    type="pii_detected",
                    severity=severity,
                    message=f"Detected {pii_type.value.replace('_', ' ')}",
                    details={
                        "pii_type": pii_type.value,
                        "count": len(detections),
                        "confidence": max(d.confidence for d in detections),
                    },
                )
            )

        return issues

    def _get_pii_severity(self, pii_type: PIIType) -> str:
        """
        Determine severity level for a PII type.

        Args:
            pii_type: Type of PII

        Returns:
            Severity level (low, medium, high, critical)
        """
        critical_pii = {
            PIIType.SSN,
            PIIType.CREDIT_CARD,
            PIIType.AWS_KEY,
            PIIType.GOOGLE_API_KEY,
            PIIType.GITHUB_TOKEN,
            PIIType.PRIVATE_KEY,
            PIIType.DATABASE_CONNECTION,
            PIIType.PASSWORD,
            PIIType.TAX_FILE_NUMBER,
        }

        high_pii = {
            PIIType.BANK_ACCOUNT,
            PIIType.MEDICARE_NUMBER,
            PIIType.PASSPORT,
            PIIType.MEDICAL_RECORD_NUMBER,
            PIIType.API_KEY,
        }

        if pii_type in critical_pii:
            return "critical"
        elif pii_type in high_pii:
            return "high"
        elif pii_type in {PIIType.EMAIL, PIIType.PHONE}:
            return "medium"
        else:
            return "low"

    def _process_content_result(
        self, result: ContentFilterResult
    ) -> List[ValidationIssue]:
        """
        Process content filter result into validation issues.

        Args:
            result: Content filter result

        Returns:
            List of validation issues
        """
        issues = []

        for violation in result.violations:
            issues.append(
                ValidationIssue(
                    type="content_violation",
                    severity=violation.severity.value,
                    message=violation.description,
                    details={
                        "violation_type": violation.type.value,
                        "confidence": violation.confidence,
                    },
                )
            )

        return issues

    def _log_validation(self, result: PromptValidationResult, prompt: str) -> None:
        """
        Log validation result for audit trail.

        Args:
            result: Validation result
            prompt: Original prompt (will be anonymized if needed)
        """
        log_extra = {
            "validation_result": result.action.value,
            "is_valid": result.is_valid,
            "issue_count": len(result.issues),
            "safe_for_logging": result.safe_for_logging,
            **result.audit_metadata,
        }

        if result.is_valid:
            logger.info("Prompt validation passed", extra=log_extra)
        else:
            # Log with appropriate level based on action
            if result.action == ValidationAction.BLOCK:
                logger.warning(
                    "Prompt validation BLOCKED",
                    extra={
                        **log_extra,
                        "prompt": result.anonymized_prompt or "[REDACTED]",
                        "issues": [
                            {
                                "type": i.type,
                                "severity": i.severity,
                                "message": i.message,
                            }
                            for i in result.issues
                        ],
                    },
                )
            elif result.action == ValidationAction.WARN:
                logger.warning("Prompt validation WARNING", extra=log_extra)


# Global instance
_prompt_validator: Optional[PromptSecurityValidator] = None


def get_prompt_validator() -> PromptSecurityValidator:
    """
    Get or create global prompt validator instance.

    Returns:
        PromptSecurityValidator: Global validator instance
    """
    global _prompt_validator
    if _prompt_validator is None:
        _prompt_validator = PromptSecurityValidator()
    return _prompt_validator


def validate_prompt(
    prompt: str,
    max_length: int = 2000,
    min_length: int = 3,
    strict_mode: bool = False,
) -> PromptValidationResult:
    """
    Convenience function to validate a prompt.

    Args:
        prompt: Prompt to validate
        max_length: Maximum allowed length
        min_length: Minimum required length
        strict_mode: Enable strict validation

    Returns:
        PromptValidationResult

    Raises:
        PIIDetectedError: If PII detected and blocking enabled
        ContentViolationError: If content violations detected
    """
    validator = get_prompt_validator()
    return validator.validate(prompt, max_length, min_length, strict_mode)


# ⚠️  SECURITY NOTES:
# - Always validate prompts before processing
# - Never log original prompts that contain PII
# - Review validation logs regularly
# - Update detection patterns based on new threats
#
# 📋 ISO 27001 Control Mapping:
# - A.12.2.1: Controls against malware
# - A.12.6.1: Management of technical vulnerabilities
# - A.18.1.4: Privacy and protection of PII
