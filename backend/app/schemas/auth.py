"""
╔════════════════════════════════════════════════════════╗
║          Authentication Pydantic Schemas                ║
║         Request/Response Models for Auth               ║
╚════════════════════════════════════════════════════════╝
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ┌─────────────────────────────────────────────────────────┐
# │ Token Schemas                                           │
# └─────────────────────────────────────────────────────────┘


class TokenResponse(BaseModel):
    """
    OAuth 2.0 token response schema.

    Returned after successful authentication or token refresh.
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token lifetime in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token (httpOnly cookie)")
    scope: Optional[str] = Field(None, description="Token scope")


class TokenRefreshRequest(BaseModel):
    """
    Request schema for token refresh.

    Note: Refresh token typically sent via httpOnly cookie,
    but can also be sent in request body for API clients.
    """

    refresh_token: str = Field(..., description="Refresh token")


# ┌─────────────────────────────────────────────────────────┐
# │ Authentication Request/Response                         │
# └─────────────────────────────────────────────────────────┘


class LoginRequest(BaseModel):
    """
    Login request schema.

    Note: For Azure AD OAuth flow, this is not used.
    Kept for potential future API key authentication.
    """

    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """
    Login response schema.

    Contains tokens and user information.
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifetime in seconds")
    user: dict = Field(..., description="User information")


class LogoutResponse(BaseModel):
    """
    Logout response schema.
    """

    message: str = Field(default="Successfully logged out", description="Success message")


# ┌─────────────────────────────────────────────────────────┐
# │ OAuth 2.0 Callback                                      │
# └─────────────────────────────────────────────────────────┘


class OAuthCallbackRequest(BaseModel):
    """
    OAuth callback request schema.

    Received from Azure AD after user authentication.
    """

    code: str = Field(..., description="Authorization code from Azure AD")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")
    error: Optional[str] = Field(None, description="Error code if authentication failed")
    error_description: Optional[str] = Field(None, description="Error description")


# ┌─────────────────────────────────────────────────────────┐
# │ Session Management                                      │
# └─────────────────────────────────────────────────────────┘


class SessionInfo(BaseModel):
    """
    Current session information.
    """

    session_id: UUID = Field(..., description="Session ID")
    created_at: datetime = Field(..., description="Session creation time")
    expires_at: datetime = Field(..., description="Session expiration time")
    last_used_at: datetime = Field(..., description="Last activity time")
    ip_address: Optional[str] = Field(None, description="IP address")
    device_info: Optional[dict] = Field(None, description="Device information")


class ActiveSessionsResponse(BaseModel):
    """
    List of active sessions for a user.
    """

    sessions: list[SessionInfo] = Field(..., description="Active sessions")
    total: int = Field(..., description="Total number of active sessions")


# ┌─────────────────────────────────────────────────────────┐
# │ MFA Management                                          │
# └─────────────────────────────────────────────────────────┘


class MFAStatusResponse(BaseModel):
    """
    MFA status for current user.
    """

    mfa_enabled: bool = Field(..., description="MFA is enabled")
    mfa_required: bool = Field(..., description="MFA is required (grace period expired)")
    grace_period_expires_at: Optional[datetime] = Field(
        None,
        description="Grace period expiration",
    )
    days_remaining: Optional[int] = Field(None, description="Days until MFA required")


# ⚠️  AUTHENTICATION FLOW SCHEMAS:
#
# 🔐 Azure AD OAuth 2.0 Flow:
# 1. GET /auth/login -> Redirect to Azure AD
# 2. User authenticates at Azure AD
# 3. GET /auth/callback?code=... -> Exchange code for tokens
# 4. Return TokenResponse with access_token
# 5. Client stores access_token (memory) and refresh_token (httpOnly cookie)
# 6. API requests include: Authorization: Bearer <access_token>
# 7. When access_token expires: POST /auth/refresh -> New TokenResponse
# 8. POST /auth/logout -> Revoke session
#
# 🎫 Token Contents:
# Access Token (JWT):
# {
#   "sub": "user@example.com",
#   "user_id": "uuid",
#   "role": "dept_manager",
#   "department_id": "uuid",
#   "exp": 1700000000,
#   "iat": 1699998000
# }
#
# Refresh Token (opaque):
# - Random 32-byte hex string
# - Stored hashed in database
# - One-time use (rotated on refresh)
#
# 📋 ISO 27001 Control Mapping:
# - A.9.4.2: Secure log-on procedures
# - A.9.4.3: Password management system
# - A.14.2.1: Secure development policy
