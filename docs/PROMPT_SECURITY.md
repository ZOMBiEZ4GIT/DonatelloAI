# Prompt Security Guide

## Overview

The DonatelloAI platform implements **comprehensive multi-layered security** to prevent users from uploading sensitive information and to protect against security threats. This guide explains the security measures in place and how to configure them.

---

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [PII Detection](#pii-detection)
3. [Content Filtering](#content-filtering)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Best Practices](#best-practices)
7. [Compliance](#compliance)
8. [Troubleshooting](#troubleshooting)

---

## Security Architecture

### Multi-Layer Defense

The platform implements defense-in-depth with multiple security layers:

```
┌─────────────────────────────────────────────────────┐
│                  User Input                          │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Layer 1: Frontend Validation (Immediate Feedback)   │
│  - Real-time PII detection                          │
│  - Pattern matching for sensitive data              │
│  - Security threat detection                        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Layer 2: Backend PII Detector (Comprehensive)       │
│  - 20+ PII types detected                           │
│  - Confidence scoring                               │
│  - Automatic anonymization                          │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Layer 3: Content Filter (Threat Detection)         │
│  - Injection attack prevention                      │
│  - Prompt injection blocking                        │
│  - Malicious content detection                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Layer 4: Security Audit Logging                    │
│  - All violations logged                            │
│  - Anonymized for compliance                        │
│  - 7-year retention                                 │
└─────────────────────────────────────────────────────┘
```

---

## PII Detection

### Detected PII Types

The system detects **20+ types** of personally identifiable information:

#### Critical Severity

🔴 **Credentials & Secrets**
- AWS Access Keys (`AKIA...`)
- Google API Keys (`AIza...`)
- GitHub Tokens (`ghp_...`, `github_pat_...`)
- JWT Tokens
- Private Keys (RSA, EC, OpenSSH)
- Database Connection Strings
- Passwords

#### High Severity

🟠 **Financial & Government IDs**
- Social Security Numbers (US: `123-45-6789`)
- Credit Card Numbers (Visa, Mastercard, Amex, Discover)
- Medicare Numbers (AU: `2123 45678 9`)
- Tax File Numbers (AU: `123 456 789`)
- IBAN (International Bank Account Numbers)
- Bank Account Numbers
- Routing Numbers

#### Medium Severity

🟡 **Contact Information**
- Email Addresses
- Phone Numbers (AU, US, International)
- IP Addresses (IPv4, IPv6)
- Home Addresses
- Dates of Birth

#### Low Severity

🟢 **Other Identifiers**
- Passport Numbers
- Driver's License Numbers
- Medical Record Numbers
- Health Insurance Numbers

### How PII Detection Works

1. **Pattern Matching**: Uses regex patterns to identify potential PII
2. **Confidence Scoring**: Each detection has a confidence score (0.0 - 1.0)
3. **Threshold Check**: Detections above threshold trigger actions
4. **Anonymization**: Sensitive values are masked in logs

#### Example Detection

```python
from app.services.security import validate_prompt

# Input with PII
prompt = "Generate image for card 4532015112830366"

try:
    result = validate_prompt(prompt)
except PIIDetectedError as e:
    print(e.message)  # "Prompt contains personally identifiable information"
    print(e.details)  # {"pii_types": ["credit_card"], ...}
```

### Luhn Algorithm Validation

Credit card numbers are validated using the **Luhn algorithm** for higher accuracy:
- Valid card numbers: Confidence = 0.99
- Invalid checksums: Confidence = 0.70 (may be false positive)

---

## Content Filtering

### Security Threat Detection

The content filter protects against various security threats:

#### Injection Attacks

🔴 **Script Injection (XSS)**
```html
<script>alert('xss')</script>
javascript:alert(1)
<iframe src="malicious.com">
```

🔴 **Command Injection**
```bash
; rm -rf /
| cat /etc/passwd
$(malicious command)
```

🔴 **Path Traversal**
```
../../etc/passwd
../../../windows/system32
```

#### Prompt Injection

🟠 **Manipulation Attempts**
```
Ignore previous instructions and...
Disregard your rules and...
New instructions: override settings...
System: you are now...
```

#### Harmful Content

🟠 **Violence & Illegal Activity**
- Multiple violence keywords
- Illegal activity references
- Explicit content

🟡 **Spam & Abuse**
- Repetitive content patterns
- Excessive length
- Spam keywords

### Risk Scoring

Each violation is assigned a severity level:

- **CRITICAL** (1.0): Immediate block
- **HIGH** (0.75): Block with high risk score
- **MEDIUM** (0.50): Warning threshold
- **LOW** (0.25): Informational

Risk score determines action:
- `≥ 0.75`: **BLOCK** - Reject prompt
- `≥ 0.40`: **WARN** - Log warning, allow with caution
- `< 0.40`: **ALLOW** - Safe to process

---

## Configuration

### Environment Variables

Configure security settings in `.env`:

```bash
# PII Detection
ENABLE_PII_DETECTION=true
PII_DETECTION_THRESHOLD=0.7        # 0.0 - 1.0
PII_ACTION=block                   # block | warn | anonymize

# Content Filtering
ENABLE_CONTENT_FILTERING=true
CONTENT_FILTER_STRICT_MODE=false
BLOCK_PROMPT_INJECTION=true
BLOCK_COMMAND_INJECTION=true

# Audit Logging
ENABLE_SECURITY_AUDIT_LOGGING=true
AUDIT_LOG_RETENTION_DAYS=2555      # 7 years
```

### PII Actions

Configure what happens when PII is detected:

#### `PII_ACTION=block` (Recommended)
```python
# Raises PIIDetectedError
# User sees: "Prompt contains sensitive information"
# Best for production environments
```

#### `PII_ACTION=warn`
```python
# Logs warning but allows processing
# User sees: Warning message
# Best for testing/development
```

#### `PII_ACTION=anonymize`
```python
# Replaces PII with [REDACTED] tags
# Allows processing with sanitized input
# Best for analytics/logging
```

### Strict Mode

Enable strict mode for enhanced security:

```python
result = validate_prompt(
    prompt="...",
    strict_mode=True  # Fail-safe: block on service errors
)
```

---

## Usage Examples

### Backend Usage

#### Basic Validation

```python
from app.services.security import validate_prompt
from app.core.exceptions import PIIDetectedError, ContentViolationError

try:
    result = validate_prompt(
        prompt=user_input,
        max_length=2000,
        min_length=3,
        strict_mode=False
    )

    if result.is_valid:
        # Process the prompt
        generate_image(prompt)
    else:
        # Handle validation issues
        for issue in result.issues:
            print(f"{issue.severity}: {issue.message}")

except PIIDetectedError as e:
    # PII detected and blocked
    log_security_event("pii_detected", e.details)
    return error_response("Sensitive information detected")

except ContentViolationError as e:
    # Harmful content detected
    log_security_event("content_violation", e.details)
    return error_response("Content policy violation")
```

#### Advanced Usage

```python
from app.services.security import (
    get_pii_detector,
    get_content_filter,
    get_prompt_validator
)

# Individual services
pii_detector = get_pii_detector()
content_filter = get_content_filter()
validator = get_prompt_validator()

# PII detection only
pii_result = pii_detector.detect(text)
if pii_result.contains_pii:
    print(f"Detected {len(pii_result.detections)} PII instances")
    print(f"Anonymized: {pii_result.anonymized_text}")

# Content filtering only
content_result = content_filter.filter(text)
if not content_result.is_safe:
    print(f"Risk score: {content_result.risk_score}")
    print(f"Violations: {[v.type for v in content_result.violations]}")

# Complete validation
validation_result = validator.validate(text)
print(f"Action: {validation_result.action}")
print(f"Audit metadata: {validation_result.audit_metadata}")
```

### Frontend Usage

```typescript
import { validatePrompt } from '@/utils/validators';

const handleSubmit = (prompt: string) => {
  const result = validatePrompt(prompt);

  if (!result.valid) {
    // Show error to user
    showError(result.error);
    return;
  }

  if (result.warnings && result.warnings.length > 0) {
    // Show warnings
    result.warnings.forEach(warning => showWarning(warning));
  }

  // Proceed with submission
  submitPrompt(prompt);
};
```

---

## Best Practices

### For Developers

1. **Always Validate on Backend**
   - Frontend validation is for UX only
   - Never trust client-side validation
   - Backend validation is your security boundary

2. **Never Log Sensitive Data**
   ```python
   # ❌ BAD
   logger.info(f"Processing prompt: {user_prompt}")

   # ✅ GOOD
   if result.safe_for_logging:
       logger.info(f"Processing prompt: {user_prompt}")
   else:
       logger.info(f"Processing prompt: {result.anonymized_prompt}")
   ```

3. **Review Security Logs Regularly**
   - Monitor for attack patterns
   - Update detection rules based on findings
   - Analyze false positives

4. **Keep Patterns Updated**
   - Review new credential formats
   - Update regex patterns quarterly
   - Subscribe to security bulletins

### For Users

1. **Don't Include Personal Information**
   - No SSN, credit cards, or passwords
   - No email addresses or phone numbers
   - No API keys or tokens

2. **Use Generic Descriptions**
   ```
   ❌ "Generate image for John Smith at 123 Main St"
   ✅ "Generate image of a person at a house"
   ```

3. **Report False Positives**
   - Help improve the system
   - Contact support if legitimate content blocked

---

## Compliance

### Standards Compliance

The prompt security system supports compliance with:

#### ISO 27001:2013
- **A.18.1.4**: Privacy and protection of PII
- **A.12.2.1**: Controls against malware
- **A.12.6.1**: Management of technical vulnerabilities
- **A.12.4.1**: Event logging

#### GDPR (EU)
- **Article 5**: Data protection principles
- **Article 25**: Data protection by design
- **Article 32**: Security of processing

#### Privacy Act 1988 (Australia)
- **APPs 1-13**: Australian Privacy Principles
- **Notifiable Data Breaches**: Prevent PII exposure

### Audit Trail

All security events are logged with:
- Timestamp (UTC)
- User ID (anonymized)
- Action taken (block/warn/allow)
- PII types detected
- Risk score
- Anonymized content
- Request ID for tracing

**Retention**: 7 years (2555 days) for compliance

---

## Troubleshooting

### Common Issues

#### False Positives

**Issue**: Legitimate content blocked as PII

**Solution**:
```python
# Adjust confidence threshold
PII_DETECTION_THRESHOLD=0.8  # Increase from 0.7

# Or switch to warn mode for testing
PII_ACTION=warn
```

#### Performance Concerns

**Issue**: Validation taking too long

**Solution**:
```python
# Optimize patterns (remove redundant checks)
# Use async validation for large batches
# Cache validation results for identical prompts
```

#### Missing PII Types

**Issue**: New PII type not detected

**Solution**:
1. Add pattern to `pii_detector.py`
2. Test with unit test
3. Update confidence scoring
4. Deploy and monitor

### Debugging

Enable debug logging:

```bash
LOG_LEVEL=DEBUG
```

Check validation details:

```python
result = validate_prompt(prompt)
print(f"Validation issues: {result.issues}")
print(f"PII detections: {result.pii_result.detections if result.pii_result else 'None'}")
print(f"Content violations: {result.content_result.violations if result.content_result else 'None'}")
print(f"Audit metadata: {result.audit_metadata}")
```

---

## API Reference

### Core Functions

#### `validate_prompt()`

```python
def validate_prompt(
    prompt: str,
    max_length: int = 2000,
    min_length: int = 3,
    strict_mode: bool = False
) -> PromptValidationResult
```

**Parameters:**
- `prompt`: Text to validate
- `max_length`: Maximum allowed length (default: 2000)
- `min_length`: Minimum required length (default: 3)
- `strict_mode`: Fail-safe mode (default: False)

**Returns:** `PromptValidationResult`

**Raises:**
- `PIIDetectedError`: When PII found and `PII_ACTION=block`
- `ContentViolationError`: When harmful content found

#### `PromptValidationResult`

```python
@dataclass
class PromptValidationResult:
    is_valid: bool                           # Overall validation status
    action: ValidationAction                 # ALLOW | WARN | BLOCK
    issues: List[ValidationIssue]           # All issues found
    pii_result: Optional[PIIDetectionResult] # PII detection details
    content_result: Optional[ContentFilterResult] # Content filter details
    anonymized_prompt: Optional[str]         # Sanitized version
    safe_for_logging: bool                   # Can log original?
    audit_metadata: dict                     # Metadata for audit
```

---

## Support

For questions or issues:

- **Documentation**: See `/docs` directory
- **Issue Tracker**: GitHub Issues
- **Security Concerns**: Email security team (DO NOT post publicly)

---

## License

This security module is part of the DonatelloAI Enterprise Image Generation Platform.

**Confidential and Proprietary**

© 2024 DonatelloAI. All rights reserved.
