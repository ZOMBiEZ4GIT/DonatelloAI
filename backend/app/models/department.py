"""
Department model for organizing users and managing budgets.

A department represents a business unit or team with its own budget
and settings.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, Numeric, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Department(Base):
    """
    Department model for organizational structure.

    Attributes:
        id: Unique department identifier
        name: Department name (e.g., "Marketing", "Engineering")
        monthly_budget_aud: Allocated monthly budget in AUD
        current_spend_aud: Current month's spend in AUD
        settings: JSON field for department-specific settings
        created_at: Department creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    monthly_budget_aud: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=5000.00,
        nullable=False,
    )
    current_spend_aud: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
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

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="department",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name={self.name}, budget={self.monthly_budget_aud})>"

    @property
    def budget_remaining(self) -> float:
        """Calculate remaining budget for the month."""
        return float(self.monthly_budget_aud) - float(self.current_spend_aud)

    @property
    def budget_utilization_percent(self) -> float:
        """Calculate budget utilization as percentage."""
        if self.monthly_budget_aud == 0:
            return 0.0
        return (float(self.current_spend_aud) / float(self.monthly_budget_aud)) * 100
