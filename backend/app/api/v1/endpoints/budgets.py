"""
Budget Management API endpoints.

Endpoints for managers to set user budgets and for users to track their spending.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models import User
from app.schemas.user_budget import (
    UserBudgetCreate,
    UserBudgetUpdate,
    UserBudgetResponse,
    UserBudgetWithUser,
    TeamBudgetOverview,
)
from app.services.budget_service import BudgetService

# Note: Authentication dependencies would be added here
# For now, using placeholder dependency
async def get_current_user() -> User:
    """Placeholder for authentication dependency."""
    # TODO: Implement actual authentication
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not implemented yet",
    )


router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post(
    "/users/{user_id}",
    response_model=UserBudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set user budget",
    description="Set or update a user's monthly budget (managers only)",
)
async def set_user_budget(
    user_id: str,
    budget_data: UserBudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set or update a user's monthly budget.

    **Permissions**: Department managers can set budgets for users in their department.
    Org admins and super admins can set budgets for any user.

    Args:
        user_id: Target user ID
        budget_data: Budget data (amount, period, alert threshold)
        db: Database session
        current_user: Authenticated user (must be manager)

    Returns:
        UserBudgetResponse: Created or updated budget

    Raises:
        403: If user is not a manager
        404: If target user not found
    """
    # Check if current user is a manager
    if not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can set user budgets",
        )

    # Override user_id in budget_data to match path parameter
    budget_data.user_id = user_id

    # Set the budget
    budget = await BudgetService.set_user_budget(
        db=db,
        budget_data=budget_data,
        set_by_user_id=current_user.id,
    )

    return budget


@router.get(
    "/me",
    response_model=UserBudgetResponse,
    summary="Get my budget",
    description="Get current user's budget for current month",
)
async def get_my_budget(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current user's budget.

    Args:
        year: Budget year (optional, defaults to current year)
        month: Budget month (optional, defaults to current month)
        db: Database session
        current_user: Authenticated user

    Returns:
        UserBudgetResponse: User's budget information
    """
    budget = await BudgetService.get_user_budget(
        db=db,
        user_id=current_user.id,
        year=year,
        month=month,
    )

    if not budget:
        # Create default budget if none exists
        budget = await BudgetService.get_or_create_current_budget(
            db=db,
            user_id=current_user.id,
        )

    return budget


@router.get(
    "/users/{user_id}",
    response_model=UserBudgetResponse,
    summary="Get user budget",
    description="Get a specific user's budget (managers only)",
)
async def get_user_budget(
    user_id: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a user's budget (managers only).

    Args:
        user_id: Target user ID
        year: Budget year (optional)
        month: Budget month (optional)
        db: Database session
        current_user: Authenticated user (must be manager)

    Returns:
        UserBudgetResponse: User's budget information

    Raises:
        403: If current user is not a manager
        404: If budget not found
    """
    # Check permissions
    if not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can view other users' budgets",
        )

    budget = await BudgetService.get_user_budget(
        db=db,
        user_id=user_id,
        year=year,
        month=month,
    )

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found for this user and period",
        )

    return budget


@router.patch(
    "/{budget_id}",
    response_model=UserBudgetResponse,
    summary="Update budget",
    description="Update an existing budget (managers only)",
)
async def update_budget(
    budget_id: str,
    budget_data: UserBudgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing budget.

    Args:
        budget_id: Budget ID to update
        budget_data: Update data
        db: Database session
        current_user: Authenticated user (must be manager)

    Returns:
        UserBudgetResponse: Updated budget

    Raises:
        403: If user is not a manager
        404: If budget not found
    """
    if not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can update budgets",
        )

    budget = await BudgetService.update_user_budget(
        db=db,
        budget_id=budget_id,
        budget_data=budget_data,
    )

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        )

    return budget


@router.get(
    "/team/overview",
    response_model=TeamBudgetOverview,
    summary="Get team budget overview",
    description="Get budget overview for all team members (managers only)",
)
async def get_team_budget_overview(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get budget overview for all users in manager's department.

    Args:
        year: Budget year (optional, defaults to current year)
        month: Budget month (optional, defaults to current month)
        db: Database session
        current_user: Authenticated user (must be manager)

    Returns:
        TeamBudgetOverview: Team budget statistics and individual budgets

    Raises:
        403: If user is not a manager
    """
    if not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can view team budget overview",
        )

    overview = await BudgetService.get_team_budget_overview(
        db=db,
        manager_id=current_user.id,
        year=year,
        month=month,
    )

    return overview
