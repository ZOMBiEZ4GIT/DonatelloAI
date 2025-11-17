# Prompt Security - Quick Reference

## 🔒 What's Protected?

### Critical (Auto-Block)
- ✅ AWS/GCP/Azure API Keys
- ✅ GitHub/GitLab Tokens
- ✅ Private Keys (RSA, SSH)
- ✅ Database Credentials
- ✅ Passwords
- ✅ JWT Tokens

### High Risk (Auto-Block)
- ✅ Credit Card Numbers
- ✅ Social Security Numbers
- ✅ Bank Account Numbers
- ✅ Medicare/Tax Numbers
- ✅ IBAN Numbers

### Medium Risk (Warning)
- ⚠️ Email Addresses
- ⚠️ Phone Numbers
- ⚠️ IP Addresses

### Security Threats (Auto-Block)
- 🛡️ Script Injection (XSS)
- 🛡️ Command Injection
- 🛡️ Prompt Injection
- 🛡️ Path Traversal

## 📝 Configuration Quick Start

```bash
# .env file
ENABLE_PII_DETECTION=true
PII_ACTION=block                    # block | warn | anonymize
PII_DETECTION_THRESHOLD=0.7

ENABLE_CONTENT_FILTERING=true
BLOCK_PROMPT_INJECTION=true
BLOCK_COMMAND_INJECTION=true
```

## 💻 Code Examples

### Backend - Simple

```python
from app.services.security import validate_prompt

try:
    result = validate_prompt("Generate a sunset")
    # Proceed with valid prompt
except PIIDetectedError:
    return {"error": "Sensitive data detected"}
except ContentViolationError:
    return {"error": "Security violation"}
```

### Backend - Advanced

```python
from app.services.security import get_prompt_validator

validator = get_prompt_validator()
result = validator.validate(
    prompt=user_input,
    max_length=2000,
    strict_mode=True
)

if result.is_valid:
    # Safe to process
    process(user_input)
else:
    # Log and reject
    logger.warning(f"Blocked: {result.issues}")
    return {"error": result.issues[0].message}
```

### Frontend

```typescript
import { validatePrompt } from '@/utils/validators';

const result = validatePrompt(userInput);

if (!result.valid) {
  showError(result.error);
  return;
}

if (result.warnings) {
  result.warnings.forEach(w => showWarning(w));
}
```

## 🔍 Detected PII Types (20+)

| Type | Pattern Example | Severity |
|------|----------------|----------|
| AWS Key | `AKIA...` | CRITICAL |
| GitHub Token | `ghp_...` | CRITICAL |
| Private Key | `-----BEGIN...` | CRITICAL |
| Credit Card | `4532-0151-1283-0366` | HIGH |
| SSN | `123-45-6789` | HIGH |
| Medicare | `2123 45678 9` | HIGH |
| Email | `user@example.com` | MEDIUM |
| Phone | `0412 345 678` | MEDIUM |

## 🚨 Common Responses

### PII Detected
```json
{
  "error": "pii_detected",
  "message": "Prompt contains sensitive information: Credit Card Number",
  "pii_types": ["credit_card"],
  "anonymized": "Generate for card [CREDIT_CARD_REDACTED]"
}
```

### Content Violation
```json
{
  "error": "content_violation",
  "message": "Security violation detected: Prompt injection attempt",
  "violations": ["prompt_injection"],
  "risk_score": 0.9
}
```

### Validation Success
```json
{
  "is_valid": true,
  "action": "allow",
  "issues": [],
  "safe_for_logging": true
}
```

## 🎯 Best Practices

### ✅ DO
- Validate all user input on backend
- Use anonymized prompts in logs
- Review security logs regularly
- Update patterns quarterly
- Test with PII samples

### ❌ DON'T
- Log raw user prompts with PII
- Trust frontend validation alone
- Hardcode sensitive patterns
- Ignore false positives
- Disable security in production

## 📊 Monitoring

### Key Metrics to Track
```python
# Audit metadata
{
  "pii_detected": bool,
  "pii_types": List[str],
  "content_violations": int,
  "risk_score": float,
  "validation_action": str,
  "prompt_length": int
}
```

### Alert Thresholds
- **Critical**: PII detected (immediate alert)
- **High**: Risk score ≥ 0.75 (daily review)
- **Medium**: Risk score ≥ 0.40 (weekly review)

## 🧪 Testing

### Run Tests
```bash
pytest backend/tests/test_security.py -v
```

### Test Cases
```python
# PII detection
assert detect_pii("SSN: 123-45-6789").contains_pii

# Content filtering
assert not filter_content("<script>alert(1)</script>").is_safe

# Validation
with pytest.raises(PIIDetectedError):
    validate_prompt("Card: 4532015112830366")
```

## 🔧 Troubleshooting

### False Positive
```bash
# Increase threshold
PII_DETECTION_THRESHOLD=0.85

# Or switch to warn mode
PII_ACTION=warn
```

### Performance Issues
```python
# Cache results
from functools import lru_cache

@lru_cache(maxsize=1000)
def validate_cached(prompt):
    return validate_prompt(prompt)
```

## 📚 Full Documentation

See `/docs/PROMPT_SECURITY.md` for complete documentation.

## 🆘 Support

- **Security Issues**: Email security team (DO NOT post publicly)
- **Bug Reports**: GitHub Issues
- **Questions**: Check documentation first
