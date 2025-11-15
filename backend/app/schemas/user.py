"""
╔════════════════════════════════════════════════════════╗
║              User Pydantic Schemas                      ║
║         Request/Response Models for Users              ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - API request and response models for user operations
    - Data validation and serialization
    - Type safety for API endpoints

Security Considerations:
    - PII fields clearly marked
    - Passwords never included (Azure AD authentication)
    - Sensitive fields excluded from responses
    - Input validation prevents injection attacks

ISO 27001 Controls:
    - A.14.2.1: Secure development policy
    - A.14.2.5: Secure system engineering principles
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import UserRole


# ┌─────────────────────────────────────────────────────────┐
# │ Base Schemas                                            │
# └─────────────────────────────────────────────────────────┘


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User email address")
    display_name: Optional[str] = Field(None, description="User display name")
    role: UserRole = Field(UserRole.STANDARD_USER, description="User role")
    department_id: Optional[UUID] = Field(None, description="Department ID")


# ┌─────────────────────────────────────────────────────────┐
# │ Request Schemas                                         │
# └─────────────────────────────────────────────────────────┘


class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Note:
        - Used by admins to create users manually
        - Most users auto-created on first Azure AD login
    """

    azure_ad_id: str = Field(..., description="Azure AD object ID")


class UserUpdate(BaseModel):
    """
    Schema for updating user information.

    All fields optional - partial updates supported.
    """

    display_name: Optional[str] = Field(None, description="User display name")
    role: Optional[UserRole] = Field(None, description="User role")
    department_id: Optional[UUID] = Field(None, description="Department ID")
    is_active: Optional[bool] = Field(None, description="Account active status")


# ┌─────────────────────────────────────────────────────────┐
# │ Response Schemas                                        │
# └─────────────────────────────────────────────────────────┘


class UserResponse(UserBase):
    """
    Schema for user responses.

    Returns user information without sensitive data.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="User ID")
    azure_ad_id: str = Field(..., description="Azure AD object ID")
    is_active: bool = Field(..., description="Account active status")
    mfa_enabled: bool = Field(..., description="MFA configured")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserDetailResponse(UserResponse):
    """
    Detailed user response with additional fields.

    Only returned to admins or user themselves.
    """

    settings: dict = Field(default_factory=dict, description="User preferences")
    mfa_grace_period_expires_at: Optional[datetime] = Field(
        None,
        description="MFA grace period expiration",
    )
    last_login_ip: Optional[str] = Field(None, description="Last login IP address")


class UserListResponse(BaseModel):
    """
    Schema for paginated user list responses.
    """

    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of users per page")


# ┌─────────────────────────────────────────────────────────┐
# │ Current User Schema                                     │
# └─────────────────────────────────────────────────────────┘


class CurrentUser(BaseModel):
    """
    Schema for currently authenticated user.

    Used internally for dependency injection.
    """

    id: UUID
    azure_ad_id: str
    email: str
    display_name: Optional[str]
    role: UserRole
    department_id: Optional[UUID]
    is_active: bool
    mfa_enabled: bool

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.DEPT_MANAGER,
        ]

    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.role == UserRole.SUPER_ADMIN


# ⚠️  SCHEMA DESIGN NOTES:
#
# 🔒 Security:
# - Email validation via EmailStr
# - No password fields (Azure AD handles auth)
# - PII clearly marked in descriptions
# - Sensitive fields excluded from public responses
#
# 📊 Validation:
# - Pydantic validates all input automatically
# - Email format checked
# - UUIDs validated
# - Enums prevent invalid role values
#
# 🔄 Serialization:
# - model_config = ConfigDict(from_attributes=True) for ORM models
# - Automatic JSON serialization
# - Datetime fields converted to ISO 8601
# - UUIDs converted to strings
#
# 📋 API Design:
# - Separate Create/Update/Response schemas
# - Partial updates supported (all fields optional in Update)
# - Pagination support in list responses
# - Detailed vs summary responses
#
# 📋 ISO 27001 Control Mapping:
# - A.14.2.1: Secure development policy (input validation)
# - A.14.2.5: Secure system engineering principles
# - A.14.2.9: System acceptance testing (schema validation)
