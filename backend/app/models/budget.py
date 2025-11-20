"""
╔════════════════════════════════════════════════════════╗
║              Budget Model                               ║
║         Department budget tracking                     ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Monthly budget tracking per department
    - Real-time spend monitoring
    - Budget alerts and enforcement

ISO 27001 Control: A.12.1.3 - Capacity management
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BudgetPeriod(str, Enum):
    """Budget period type."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class BudgetAlertType(str, Enum):
    """Type of budget alert."""

    WARNING = "warning"  # 80% threshold
    CRITICAL = "critical"  # 95% threshold
    EXCEEDED = "exceeded"  # 100% exceeded


class Budget(Base, TimestampMixin):
    """
    Department budget tracking for a specific period.

    Tracks actual spend against allocated budget and generates
    alerts when thresholds are exceeded.
    """

    __tablename__ = "budgets"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Department relationship
    department_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Department this budget belongs to",
    )

    # Period
    period_type: Mapped[BudgetPeriod] = mapped_column(
        SQLEnum(BudgetPeriod),
        nullable=False,
        default=BudgetPeriod.MONTHLY,
        comment="Budget period type",
    )

    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Period start date",
    )

    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Period end date",
    )

    # Budget amounts (AUD)
    allocated_aud: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Allocated budget in AUD",
    )

    spent_aud: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00,
        comment="Amount spent in AUD",
    )

    # Alerts
    alert_threshold_warning: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=80,
        comment="Warning alert threshold percentage",
    )

    alert_threshold_critical: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=95,
        comment="Critical alert threshold percentage",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether this budget period is active",
    )

    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether budget is locked (period ended)",
    )

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="budgets",
    )

    alerts: Mapped[list["BudgetAlert"]] = relationship(
        "BudgetAlert",
        back_populates="budget",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Budget(id={self.id}, department_id={self.department_id}, spent={self.spent_aud}/{self.allocated_aud})>"

    @property
    def remaining_aud(self) -> float:
        """Calculate remaining budget."""
        return float(self.allocated_aud - self.spent_aud)

    @property
    def utilization_percentage(self) -> float:
        """Calculate budget utilization percentage."""
        if self.allocated_aud == 0:
            return 0.0
        return (float(self.spent_aud) / float(self.allocated_aud)) * 100

    @property
    def is_over_budget(self) -> bool:
        """Check if budget is exceeded."""
        return self.spent_aud > self.allocated_aud

    def should_alert(self, alert_type: BudgetAlertType) -> bool:
        """
        Check if an alert should be triggered.

        Args:
            alert_type: Type of alert to check

        Returns:
            True if alert threshold is exceeded
        """
        utilization = self.utilization_percentage

        if alert_type == BudgetAlertType.WARNING:
            return utilization >= self.alert_threshold_warning
        elif alert_type == BudgetAlertType.CRITICAL:
            return utilization >= self.alert_threshold_critical
        elif alert_type == BudgetAlertType.EXCEEDED:
            return self.is_over_budget

        return False


class BudgetAlert(Base, TimestampMixin):
    """
    Budget alert notification.

    Records when budget thresholds are exceeded and tracks
    notification delivery.
    """

    __tablename__ = "budget_alerts"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Budget relationship
    budget_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("budgets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Budget this alert relates to",
    )

    # Alert details
    alert_type: Mapped[BudgetAlertType] = mapped_column(
        SQLEnum(BudgetAlertType),
        nullable=False,
        comment="Type of alert",
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Alert message",
    )

    utilization_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Budget utilization at time of alert",
    )

    # Notification tracking
    notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When notification was sent",
    )

    notification_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Notification method (email, webhook, etc.)",
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When alert was acknowledged",
    )

    acknowledged_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Who acknowledged the alert",
    )

    # Relationships
    budget: Mapped["Budget"] = relationship(
        "Budget",
        back_populates="alerts",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<BudgetAlert(id={self.id}, type={self.alert_type.value}, utilization={self.utilization_percentage}%)>"
