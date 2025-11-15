"""
╔════════════════════════════════════════════════════════╗
║             Security Utilities & Helpers                ║
║         🔒 Cryptography & Token Management             ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Core security primitives for authentication
    - JWT token creation and validation
    - Password hashing (not used for users, but for refresh tokens)
    - Secure random token generation

Security Considerations:
    - Uses industry-standard algorithms (bcrypt, HS256)
    - Secrets never logged or exposed
    - Timing-attack resistant comparisons
    - Cryptographically secure random generation

ISO 27001 Controls:
    - A.9.4.3: Password management system
    - A.10.1.1: Policy on the use of cryptographic controls
    - A.10.1.2: Key management
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import logger

# ┌─────────────────────────────────────────────────────────┐
# │ Password Hashing Context                                │
# └─────────────────────────────────────────────────────────┘
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def hash_token(token: str) -> str:
    """
    Hash a token using bcrypt.

    Used for storing refresh tokens securely in database.

    Args:
        token: Token to hash

    Returns:
        Hashed token

    Security:
        - Bcrypt with configurable rounds (default: 12)
        - Salt automatically generated
        - Timing-attack resistant
        - Rainbow table resistant

    ISO 27001 Control: A.9.4.3 - Password management system
    """
    return pwd_context.hash(token)


def verify_token(plain_token: str, hashed_token: str) -> bool:
    """
    Verify a token against its hash.

    Args:
        plain_token: Plain text token
        hashed_token: Hashed token from database

    Returns:
        True if token matches hash

    Security:
        - Constant-time comparison
        - Prevents timing attacks
    """
    try:
        return pwd_context.verify(plain_token, hashed_token)
    except Exception as e:
        logger.warning("token_verification_failed", error=str(e))
        return False


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Token length in bytes (default: 32)

    Returns:
        Hex-encoded secure random token

    Security:
        - Uses secrets module (cryptographically secure)
        - Not predictable
        - Suitable for session tokens, API keys, etc.

    Example:
        >>> token = generate_secure_token()
        >>> len(token)
        64  # 32 bytes = 64 hex characters
    """
    return secrets.token_hex(length)


# ┌─────────────────────────────────────────────────────────┐
# │ JWT Token Management                                    │
# └─────────────────────────────────────────────────────────┘


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Claims to encode in token
        expires_delta: Token expiration time (default: from settings)

    Returns:
        Encoded JWT token

    Security:
        - Signed with SECRET_KEY (HS256 algorithm)
        - Includes expiration claim (exp)
        - Includes issued-at claim (iat)
        - Never includes sensitive data

    ISO 27001 Control: A.10.1.2 - Key management

    Example:
        >>> token = create_access_token({"sub": "user@example.com", "role": "admin"})
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "eig-platform",  # Issuer
        "aud": "eig-platform-api",  # Audience
    })

    # Encode JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    logger.info(
        "access_token_created",
        subject=to_encode.get("sub"),
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """
    Create a refresh token.

    Args:
        user_id: User ID to associate with token

    Returns:
        Secure random refresh token

    Security:
        - Cryptographically secure random token
        - Stored hashed in database
        - One-time use (rotated on refresh)
        - Long expiration (7 days default)

    Notes:
        - Refresh tokens are NOT JWTs
        - They are opaque random strings
        - Validated against database only
    """
    return generate_secure_token(32)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token claims if valid, None if invalid

    Security:
        - Verifies signature
        - Checks expiration
        - Validates issuer and audience
        - Returns None on any validation failure

    ISO 27001 Control: A.10.1.2 - Key management
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience="eig-platform-api",
            issuer="eig-platform",
        )
        return payload
    except JWTError as e:
        logger.warning(
            "token_decode_failed",
            error=type(e).__name__,
            message=str(e),
        )
        return None


def verify_jwt_token(token: str) -> bool:
    """
    Verify if a JWT token is valid.

    Args:
        token: JWT token to verify

    Returns:
        True if token is valid

    Security:
        - Checks signature
        - Checks expiration
        - Checks issuer/audience
    """
    return decode_access_token(token) is not None


# ┌─────────────────────────────────────────────────────────┐
# │ Token Extraction Utilities                              │
# └─────────────────────────────────────────────────────────┘


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.

    Args:
        authorization_header: Authorization header value

    Returns:
        Token if present and valid format, None otherwise

    Example:
        >>> extract_bearer_token("Bearer eyJhbG...")
        'eyJhbG...'
        >>> extract_bearer_token("Invalid")
        None
    """
    if not authorization_header:
        return None

    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


# ⚠️  SECURITY BEST PRACTICES:
#
# 🔒 Token Security:
# - Access tokens: Short-lived (30 minutes)
# - Refresh tokens: Longer-lived (7 days) but rotated
# - Tokens stored in httpOnly cookies (not localStorage)
# - CSRF protection for state-changing operations
#
# 🔐 Algorithm Selection:
# - HS256 for symmetric signing (faster)
# - Could upgrade to RS256 for asymmetric (better for distributed systems)
# - Bcrypt for hashing (slow by design, prevents brute force)
#
# 🚨 Common Pitfalls to Avoid:
# - ❌ Never store secrets in tokens (they're just encoded, not encrypted)
# - ❌ Never use predictable token generation (always use secrets module)
# - ❌ Never skip signature verification
# - ❌ Never ignore expiration claims
# - ❌ Never log tokens (even in debug mode)
#
# 💡 Token Rotation:
# - Refresh tokens rotated on every use
# - Old refresh token immediately invalidated
# - Prevents token replay attacks
# - Sliding window approach
#
# 📋 ISO 27001 Control Mapping:
# - A.9.4.3: Password management system (bcrypt hashing)
# - A.10.1.1: Policy on the use of cryptographic controls
# - A.10.1.2: Key management (JWT secret management)
# - A.14.1.3: Protecting application services transactions
