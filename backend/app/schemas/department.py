"""
╔════════════════════════════════════════════════════════╗
║        Department Pydantic Schemas                     ║
║     Request/Response Models for Departments            ║
╚════════════════════════════════════════════════════════╝
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ┌─────────────────────────────────────────────────────────┐
# │ Department Request Schemas                              │
# └─────────────────────────────────────────────────────────┘


class DepartmentCreate(BaseModel):
    """
    Request to create a new department.

    Validation:
        - Name must be 2-255 characters
        - Name must be unique
        - Monthly budget must be positive
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Department name",
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Department description",
    )
    monthly_budget_aud: Decimal = Field(
        default=Decimal("5000.00"),
        ge=0,
        description="Monthly budget in AUD",
    )
    budget_reset_day: str = Field(
        default="01",
        description="Day of month to reset budget (01-31)",
    )
    settings: dict = Field(
        default_factory=dict,
        description="Department settings",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate department name."""
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Department name must be at least 2 characters")
        return v

    @field_validator("budget_reset_day")
    @classmethod
    def validate_budget_reset_day(cls, v: str) -> str:
        """Validate budget reset day."""
        try:
            day = int(v)
            if day < 1 or day > 31:
                raise ValueError("Budget reset day must be between 01 and 31")
            return f"{day:02d}"
        except ValueError:
            raise ValueError("Budget reset day must be a valid day number (01-31)")


class DepartmentUpdate(BaseModel):
    """
    Request to update an existing department.

    All fields optional - only provided fields will be updated.
    """

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    monthly_budget_aud: Optional[Decimal] = Field(None, ge=0)
    budget_reset_day: Optional[str] = None
    settings: Optional[dict] = None

    @field_validator("budget_reset_day")
    @classmethod
    def validate_budget_reset_day(cls, v: Optional[str]) -> Optional[str]:
        """Validate budget reset day if provided."""
        if v is None:
            return v
        try:
            day = int(v)
            if day < 1 or day > 31:
                raise ValueError("Budget reset day must be between 01 and 31")
            return f"{day:02d}"
        except ValueError:
            raise ValueError("Budget reset day must be a valid day number (01-31)")


# ┌─────────────────────────────────────────────────────────┐
# │ Department Response Schemas                             │
# └─────────────────────────────────────────────────────────┘


class DepartmentResponse(BaseModel):
    """
    Department information response.
    """

    id: UUID = Field(..., description="Department ID")
    name: str = Field(..., description="Department name")
    description: Optional[str] = Field(None, description="Department description")
    monthly_budget_aud: Decimal = Field(..., description="Monthly budget in AUD")
    current_spend_aud: Decimal = Field(..., description="Current month spend in AUD")
    budget_remaining_aud: Decimal = Field(..., description="Remaining budget in AUD")
    budget_utilization_percent: float = Field(..., description="Budget utilization %")
    budget_status: str = Field(..., description="Budget status: healthy/warning/critical/exceeded")
    budget_reset_day: str = Field(..., description="Budget reset day")
    user_count: int = Field(default=0, description="Number of users")
    settings: dict = Field(..., description="Department settings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DepartmentListResponse(BaseModel):
    """
    Paginated list of departments.
    """

    items: list[DepartmentResponse] = Field(..., description="Department items")
    total: int = Field(..., description="Total departments")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")


class DepartmentBudgetUpdate(BaseModel):
    """
    Request to update department budget.

    Separate endpoint for budget updates to track changes properly.
    """

    monthly_budget_aud: Decimal = Field(
        ...,
        ge=0,
        description="New monthly budget in AUD",
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for budget change (audit trail)",
    )


class DepartmentSpendReset(BaseModel):
    """
    Request to manually reset department spend.

    Use case: Month-end processing, corrections, adjustments.
    """

    reset_to: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Reset current spend to this value (usually 0.00)",
    )
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for spend reset (required for audit)",
    )


# ┌─────────────────────────────────────────────────────────┐
# │ Department Analytics                                    │
# └─────────────────────────────────────────────────────────┘


class DepartmentUsageStats(BaseModel):
    """
    Department usage statistics.
    """

    department_id: UUID = Field(..., description="Department ID")
    department_name: str = Field(..., description="Department name")

    # Budget metrics
    monthly_budget_aud: Decimal = Field(..., description="Monthly budget")
    current_spend_aud: Decimal = Field(..., description="Current spend")
    budget_remaining_aud: Decimal = Field(..., description="Remaining budget")
    budget_utilization_percent: float = Field(..., description="Budget utilization %")

    # Usage metrics
    total_images_generated: int = Field(..., description="Total images this month")
    total_users: int = Field(..., description="Total users in department")
    active_users_count: int = Field(..., description="Active users this month")

    # Cost breakdown
    cost_by_provider: dict[str, Decimal] = Field(..., description="Spend by provider")
    cost_by_user: dict[str, Decimal] = Field(..., description="Spend by user")

    # Performance
    average_cost_per_image_aud: Decimal = Field(..., description="Avg cost per image")
    most_used_provider: Optional[str] = Field(None, description="Most used provider")

    # Time period
    period_start: datetime = Field(..., description="Stats period start")
    period_end: datetime = Field(..., description="Stats period end")


class DepartmentBudgetHistory(BaseModel):
    """
    Historical budget change record.
    """

    changed_at: datetime = Field(..., description="Change timestamp")
    changed_by: str = Field(..., description="User email who made change")
    old_budget_aud: Decimal = Field(..., description="Previous budget")
    new_budget_aud: Decimal = Field(..., description="New budget")
    reason: Optional[str] = Field(None, description="Change reason")


class DepartmentBudgetAlert(BaseModel):
    """
    Budget alert notification.
    """

    department_id: UUID = Field(..., description="Department ID")
    department_name: str = Field(..., description="Department name")
    alert_type: str = Field(..., description="Alert type: warning/critical/exceeded")
    current_spend_aud: Decimal = Field(..., description="Current spend")
    monthly_budget_aud: Decimal = Field(..., description="Monthly budget")
    utilization_percent: float = Field(..., description="Budget utilization %")
    message: str = Field(..., description="Alert message")
    created_at: datetime = Field(..., description="Alert timestamp")


# ┌─────────────────────────────────────────────────────────┐
# │ Budget Enforcement Settings                             │
# └─────────────────────────────────────────────────────────┘


class BudgetEnforcementSettings(BaseModel):
    """
    Budget enforcement configuration.

    Stored in department.settings JSONB field.
    """

    budget_enforcement: str = Field(
        default="hard",
        description="Enforcement mode: hard/soft/warn",
    )
    default_model: Optional[str] = Field(
        None,
        description="Default model provider",
    )
    allowed_models: list[str] = Field(
        default_factory=lambda: ["azure_openai_dalle3", "replicate_sdxl"],
        description="Allowed model providers",
    )
    cost_alert_emails: list[str] = Field(
        default_factory=list,
        description="Email addresses for cost alerts",
    )
    require_approval_over_aud: Optional[Decimal] = Field(
        None,
        description="Require approval for generations over this cost",
    )
    auto_stop_at_percent: int = Field(
        default=100,
        ge=80,
        le=150,
        description="Auto-stop at this budget % (hard mode only)",
    )

    @field_validator("budget_enforcement")
    @classmethod
    def validate_enforcement(cls, v: str) -> str:
        """Validate enforcement mode."""
        if v not in ["hard", "soft", "warn"]:
            raise ValueError("budget_enforcement must be: hard, soft, or warn")
        return v


# 📋 ISO 27001 Control Mapping:
# - A.8.1.1: Inventory of assets (department tracking)
# - A.12.1.3: Capacity management (budget limits)
# - A.12.4.1: Event logging (budget change audit)
# - A.9.4.1: Information access restriction (dept isolation)
