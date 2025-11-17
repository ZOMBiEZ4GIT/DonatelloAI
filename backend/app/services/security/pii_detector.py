"""
╔════════════════════════════════════════════════════════╗
║           PII Detection Service                         ║
║         🔒 Personally Identifiable Information         ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Detects sensitive information in user prompts
    - Prevents data leaks and compliance violations
    - Supports GDPR, Privacy Act, and ISO 27001 compliance

Security Considerations:
    - Comprehensive pattern matching for various PII types
    - Configurable confidence thresholds
    - Detailed detection results for audit logging
    - Supports anonymization for logging purposes

ISO 27001 Controls:
    - A.18.1.4: Privacy and protection of PII
    - A.12.3.1: Information backup
    - A.12.4.1: Event logging
    - A.8.2.3: Handling of assets

Compliance:
    - GDPR Article 5: Data protection principles
    - Privacy Act 1988 (Cth): APPs 1-13
    - ISO 27001:2013 Annex A.18.1.4
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Pattern

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PIIType(str, Enum):
    """Types of PII that can be detected."""

    # Personal identifiers
    SSN = "ssn"
    EMAIL = "email"
    PHONE = "phone"
    IP_ADDRESS = "ip_address"

    # Financial
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    ROUTING_NUMBER = "routing_number"
    IBAN = "iban"

    # Government IDs
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    MEDICARE_NUMBER = "medicare_number"
    TAX_FILE_NUMBER = "tax_file_number"

    # Credentials & Secrets
    API_KEY = "api_key"
    AWS_KEY = "aws_key"
    GOOGLE_API_KEY = "google_api_key"
    GITHUB_TOKEN = "github_token"
    JWT_TOKEN = "jwt_token"
    PASSWORD = "password"
    PRIVATE_KEY = "private_key"
    DATABASE_CONNECTION = "database_connection"

    # Medical
    MEDICAL_RECORD_NUMBER = "medical_record_number"
    HEALTH_INSURANCE_NUMBER = "health_insurance_number"

    # Other
    DATE_OF_BIRTH = "date_of_birth"
    HOME_ADDRESS = "home_address"


@dataclass
class PIIDetection:
    """Result of PII detection."""

    type: PIIType
    value: str  # The detected PII (masked for logging)
    start: int
    end: int
    confidence: float
    context: str  # Surrounding text for context


@dataclass
class PIIDetectionResult:
    """Overall result of PII detection scan."""

    contains_pii: bool
    detections: List[PIIDetection]
    confidence: float
    safe_for_logging: bool
    anonymized_text: Optional[str] = None


class PIIDetector:
    """
    Comprehensive PII detection service.

    Detects various types of personally identifiable information
    and sensitive data in text inputs.
    """

    def __init__(self):
        """Initialize PII detector with pattern configurations."""
        self.enabled = settings.ENABLE_PII_DETECTION
        self.threshold = settings.PII_DETECTION_THRESHOLD
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for PII detection."""
        self.patterns: Dict[PIIType, List[Pattern]] = {
            # Personal Identifiers
            PIIType.SSN: [
                re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # US SSN: 123-45-6789
                re.compile(r'\b\d{9}\b'),  # SSN without dashes
            ],
            PIIType.EMAIL: [
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            ],
            PIIType.PHONE: [
                re.compile(r'\b(?:\+?61|0)[2-478](?:[ -]?[0-9]){8}\b'),  # Australian
                re.compile(r'\b\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),  # US/Canada
                re.compile(r'\b\+[1-9]{1}[0-9]{1,14}\b'),  # International
            ],
            PIIType.IP_ADDRESS: [
                re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),  # IPv4
                re.compile(r'\b(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}\b', re.IGNORECASE),  # IPv6
            ],

            # Financial
            PIIType.CREDIT_CARD: [
                re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?)\b'),  # Visa
                re.compile(r'\b(?:5[1-5][0-9]{14})\b'),  # Mastercard
                re.compile(r'\b(?:3[47][0-9]{13})\b'),  # Amex
                re.compile(r'\b(?:6(?:011|5[0-9]{2})[0-9]{12})\b'),  # Discover
            ],
            PIIType.BANK_ACCOUNT: [
                re.compile(r'\b[0-9]{6,17}\b'),  # Generic account number
            ],
            PIIType.ROUTING_NUMBER: [
                re.compile(r'\b[0-9]{9}\b'),  # US routing number
                re.compile(r'\b[0-9]{6}-[0-9]{3}\b'),  # Australian BSB
            ],
            PIIType.IBAN: [
                re.compile(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b'),
            ],

            # Government IDs
            PIIType.PASSPORT: [
                re.compile(r'\b[A-Z]{1,2}[0-9]{6,9}\b'),  # Generic passport
            ],
            PIIType.DRIVERS_LICENSE: [
                re.compile(r'\b[A-Z0-9]{5,15}\b'),  # Generic DL
            ],
            PIIType.MEDICARE_NUMBER: [
                re.compile(r'\b[2-6]\d{3}\s?\d{5}\s?\d\b'),  # Australian Medicare
            ],
            PIIType.TAX_FILE_NUMBER: [
                re.compile(r'\b\d{3}\s?\d{3}\s?\d{3}\b'),  # Australian TFN
                re.compile(r'\b\d{9}\b'),  # TFN without spaces
            ],

            # Credentials & Secrets
            PIIType.API_KEY: [
                re.compile(r'\b(?:api[_-]?key|apikey)["\s:=]+([a-zA-Z0-9_\-]{16,64})', re.IGNORECASE),
                re.compile(r'\b[a-zA-Z0-9_\-]{32,64}\b'),  # Generic API key pattern
            ],
            PIIType.AWS_KEY: [
                re.compile(r'\b(AKIA[0-9A-Z]{16})\b'),  # AWS Access Key
                re.compile(r'\b(aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40})', re.IGNORECASE),
            ],
            PIIType.GOOGLE_API_KEY: [
                re.compile(r'\bAIza[0-9A-Za-z_\-]{35}\b'),
            ],
            PIIType.GITHUB_TOKEN: [
                re.compile(r'\bgh[pousr]_[A-Za-z0-9_]{36,255}\b'),
                re.compile(r'\bgithub_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}\b'),
            ],
            PIIType.JWT_TOKEN: [
                re.compile(r'\beyJ[A-Za-z0-9_\-]*\.eyJ[A-Za-z0-9_\-]*\.[A-Za-z0-9_\-]*\b'),
            ],
            PIIType.PASSWORD: [
                re.compile(r'(?:password|passwd|pwd)["\s:=]+([^\s]{8,})', re.IGNORECASE),
            ],
            PIIType.PRIVATE_KEY: [
                re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----'),
                re.compile(r'-----BEGIN OPENSSH PRIVATE KEY-----'),
            ],
            PIIType.DATABASE_CONNECTION: [
                re.compile(r'\b(?:mysql|postgres|mongodb|redis)://[^\s]+:[^\s]+@[^\s]+', re.IGNORECASE),
                re.compile(r'\bServer=[^;]+;Database=[^;]+;User Id=[^;]+;Password=[^;]+', re.IGNORECASE),
            ],

            # Medical
            PIIType.MEDICAL_RECORD_NUMBER: [
                re.compile(r'\b(?:MRN|Medical Record)[:\s#]+([0-9]{6,10})\b', re.IGNORECASE),
            ],
            PIIType.HEALTH_INSURANCE_NUMBER: [
                re.compile(r'\b[A-Z]{3}[0-9]{9}[A-Z]{2}\b'),  # Generic health insurance
            ],

            # Other
            PIIType.DATE_OF_BIRTH: [
                re.compile(r'\b(?:0[1-9]|[12][0-9]|3[01])[/-](?:0[1-9]|1[012])[/-](?:19|20)\d\d\b'),  # DD/MM/YYYY
                re.compile(r'\b(?:19|20)\d\d[/-](?:0[1-9]|1[012])[/-](?:0[1-9]|[12][0-9]|3[01])\b'),  # YYYY-MM-DD
            ],
            PIIType.HOME_ADDRESS: [
                re.compile(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Court|Ct|Boulevard|Blvd)\b', re.IGNORECASE),
            ],
        }

    def detect(self, text: str) -> PIIDetectionResult:
        """
        Detect PII in the given text.

        Args:
            text: Text to scan for PII

        Returns:
            PIIDetectionResult with detection details
        """
        if not self.enabled:
            logger.debug("PII detection is disabled")
            return PIIDetectionResult(
                contains_pii=False,
                detections=[],
                confidence=0.0,
                safe_for_logging=True,
            )

        detections: List[PIIDetection] = []

        for pii_type, patterns in self.patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    # Extract context (20 chars before and after)
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end]

                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_confidence(pii_type, match.group())

                    # Mask the detected value
                    masked_value = self._mask_value(match.group())

                    detection = PIIDetection(
                        type=pii_type,
                        value=masked_value,
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence,
                        context=self._mask_value(context),
                    )
                    detections.append(detection)

        # Calculate overall confidence (average of all detections)
        overall_confidence = (
            sum(d.confidence for d in detections) / len(detections)
            if detections
            else 0.0
        )

        # Determine if contains PII based on threshold
        contains_pii = overall_confidence >= self.threshold

        # Create anonymized version
        anonymized_text = self._anonymize_text(text, detections) if contains_pii else None

        result = PIIDetectionResult(
            contains_pii=contains_pii,
            detections=detections,
            confidence=overall_confidence,
            safe_for_logging=not contains_pii,
            anonymized_text=anonymized_text,
        )

        # Log detection event
        if contains_pii:
            logger.warning(
                "PII detected in text",
                extra={
                    "pii_types": [d.type.value for d in detections],
                    "detection_count": len(detections),
                    "confidence": overall_confidence,
                },
            )

        return result

    def _calculate_confidence(self, pii_type: PIIType, value: str) -> float:
        """
        Calculate confidence score for a detection.

        Args:
            pii_type: Type of PII detected
            value: The detected value

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence levels by type
        base_confidence = {
            PIIType.SSN: 0.95,
            PIIType.EMAIL: 0.90,
            PIIType.CREDIT_CARD: 0.95,
            PIIType.AWS_KEY: 0.98,
            PIIType.GOOGLE_API_KEY: 0.98,
            PIIType.GITHUB_TOKEN: 0.98,
            PIIType.JWT_TOKEN: 0.95,
            PIIType.PRIVATE_KEY: 0.99,
            PIIType.DATABASE_CONNECTION: 0.98,
            PIIType.PHONE: 0.85,
            PIIType.IP_ADDRESS: 0.70,
            PIIType.MEDICARE_NUMBER: 0.90,
            PIIType.TAX_FILE_NUMBER: 0.92,
            PIIType.BANK_ACCOUNT: 0.75,
            PIIType.API_KEY: 0.85,
            PIIType.PASSWORD: 0.90,
            PIIType.MEDICAL_RECORD_NUMBER: 0.85,
            PIIType.DATE_OF_BIRTH: 0.75,
            PIIType.HOME_ADDRESS: 0.80,
            PIIType.PASSPORT: 0.80,
            PIIType.DRIVERS_LICENSE: 0.75,
            PIIType.ROUTING_NUMBER: 0.85,
            PIIType.IBAN: 0.90,
            PIIType.HEALTH_INSURANCE_NUMBER: 0.85,
        }

        # Additional validation for specific types
        if pii_type == PIIType.CREDIT_CARD:
            # Luhn algorithm check for credit cards
            if self._validate_luhn(value):
                return 0.99
            return 0.70

        return base_confidence.get(pii_type, 0.70)

    def _validate_luhn(self, number: str) -> bool:
        """
        Validate credit card number using Luhn algorithm.

        Args:
            number: Credit card number to validate

        Returns:
            True if valid, False otherwise
        """
        digits = [int(d) for d in number if d.isdigit()]
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0

    def _mask_value(self, value: str, show_chars: int = 2) -> str:
        """
        Mask sensitive value for logging.

        Args:
            value: Value to mask
            show_chars: Number of characters to show at start/end

        Returns:
            Masked value
        """
        if len(value) <= show_chars * 2:
            return "*" * len(value)

        return f"{value[:show_chars]}{'*' * (len(value) - show_chars * 2)}{value[-show_chars:]}"

    def _anonymize_text(self, text: str, detections: List[PIIDetection]) -> str:
        """
        Create anonymized version of text with PII replaced.

        Args:
            text: Original text
            detections: List of PII detections

        Returns:
            Anonymized text
        """
        # Sort detections by position (reverse order for replacement)
        sorted_detections = sorted(detections, key=lambda d: d.start, reverse=True)

        anonymized = text
        for detection in sorted_detections:
            replacement = f"[{detection.type.value.upper()}_REDACTED]"
            anonymized = (
                anonymized[: detection.start]
                + replacement
                + anonymized[detection.end :]
            )

        return anonymized


# Global instance
_pii_detector: Optional[PIIDetector] = None


def get_pii_detector() -> PIIDetector:
    """
    Get or create global PII detector instance.

    Returns:
        PIIDetector: Global PII detector instance
    """
    global _pii_detector
    if _pii_detector is None:
        _pii_detector = PIIDetector()
    return _pii_detector


# ⚠️  SECURITY NOTES:
# - Always mask PII in logs
# - Never store PII in plaintext audit logs
# - Use anonymized text for debugging
# - Update patterns regularly for new threats
#
# 📋 ISO 27001 Control Mapping:
# - A.18.1.4: Privacy and protection of PII
# - A.12.3.1: Information backup
# - A.12.4.1: Event logging
# - A.8.2.3: Handling of assets
