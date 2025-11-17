"""
╔════════════════════════════════════════════════════════╗
║           Content Moderation Service                    ║
║         🛡️ Harmful Content Detection                   ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Detects inappropriate, harmful, or malicious content
    - Prevents platform abuse and brand risk
    - Ensures safe and compliant usage

Security Considerations:
    - Multi-layer content analysis
    - Configurable severity thresholds
    - Detailed violation logging
    - Support for custom blocklists

ISO 27001 Controls:
    - A.13.2.2: Agreements on information transfer
    - A.18.1.3: Protection of records
    - A.12.6.1: Management of technical vulnerabilities
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

from app.core.logging import get_logger

logger = get_logger(__name__)


class ContentViolationType(str, Enum):
    """Types of content violations."""

    # Security threats
    INJECTION_ATTEMPT = "injection_attempt"
    COMMAND_INJECTION = "command_injection"
    XSS_ATTEMPT = "xss_attempt"
    PATH_TRAVERSAL = "path_traversal"

    # Inappropriate content
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SEXUAL_CONTENT = "sexual_content"
    HARASSMENT = "harassment"

    # Illegal content
    ILLEGAL_ACTIVITY = "illegal_activity"
    COPYRIGHT_VIOLATION = "copyright_violation"
    TRADEMARK_VIOLATION = "trademark_violation"

    # Spam/Abuse
    SPAM = "spam"
    REPETITIVE_CONTENT = "repetitive_content"
    EXCESSIVE_LENGTH = "excessive_length"

    # Platform abuse
    PROMPT_INJECTION = "prompt_injection"
    SYSTEM_MANIPULATION = "system_manipulation"
    RESOURCE_ABUSE = "resource_abuse"


class ViolationSeverity(str, Enum):
    """Severity levels for content violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ContentViolation:
    """Detected content violation."""

    type: ContentViolationType
    severity: ViolationSeverity
    description: str
    matched_pattern: str
    confidence: float


@dataclass
class ContentFilterResult:
    """Result of content filtering."""

    is_safe: bool
    violations: List[ContentViolation]
    risk_score: float
    action: str  # "allow", "warn", "block"
    reason: Optional[str] = None


class ContentFilter:
    """
    Content moderation and filtering service.

    Detects harmful, inappropriate, or malicious content
    in user inputs.
    """

    def __init__(self):
        """Initialize content filter with patterns."""
        self._initialize_patterns()
        self._initialize_blocklists()

    def _initialize_patterns(self) -> None:
        """Initialize detection patterns for various violation types."""
        self.patterns: Dict[ContentViolationType, List[tuple]] = {
            # Security threats
            ContentViolationType.INJECTION_ATTEMPT: [
                (re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL), ViolationSeverity.CRITICAL),
                (re.compile(r'javascript:', re.IGNORECASE), ViolationSeverity.HIGH),
                (re.compile(r'on\w+\s*=', re.IGNORECASE), ViolationSeverity.HIGH),  # Event handlers
            ],
            ContentViolationType.COMMAND_INJECTION: [
                (re.compile(r'[;&|`$(){}]', re.IGNORECASE), ViolationSeverity.HIGH),
                (re.compile(r'(?:rm|del|format)\s+-[rf]', re.IGNORECASE), ViolationSeverity.CRITICAL),
                (re.compile(r'\$\([^)]+\)', re.IGNORECASE), ViolationSeverity.HIGH),
            ],
            ContentViolationType.XSS_ATTEMPT: [
                (re.compile(r'<iframe[^>]*>', re.IGNORECASE), ViolationSeverity.HIGH),
                (re.compile(r'<embed[^>]*>', re.IGNORECASE), ViolationSeverity.HIGH),
                (re.compile(r'<object[^>]*>', re.IGNORECASE), ViolationSeverity.HIGH),
            ],
            ContentViolationType.PATH_TRAVERSAL: [
                (re.compile(r'\.\./|\.\.\\', re.IGNORECASE), ViolationSeverity.HIGH),
                (re.compile(r'(?:/etc/passwd|/etc/shadow)', re.IGNORECASE), ViolationSeverity.CRITICAL),
            ],

            # Prompt injection attempts
            ContentViolationType.PROMPT_INJECTION: [
                (re.compile(r'ignore\s+(?:previous|above|all)\s+(?:instructions|prompts|commands)', re.IGNORECASE), ViolationSeverity.HIGH),
                (re.compile(r'system\s*:\s*you\s+are', re.IGNORECASE), ViolationSeverity.MEDIUM),
                (re.compile(r'(?:disregard|forget)\s+(?:your|the)\s+(?:rules|instructions)', re.IGNORECASE), ViolationSeverity.HIGH),
                (re.compile(r'new\s+instructions?:', re.IGNORECASE), ViolationSeverity.MEDIUM),
                (re.compile(r'override\s+(?:your|the)\s+(?:settings|configuration)', re.IGNORECASE), ViolationSeverity.HIGH),
            ],
            ContentViolationType.SYSTEM_MANIPULATION: [
                (re.compile(r'</system>|<system>|</admin>|<admin>', re.IGNORECASE), ViolationSeverity.HIGH),
                (re.compile(r'sudo|su\s+root|chmod\s+777', re.IGNORECASE), ViolationSeverity.MEDIUM),
            ],

            # Spam patterns
            ContentViolationType.SPAM: [
                (re.compile(r'(?:click|visit|check|buy)\s+(?:here|now|today)', re.IGNORECASE), ViolationSeverity.LOW),
                (re.compile(r'(?:100%|guaranteed)\s+(?:free|money|income)', re.IGNORECASE), ViolationSeverity.LOW),
            ],
            ContentViolationType.REPETITIVE_CONTENT: [
                (re.compile(r'(.{10,}?)\1{5,}'), ViolationSeverity.LOW),  # Repeated strings
            ],
        }

    def _initialize_blocklists(self) -> None:
        """Initialize blocklists for known problematic content."""
        # Hate speech keywords (sample - should be more comprehensive)
        self.hate_speech_keywords: Set[str] = {
            # This is a minimal example - production should use comprehensive lists
            # and context-aware detection
        }

        # Violence keywords
        self.violence_keywords: Set[str] = {
            "murder", "kill", "torture", "bomb", "terrorist", "weapon",
            "explosive", "assault", "massacre"
        }

        # Sexual content keywords (age-restricted)
        self.sexual_keywords: Set[str] = {
            "explicit", "pornographic", "xxx", "nsfw"
        }

        # Illegal activity keywords
        self.illegal_keywords: Set[str] = {
            "drugs", "cocaine", "heroin", "methamphetamine",
            "counterfeit", "fraud", "money laundering", "hack", "crack",
            "exploit", "vulnerability", "zero-day"
        }

    def filter(self, text: str, max_length: int = 2000) -> ContentFilterResult:
        """
        Filter content for violations.

        Args:
            text: Text to analyze
            max_length: Maximum allowed length

        Returns:
            ContentFilterResult with analysis
        """
        violations: List[ContentViolation] = []

        # Check length
        if len(text) > max_length:
            violations.append(
                ContentViolation(
                    type=ContentViolationType.EXCESSIVE_LENGTH,
                    severity=ViolationSeverity.MEDIUM,
                    description=f"Content exceeds maximum length of {max_length}",
                    matched_pattern="length_check",
                    confidence=1.0,
                )
            )

        # Check patterns
        for violation_type, patterns in self.patterns.items():
            for pattern, severity in patterns:
                if pattern.search(text):
                    violations.append(
                        ContentViolation(
                            type=violation_type,
                            severity=severity,
                            description=f"Detected {violation_type.value}",
                            matched_pattern=pattern.pattern,
                            confidence=0.9,
                        )
                    )

        # Check keyword blocklists
        text_lower = text.lower()

        # Hate speech
        for keyword in self.hate_speech_keywords:
            if keyword in text_lower:
                violations.append(
                    ContentViolation(
                        type=ContentViolationType.HATE_SPEECH,
                        severity=ViolationSeverity.CRITICAL,
                        description="Contains hate speech",
                        matched_pattern=keyword,
                        confidence=0.8,
                    )
                )

        # Violence
        violence_matches = sum(1 for kw in self.violence_keywords if kw in text_lower)
        if violence_matches >= 2:  # Multiple violence keywords
            violations.append(
                ContentViolation(
                    type=ContentViolationType.VIOLENCE,
                    severity=ViolationSeverity.HIGH,
                    description="Contains violent content",
                    matched_pattern=f"{violence_matches} violence keywords",
                    confidence=0.7,
                )
            )

        # Sexual content
        for keyword in self.sexual_keywords:
            if keyword in text_lower:
                violations.append(
                    ContentViolation(
                        type=ContentViolationType.SEXUAL_CONTENT,
                        severity=ViolationSeverity.HIGH,
                        description="Contains explicit sexual content",
                        matched_pattern=keyword,
                        confidence=0.8,
                    )
                )

        # Illegal activity
        illegal_matches = sum(1 for kw in self.illegal_keywords if kw in text_lower)
        if illegal_matches >= 2:
            violations.append(
                ContentViolation(
                    type=ContentViolationType.ILLEGAL_ACTIVITY,
                    severity=ViolationSeverity.CRITICAL,
                    description="References illegal activities",
                    matched_pattern=f"{illegal_matches} illegal keywords",
                    confidence=0.75,
                )
            )

        # Calculate risk score
        risk_score = self._calculate_risk_score(violations)

        # Determine action
        action, reason = self._determine_action(violations, risk_score)

        result = ContentFilterResult(
            is_safe=action == "allow",
            violations=violations,
            risk_score=risk_score,
            action=action,
            reason=reason,
        )

        # Log if violations found
        if violations:
            logger.warning(
                "Content violations detected",
                extra={
                    "violation_count": len(violations),
                    "risk_score": risk_score,
                    "action": action,
                    "violation_types": [v.type.value for v in violations],
                },
            )

        return result

    def _calculate_risk_score(self, violations: List[ContentViolation]) -> float:
        """
        Calculate overall risk score.

        Args:
            violations: List of violations

        Returns:
            Risk score between 0.0 and 1.0
        """
        if not violations:
            return 0.0

        severity_weights = {
            ViolationSeverity.LOW: 0.25,
            ViolationSeverity.MEDIUM: 0.50,
            ViolationSeverity.HIGH: 0.75,
            ViolationSeverity.CRITICAL: 1.0,
        }

        total_score = sum(
            severity_weights[v.severity] * v.confidence for v in violations
        )

        # Normalize by number of violations (max 1.0)
        return min(1.0, total_score / max(1, len(violations)))

    def _determine_action(
        self, violations: List[ContentViolation], risk_score: float
    ) -> tuple[str, Optional[str]]:
        """
        Determine what action to take based on violations.

        Args:
            violations: List of violations
            risk_score: Overall risk score

        Returns:
            Tuple of (action, reason)
        """
        # Critical violations always block
        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        if critical_violations:
            return (
                "block",
                f"Critical security violation: {critical_violations[0].description}",
            )

        # High risk score blocks
        if risk_score >= 0.75:
            return ("block", "Content contains multiple high-risk violations")

        # Medium risk warns
        if risk_score >= 0.40:
            return ("warn", "Content may contain inappropriate material")

        # Low risk allows
        return ("allow", None)


# Global instance
_content_filter: Optional[ContentFilter] = None


def get_content_filter() -> ContentFilter:
    """
    Get or create global content filter instance.

    Returns:
        ContentFilter: Global content filter instance
    """
    global _content_filter
    if _content_filter is None:
        _content_filter = ContentFilter()
    return _content_filter


# ⚠️  SECURITY NOTES:
# - Regularly update blocklists and patterns
# - Consider ML-based content moderation for production
# - Log all violations for analysis and improvement
# - Review false positives to refine patterns
#
# 📋 ISO 27001 Control Mapping:
# - A.13.2.2: Agreements on information transfer
# - A.18.1.3: Protection of records
# - A.12.6.1: Management of technical vulnerabilities
