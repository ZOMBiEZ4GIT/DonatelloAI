"""
User Budget model for tracking individual user spending limits.

Managers can set monthly budgets for their team members to control costs.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class UserBudget(Base):
    """
    User Budget model for individual cost tracking.

    This table tracks monthly budgets set by managers for individual users.
    Budgets reset monthly and track cumulative spending.

    Attributes:
        id: Unique budget record identifier
        user_id: Foreign key to user
        monthly_budget_aud: Allocated monthly budget in AUD
        current_spend_aud: Current month's spend in AUD
        budget_period_year: Year of the budget period
        budget_period_month: Month of the budget period (1-12)
        alert_threshold_percent: Alert when spending reaches this % (default 80)
        is_active: Whether this budget is active
        set_by_user_id: ID of the manager who set this budget
        created_at: Budget creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "user_budgets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    monthly_budget_aud: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    current_spend_aud: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
    )
    budget_period_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    budget_period_month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    alert_threshold_percent: Mapped[int] = mapped_column(
        Integer,
        default=80,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    set_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
    )
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
    user: Mapped["User"] = relationship(
        "User",
        back_populates="budget",
    )

    def __repr__(self) -> str:
        return (
            f"<UserBudget(id={self.id}, user_id={self.user_id}, "
            f"budget={self.monthly_budget_aud}, spend={self.current_spend_aud})>"
        )

    @property
    def budget_remaining(self) -> float:
        """Calculate remaining budget for the period."""
        return float(self.monthly_budget_aud) - float(self.current_spend_aud)

    @property
    def budget_utilization_percent(self) -> float:
        """Calculate budget utilization as percentage."""
        if self.monthly_budget_aud == 0:
            return 0.0
        return (float(self.current_spend_aud) / float(self.monthly_budget_aud)) * 100

    @property
    def is_over_budget(self) -> bool:
        """Check if user is over budget."""
        return self.current_spend_aud > self.monthly_budget_aud

    @property
    def should_alert(self) -> bool:
        """Check if budget utilization exceeds alert threshold."""
        return self.budget_utilization_percent >= self.alert_threshold_percent
