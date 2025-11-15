"""
╔════════════════════════════════════════════════════════╗
║                 User Database Model                     ║
║         ISO 27001 A.9.2.1 - User Registration          ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Central user identity management
    - Links to Azure AD for authentication
    - Tracks department membership and role assignment
    - MFA status and compliance

Security Considerations:
    - No passwords stored (delegated to Azure AD)
    - PII stored encrypted at rest (Azure SQL TDE)
    - Audit trail for all user changes
    - Soft delete for compliance

ISO 27001 Controls:
    - A.9.2.1: User registration and de-registration
    - A.9.2.2: User access provisioning
    - A.9.2.3: Management of privileged access rights
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserRole(str, Enum):
    """
    User role enumeration.

    Hierarchy (highest to lowest privilege):
    1. SUPER_ADMIN: Platform-wide administration
    2. ORG_ADMIN: Organization-level administration
    3. DEPT_MANAGER: Department management and budgets
    4. POWER_USER: Unlimited generation within budget
    5. STANDARD_USER: Rate-limited generation

    ISO 27001 Control: A.9.2.3 - Management of privileged access rights
    """
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    DEPT_MANAGER = "dept_manager"
    POWER_USER = "power_user"
    STANDARD_USER = "standard_user"


class User(Base):
    """
    User model representing platform users.

    Each user corresponds to an Azure AD identity and is assigned
    to a department with a specific role.

    Business Rules:
        - Email must be unique across platform
        - Azure AD ID must be unique (1:1 mapping)
        - Department assignment required (except super admins)
        - MFA required after grace period expires
        - Role determines access permissions

    Security:
        - No password storage (Azure AD handles authentication)
        - PII encrypted at rest (Azure SQL TDE)
        - Audit log for all user modifications
        - Soft delete preserves audit trail

    ISO 27001 Control: A.9.2.1 - User registration
    """

    __tablename__ = "users"

    # ┌─────────────────────────────────────────────────────────┐
    # │ Primary Identity                                         │
    # └─────────────────────────────────────────────────────────┘
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Internal user ID"
    )

    azure_ad_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Azure AD object ID (oid claim from JWT)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ User Information (PII - Encrypted at Rest)              │
    # └─────────────────────────────────────────────────────────┘
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address"
    )

    display_name = Column(
        String(255),
        nullable=True,
        comment="User's display name"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Organization & Access Control                           │
    # └─────────────────────────────────────────────────────────┘
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Department membership (NULL for super admins)"
    )

    role = Column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        index=True,
        default=UserRole.STANDARD_USER,
        comment="User role determining permissions"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Account Status                                          │
    # └─────────────────────────────────────────────────────────┘
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Account active status (soft delete)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ MFA Compliance (ISO 27001 A.9.4.2)                      │
    # └─────────────────────────────────────────────────────────┘
    mfa_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="MFA configured in Azure AD"
    )

    mfa_grace_period_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="MFA grace period expiration (7 days from creation)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Activity Tracking                                       │
    # └─────────────────────────────────────────────────────────┘
    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp"
    )

    last_login_ip = Column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="IP address of last login"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Timestamps (ISO 27001 A.12.4.4)                         │
    # └─────────────────────────────────────────────────────────┘
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Account creation timestamp (UTC)"
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp (UTC)"
    )

    deactivated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account deactivation timestamp (soft delete)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ User Preferences & Settings                             │
    # └─────────────────────────────────────────────────────────┘
    settings = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="User preferences (JSON)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Relationships                                           │
    # └─────────────────────────────────────────────────────────┘
    # department = relationship("Department", back_populates="users")
    # sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    # generations = relationship("Generation", back_populates="user")

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.DEPT_MANAGER
        ]

    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.role == UserRole.SUPER_ADMIN

    @property
    def mfa_required(self) -> bool:
        """
        Check if MFA is required for this user.

        Returns:
            True if MFA grace period has expired or never set
        """
        if self.mfa_enabled:
            return False  # Already enabled

        if self.mfa_grace_period_expires_at is None:
            return True  # No grace period set, require immediately

        return datetime.utcnow() > self.mfa_grace_period_expires_at

    @property
    def can_generate_images(self) -> bool:
        """Check if user can generate images."""
        return self.is_active and (not self.mfa_required or self.mfa_enabled)


# ⚠️  SECURITY NOTES:
#
# 🔒 Authentication:
# - NO passwords stored in database (Azure AD handles auth)
# - Azure AD object ID is the authoritative identity
# - JWT tokens validated against Azure AD public keys
#
# 🛡️ Authorization:
# - Role-based access control (RBAC)
# - Permissions checked on every request
# - Principle of least privilege enforced
#
# 🔐 MFA Enforcement:
# - 7-day grace period for new users
# - Required for all roles after grace period
# - Enforced at API gateway level
#
# 📊 Audit Trail:
# - All user changes logged to Cosmos DB
# - Created/updated timestamps tracked
# - Soft delete preserves history
#
# 💾 Data Protection:
# - PII encrypted at rest (Azure SQL TDE)
# - PII encrypted in transit (TLS 1.3)
# - Email and display name considered PII
#
# 📋 ISO 27001 Control Mapping:
# - A.9.2.1: User registration and de-registration
# - A.9.2.2: User access provisioning
# - A.9.2.3: Management of privileged access rights
# - A.9.2.4: Management of secret authentication information
# - A.9.4.2: Secure log-on procedures
# - A.12.4.4: Clock synchronisation (UTC timestamps)
