"""
╔════════════════════════════════════════════════════════╗
║              Department Database Model                  ║
║         Cost Center & Budget Management                ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Organizational unit for budget allocation
    - Groups users for cost tracking and reporting
    - Enforces spending limits per department
    - Tracks monthly budget vs actual spend

Security Considerations:
    - Budget data considered financially sensitive
    - Access restricted to department managers and above
    - All budget changes audited
    - Soft delete preserves financial history

ISO 27001 Controls:
    - A.8.1.1: Inventory of assets
    - A.12.1.3: Capacity management
"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Column, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Department(Base):
    """
    Department model for organizational structure and budget management.

    Business Rules:
        - Each department has a monthly budget in AUD
        - Current spend tracked in real-time
        - Budget enforcement: hard (block), soft (warn), warn (notify only)
        - Monthly budgets reset on 1st of month
        - Historical spend preserved for reporting

    Cost Management:
        - Budget alerts at 80%, 90%, 100%
        - Overage handling based on enforcement mode
        - Cost allocation per user tracked
        - Chargeback reports generated monthly

    ISO 27001 Control: A.8.1.1 - Inventory of assets
    """

    __tablename__ = "departments"

    # ┌─────────────────────────────────────────────────────────┐
    # │ Primary Identity                                         │
    # └─────────────────────────────────────────────────────────┘
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Department ID"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Department Information                                  │
    # └─────────────────────────────────────────────────────────┘
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Department name (e.g., 'Marketing', 'Engineering')"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Department description"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Budget Management (💰 COST CRITICAL)                    │
    # └─────────────────────────────────────────────────────────┘
    monthly_budget_aud = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("5000.00"),
        comment="Monthly budget in AUD"
    )

    current_spend_aud = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Current month spend in AUD"
    )

    budget_reset_day = Column(
        String(10),
        nullable=False,
        default="01",
        comment="Day of month to reset budget (01-31)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Timestamps                                              │
    # └─────────────────────────────────────────────────────────┘
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Department creation timestamp (UTC)"
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp (UTC)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Department Settings & Preferences                       │
    # └─────────────────────────────────────────────────────────┘
    settings = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Department settings (JSON)"
    )
    # Example settings:
    # {
    #   "budget_enforcement": "hard",  # hard | soft | warn
    #   "default_model": "azure-openai",
    #   "allowed_models": ["azure-openai", "replicate-sdxl"],
    #   "cost_alert_emails": ["manager@company.com.au"],
    #   "require_approval_over_aud": 100.00
    # }

    # ┌─────────────────────────────────────────────────────────┐
    # │ Relationships                                           │
    # └─────────────────────────────────────────────────────────┘
    # users = relationship("User", back_populates="department")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Department(id={self.id}, name={self.name})>"

    @property
    def budget_remaining_aud(self) -> Decimal:
        """Calculate remaining budget."""
        return self.monthly_budget_aud - self.current_spend_aud

    @property
    def budget_utilization_percent(self) -> float:
        """Calculate budget utilization percentage."""
        if self.monthly_budget_aud == 0:
            return 0.0
        return float((self.current_spend_aud / self.monthly_budget_aud) * 100)

    @property
    def is_over_budget(self) -> bool:
        """Check if department is over budget."""
        return self.current_spend_aud > self.monthly_budget_aud

    @property
    def budget_status(self) -> str:
        """Get budget status string."""
        util = self.budget_utilization_percent
        if util >= 100:
            return "exceeded"
        elif util >= 90:
            return "critical"
        elif util >= 80:
            return "warning"
        else:
            return "healthy"


# ⚠️  COST MANAGEMENT NOTES:
#
# 💰 Budget Enforcement:
# - hard: Block all requests when budget exceeded
# - soft: Allow with approval workflow
# - warn: Notify but don't block
#
# 📊 Budget Tracking:
# - Real-time spend updates after each generation
# - Monthly reset on configured day
# - Historical data preserved in audit logs
#
# 🚨 Budget Alerts:
# - 80%: Warning email to department manager
# - 90%: Critical alert to manager + org admin
# - 100%: Block (hard) or require approval (soft)
#
# 📋 Cost Allocation:
# - Per-user spend tracked in separate table
# - Chargeback reports generated monthly
# - Cost by model, by project, by time period
#
# 📋 ISO 27001 Control Mapping:
# - A.8.1.1: Inventory of assets
# - A.12.1.3: Capacity management
# - A.12.6.1: Management of technical vulnerabilities
