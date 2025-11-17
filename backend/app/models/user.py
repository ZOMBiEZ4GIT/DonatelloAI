"""
User model for authentication and authorization.

Users are authenticated via Azure AD and assigned roles for access control.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from app.db.base import Base


class UserRole(str, Enum):
    """User role enumeration matching frontend types."""

    SUPER_ADMIN = "SUPER_ADMIN"
    ORG_ADMIN = "ORG_ADMIN"
    DEPARTMENT_MANAGER = "DEPARTMENT_MANAGER"
    POWER_USER = "POWER_USER"
    STANDARD_USER = "STANDARD_USER"


class User(Base):
    """
    User model for authentication and access control.

    Attributes:
        id: Unique user identifier
        azure_ad_id: Azure AD object ID (unique)
        email: User email address
        name: User display name
        department_id: Foreign key to department
        role: User role for permissions
        settings: JSON field for user preferences
        created_at: User creation timestamp
        updated_at: Last update timestamp
        last_login_at: Last login timestamp
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    azure_ad_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.STANDARD_USER,
        nullable=False,
        index=True,
    )
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="users",
    )
    generations: Mapped[list["Generation"]] = relationship(
        "Generation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    budget: Mapped[Optional["UserBudget"]] = relationship(
        "UserBudget",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    @property
    def is_manager(self) -> bool:
        """Check if user has manager privileges."""
        return self.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.DEPARTMENT_MANAGER,
        ]

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]
