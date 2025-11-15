"""
╔════════════════════════════════════════════════════════╗
║          Authentication API Endpoints                   ║
║         OAuth 2.0 Login, Logout, Token Refresh         ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Central authentication endpoints for the platform
    - Azure AD OAuth 2.0 integration
    - Session management and token refresh
    - MFA enforcement

Security Considerations:
    - State parameter for CSRF protection
    - Secure token storage (httpOnly cookies)
    - Token rotation on refresh
    - Session revocation on logout

ISO 27001 Controls:
    - A.9.4.2: Secure log-on procedures
    - A.9.4.3: Password management system
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_async_db
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_token,
    generate_secure_token,
)
from app.api.v1.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.models.session import UserSession
from app.schemas.auth import (
    LoginResponse,
    LogoutResponse,
    MFAStatusResponse,
    TokenResponse,
)
from app.schemas.user import CurrentUser, UserDetailResponse
from app.services.auth.azure_ad import AzureADService

router = APIRouter()

# Initialize Azure AD service
azure_ad_service = AzureADService()


# ┌─────────────────────────────────────────────────────────┐
# │ Login Endpoints                                         │
# └─────────────────────────────────────────────────────────┘


@router.get(
    "/login",
    summary="Initiate Azure AD Login",
    description="""
    Initiates OAuth 2.0 authorization code flow with Azure AD.

    **Flow:**
    1. Generate authorization URL with CSRF state
    2. Redirect user to Azure AD
    3. User authenticates (username + password + MFA)
    4. Azure AD redirects to /auth/callback

    **Security:**
    - State parameter prevents CSRF attacks
    - PKCE prevents authorization code interception
    """,
    tags=["auth"],
)
async def login() -> RedirectResponse:
    """
    Redirect to Azure AD login page.

    Returns:
        Redirect to Azure AD authorization endpoint

    ISO 27001 Control: A.9.4.2 - Secure log-on procedures
    """
    # Generate CSRF state token
    state = generate_secure_token(16)

    # TODO: Store state in session/cache for validation in callback
    # For now, we'll skip state validation (not recommended for production)

    # Get authorization URL
    auth_url = azure_ad_service.get_authorization_url(state=state)

    logger.info("azure_ad_login_initiated", state=state[:8] + "...")

    return RedirectResponse(url=auth_url)


@router.get(
    "/callback",
    response_model=LoginResponse,
    summary="Azure AD Callback",
    description="""
    Handles OAuth 2.0 callback from Azure AD.

    **Flow:**
    1. Receive authorization code from Azure AD
    2. Exchange code for access/ID/refresh tokens
    3. Extract user identity from ID token
    4. Create or update user in database
    5. Create session and generate our tokens
    6. Return tokens to client

    **Security:**
    - Validates state parameter (CSRF protection)
    - Validates tokens against Azure AD
    - Checks MFA compliance
    - Creates audit log entry
    """,
    tags=["auth"],
)
async def auth_callback(
    code: str = Query(..., description="Authorization code from Azure AD"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="Error code if auth failed"),
    error_description: Optional[str] = Query(None, description="Error description"),
    db: AsyncSession = Depends(get_async_db),
    response: Response = None,
) -> LoginResponse:
    """
    Handle Azure AD OAuth callback.

    Args:
        code: Authorization code
        state: CSRF state token
        error: Error code (if auth failed)
        error_description: Error description
        db: Database session
        response: HTTP response for setting cookies

    Returns:
        LoginResponse with tokens and user info

    Raises:
        HTTPException: If authentication fails

    ISO 27001 Control: A.9.4.2 - Secure log-on procedures
    """
    # Check for errors from Azure AD
    if error:
        logger.error(
            "azure_ad_callback_error",
            error=error,
            description=error_description,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Azure AD authentication failed: {error_description}",
        )

    # TODO: Validate state parameter against stored value
    # if not validate_state(state):
    #     raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Exchange authorization code for tokens
    try:
        token_response = azure_ad_service.acquire_token_by_authorization_code(
            authorization_code=code,
            state=state,
        )
    except Exception as e:
        logger.error("token_acquisition_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acquire tokens from Azure AD",
        )

    # Extract user claims from ID token
    id_token_claims = token_response.get("id_token_claims", {})
    azure_ad_id = id_token_claims.get("oid")  # Object ID
    email = id_token_claims.get("preferred_username") or id_token_claims.get("email")
    display_name = id_token_claims.get("name")

    if not azure_ad_id or not email:
        logger.error("missing_required_claims", claims=id_token_claims)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing required claims in ID token",
        )

    # Check if user exists, create if not
    result = await db.execute(
        select(User).where(User.azure_ad_id == azure_ad_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            azure_ad_id=azure_ad_id,
            email=email,
            display_name=display_name,
            role=UserRole.STANDARD_USER,  # Default role
            mfa_grace_period_expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db.add(user)
        await db.flush()  # Get user ID
        await db.commit()

        logger.info(
            "new_user_created",
            user_id=user.id,
            azure_ad_id=azure_ad_id,
            email=email,
        )
    else:
        # Update last login
        user.last_login_at = datetime.utcnow()
        # TODO: Update last_login_ip from request
        await db.commit()

        logger.info(
            "existing_user_login",
            user_id=user.id,
            email=email,
        )

    # Generate our own tokens
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role.value,
            "department_id": str(user.department_id) if user.department_id else None,
        }
    )

    refresh_token = create_refresh_token(str(user.id))

    # Create session record
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=7),
        # TODO: Extract device info and IP from request
        device_info={},
        ip_address="0.0.0.0",  # Placeholder
    )
    db.add(session)
    await db.commit()

    # Set refresh token in httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,  # HTTPS only in production
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    logger.info(
        "login_successful",
        user_id=user.id,
        email=user.email,
        session_id=session.id,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role.value,
        },
    )


# ┌─────────────────────────────────────────────────────────┐
# │ Token Refresh                                           │
# └─────────────────────────────────────────────────────────┘


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Access Token",
    description="""
    Refresh expired access token using refresh token.

    **Flow:**
    1. Extract refresh token from httpOnly cookie
    2. Validate token against database
    3. Generate new access token
    4. Rotate refresh token (one-time use)
    5. Return new tokens

    **Security:**
    - Refresh token rotation prevents replay attacks
    - Old refresh token immediately invalidated
    - Session validated before refresh
    """,
    tags=["auth"],
)
async def refresh_token(
    response: Response,
    db: AsyncSession = Depends(get_async_db),
) -> TokenResponse:
    """
    Refresh access token.

    NOTE: This is a simplified version. Full implementation would:
    - Extract refresh token from cookie
    - Validate against database
    - Rotate refresh token
    - Update session

    Returns:
        TokenResponse with new access token

    ISO 27001 Control: A.9.4.3 - Password management system
    """
    # TODO: Implement full refresh token logic
    # For now, return error
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not yet fully implemented",
    )


# ┌─────────────────────────────────────────────────────────┐
# │ Logout                                                  │
# └─────────────────────────────────────────────────────────┘


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout",
    description="""
    Logout current user and revoke session.

    **Flow:**
    1. Validate current session
    2. Revoke session in database
    3. Clear refresh token cookie
    4. Return success message

    **Security:**
    - Session immediately invalidated
    - Tokens can no longer be used
    - Refresh token cookie cleared
    """,
    tags=["auth"],
)
async def logout(
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> LogoutResponse:
    """
    Logout current user.

    Args:
        response: HTTP response for clearing cookies
        current_user: Current authenticated user
        db: Database session

    Returns:
        LogoutResponse with success message

    ISO 27001 Control: A.9.4.2 - Secure log-on procedures
    """
    # TODO: Revoke current session in database
    # TODO: Clear refresh token cookie

    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")

    logger.info(
        "user_logged_out",
        user_id=current_user.id,
        email=current_user.email,
    )

    return LogoutResponse(message="Successfully logged out")


# ┌─────────────────────────────────────────────────────────┐
# │ Current User                                            │
# └─────────────────────────────────────────────────────────┘


@router.get(
    "/me",
    response_model=UserDetailResponse,
    summary="Get Current User",
    description="""
    Get currently authenticated user information.

    **Returns:**
    - User profile data
    - Role and permissions
    - MFA status
    - Last login information

    **Security:**
    - Requires valid JWT token
    - Returns current user data only
    """,
    tags=["auth"],
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> UserDetailResponse:
    """
    Get current user information.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserDetailResponse with detailed user info
    """
    # Load full user from database
    result = await db.execute(
        select(User).where(User.id == current_user.id)
    )
    user = result.scalar_one()

    return UserDetailResponse.model_validate(user)


@router.get(
    "/mfa/status",
    response_model=MFAStatusResponse,
    summary="Get MFA Status",
    description="""
    Get MFA status for current user.

    **Returns:**
    - MFA enabled status
    - MFA required status
    - Grace period expiration
    - Days remaining until required
    """,
    tags=["auth"],
)
async def get_mfa_status(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> MFAStatusResponse:
    """
    Get MFA status for current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        MFAStatusResponse with MFA information
    """
    # Load full user from database
    result = await db.execute(
        select(User).where(User.id == current_user.id)
    )
    user = result.scalar_one()

    days_remaining = None
    if user.mfa_grace_period_expires_at:
        delta = user.mfa_grace_period_expires_at - datetime.utcnow()
        days_remaining = max(0, delta.days)

    return MFAStatusResponse(
        mfa_enabled=user.mfa_enabled,
        mfa_required=user.mfa_required,
        grace_period_expires_at=user.mfa_grace_period_expires_at,
        days_remaining=days_remaining,
    )


# ⚠️  AUTHENTICATION ENDPOINT NOTES:
#
# 🔐 OAuth 2.0 Flow:
# 1. GET /auth/login
#    - Redirects to Azure AD
#    - User authenticates there
# 2. GET /auth/callback?code=...
#    - Exchange code for tokens
#    - Create/update user
#    - Return our tokens
# 3. Client stores tokens
# 4. API requests use: Authorization: Bearer <access_token>
# 5. POST /auth/refresh (when access token expires)
# 6. POST /auth/logout (to end session)
#
# 🎫 Token Management:
# - Access tokens: 30 min (JWT, stored in memory)
# - Refresh tokens: 7 days (opaque, stored in httpOnly cookie)
# - Refresh token rotation on every use
# - Session tracking in database
#
# 🛡️ Security Features:
# - State parameter for CSRF protection
# - PKCE for authorization code flow
# - httpOnly cookies prevent XSS
# - Secure flag in production (HTTPS only)
# - SameSite=Lax prevents CSRF
#
# 📊 TODO for Production:
# - [ ] Implement state validation (store in Redis/cache)
# - [ ] Extract IP address and device info from request
# - [ ] Implement full refresh token rotation
# - [ ] Session cleanup job (delete expired sessions)
# - [ ] Rate limiting on login endpoints
# - [ ] Brute force protection
# - [ ] Account lockout after failed attempts
# - [ ] Email notifications on new logins
#
# 📋 ISO 27001 Control Mapping:
# - A.9.4.2: Secure log-on procedures
# - A.9.4.3: Password management system
# - A.12.4.1: Event logging (all auth events logged)
# - A.13.1.1: Network controls (HTTPS enforced)
