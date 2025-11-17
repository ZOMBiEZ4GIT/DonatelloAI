"""
User Budget API schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserBudgetBase(BaseModel):
    """Base schema for user budget."""

    monthly_budget_aud: float = Field(..., gt=0, description="Monthly budget in AUD")
    alert_threshold_percent: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Alert threshold percentage",
    )


class UserBudgetCreate(UserBudgetBase):
    """Schema for creating a user budget."""

    user_id: str = Field(..., description="User ID to set budget for")
    budget_period_year: int = Field(..., ge=2020, le=2100, description="Budget year")
    budget_period_month: int = Field(..., ge=1, le=12, description="Budget month (1-12)")


class UserBudgetUpdate(BaseModel):
    """Schema for updating a user budget."""

    monthly_budget_aud: Optional[float] = Field(None, gt=0, description="Monthly budget in AUD")
    alert_threshold_percent: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Alert threshold percentage",
    )
    is_active: Optional[bool] = Field(None, description="Whether budget is active")


class UserBudgetResponse(UserBudgetBase):
    """Schema for user budget response."""

    id: str
    user_id: str
    current_spend_aud: float
    budget_period_year: int
    budget_period_month: int
    is_active: bool
    set_by_user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    budget_remaining: float
    budget_utilization_percent: float
    is_over_budget: bool
    should_alert: bool

    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    """Schema for user information in budget responses."""

    id: str
    email: str
    name: Optional[str]
    role: str


class UserBudgetWithUser(UserBudgetResponse):
    """Schema for user budget with user information."""

    user: UserInfo


class TeamMemberBudget(BaseModel):
    """Schema for team member budget summary."""

    user_id: str
    user_name: Optional[str]
    user_email: str
    monthly_budget_aud: float
    current_spend_aud: float
    budget_remaining: float
    budget_utilization_percent: float
    is_over_budget: bool
    should_alert: bool
    budget_period_year: int
    budget_period_month: int


class TeamBudgetOverview(BaseModel):
    """Schema for team budget overview (for managers)."""

    total_team_budget: float
    total_team_spend: float
    total_team_remaining: float
    average_utilization_percent: float
    users_over_budget: int
    users_near_threshold: int
    team_members: list[TeamMemberBudget]
