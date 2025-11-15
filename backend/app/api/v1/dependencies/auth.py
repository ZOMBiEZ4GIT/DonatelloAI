"""
╔════════════════════════════════════════════════════════╗
║         Authentication Dependencies                     ║
║         FastAPI Dependency Injection for Auth          ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Reusable dependencies for protecting endpoints
    - Extracts and validates JWT tokens
    - Loads current user from database
    - Checks role-based permissions

Security Considerations:
    - Token validation on every request
    - Database lookup for current user state
    - MFA enforcement checked
    - Account status verified (is_active)

ISO 27001 Controls:
    - A.9.4.1: Information access restriction
    - A.9.4.2: Secure log-on procedures
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_db
from app.core.security import decode_access_token, extract_bearer_token
from app.core.exceptions import AuthenticationError, AuthorizationError, MFARequiredError
from app.core.logging import logger
from app.models.user import User, UserRole
from app.schemas.user import CurrentUser


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_db),
) -> CurrentUser:
    """
    Get currently authenticated user from JWT token.

    Args:
        authorization: Authorization header (Bearer token)
        db: Database session

    Returns:
        CurrentUser: Current user information

    Raises:
        HTTPException: 401 if token invalid/missing, 403 if MFA required

    Security:
        - Validates JWT signature and expiration
        - Verifies user exists and is active
        - Checks MFA compliance
        - Logs authentication events

    ISO 27001 Control: A.9.4.2 - Secure log-on procedures

    Usage:
        @app.get("/protected")
        async def protected_route(
            current_user: CurrentUser = Depends(get_current_user)
        ):
            return {"user": current_user.email}
    """
    # Extract token from Authorization header
    token = extract_bearer_token(authorization)
    if not token:
        logger.warning("authentication_failed_no_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode and validate JWT
    payload = decode_access_token(token)
    if not payload:
        logger.warning("authentication_failed_invalid_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token
    user_id_str = payload.get("user_id")
    if not user_id_str:
        logger.error("token_missing_user_id", payload=payload)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        logger.error("token_invalid_user_id", user_id=user_id_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )

    # Load user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Check if account is active
    if not user.is_active:
        logger.warning("user_account_inactive", user_id=user_id, email=user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Check MFA compliance
    if user.mfa_required and not user.mfa_enabled:
        logger.warning(
            "mfa_required_not_enabled",
            user_id=user_id,
            email=user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA setup required. Please configure multi-factor authentication.",
        )

    # Return current user
    current_user = CurrentUser(
        id=user.id,
        azure_ad_id=user.azure_ad_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        department_id=user.department_id,
        is_active=user.is_active,
        mfa_enabled=user.mfa_enabled,
    )

    logger.info(
        "user_authenticated",
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )

    return current_user


# ┌─────────────────────────────────────────────────────────┐
# │ Role-Based Authorization Dependencies                   │
# └─────────────────────────────────────────────────────────┘


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access control.

    Args:
        *allowed_roles: Roles allowed to access endpoint

    Returns:
        Dependency function that checks user role

    Raises:
        HTTPException: 403 if user doesn't have required role

    ISO 27001 Control: A.9.4.1 - Information access restriction

    Usage:
        @app.get("/admin/users")
        async def admin_only(
            current_user: CurrentUser = Depends(require_role(UserRole.SUPER_ADMIN))
        ):
            return {"message": "Admin access"}

        @app.get("/department/budget")
        async def dept_manager_or_above(
            current_user: CurrentUser = Depends(
                require_role(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.DEPT_MANAGER)
            )
        ):
            return {"budget": "..."}
    """

    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        """Check if user has required role."""
        if current_user.role not in allowed_roles:
            logger.warning(
                "authorization_failed_insufficient_role",
                user_id=current_user.id,
                user_role=current_user.role.value,
                required_roles=[r.value for r in allowed_roles],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in allowed_roles]}",
            )

        return current_user

    return role_checker


# Convenience dependencies for common role checks
require_super_admin = require_role(UserRole.SUPER_ADMIN)
require_admin = require_role(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)
require_manager = require_role(
    UserRole.SUPER_ADMIN,
    UserRole.ORG_ADMIN,
    UserRole.DEPT_MANAGER,
)


# ┌─────────────────────────────────────────────────────────┐
# │ Optional Authentication                                 │
# └─────────────────────────────────────────────────────────┘


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_db),
) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, otherwise None.

    Useful for endpoints that have different behavior for
    authenticated vs anonymous users.

    Args:
        authorization: Authorization header
        db: Database session

    Returns:
        CurrentUser if authenticated, None otherwise

    Usage:
        @app.get("/public-or-private")
        async def mixed_access(
            current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
        ):
            if current_user:
                return {"message": f"Hello {current_user.email}"}
            else:
                return {"message": "Hello anonymous user"}
    """
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None


# ⚠️  DEPENDENCY USAGE NOTES:
#
# 🔐 Authentication Flow:
# 1. Client sends: Authorization: Bearer <jwt_token>
# 2. Dependency extracts token from header
# 3. JWT decoded and validated (signature, expiration)
# 4. User loaded from database
# 5. Account status and MFA compliance checked
# 6. CurrentUser returned to endpoint
#
# 🛡️ Authorization Patterns:
#
# # Any authenticated user
# @app.get("/profile")
# async def get_profile(user: CurrentUser = Depends(get_current_user)):
#     return user
#
# # Admin only
# @app.get("/admin/users")
# async def admin_route(user: CurrentUser = Depends(require_super_admin)):
#     return {"users": [...]}
#
# # Manager or above
# @app.get("/budgets")
# async def budgets(user: CurrentUser = Depends(require_manager)):
#     return {"budgets": [...]}
#
# # Custom role check
# @app.get("/power-users")
# async def power_users(
#     user: CurrentUser = Depends(require_role(UserRole.POWER_USER))
# ):
#     return {"data": [...]}
#
# 📊 Performance:
# - Database query on every request (cached in connection pool)
# - Consider caching user data in Redis for high traffic
# - JWT validation is fast (cryptographic operation)
# - Typical overhead: ~10-20ms per request
#
# 🚨 Security Checklist:
# ✅ Token signature verified
# ✅ Token expiration checked
# ✅ User exists in database
# ✅ User account is active
# ✅ MFA compliance enforced
# ✅ All events logged for audit
#
# 📋 ISO 27001 Control Mapping:
# - A.9.4.1: Information access restriction
# - A.9.4.2: Secure log-on procedures
# - A.12.4.1: Event logging
# - A.16.1.7: Collection of evidence
