"""
Budget Management Service.

Business logic for managing user budgets and tracking costs.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models import User, UserBudget
from app.schemas.user_budget import (
    UserBudgetCreate,
    UserBudgetUpdate,
    TeamBudgetOverview,
    TeamMemberBudget,
)


class BudgetService:
    """Service for budget management operations."""

    @staticmethod
    async def get_or_create_current_budget(
        db: AsyncSession,
        user_id: str,
    ) -> UserBudget:
        """
        Get or create the current month's budget for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            UserBudget: Current budget record
        """
        now = datetime.utcnow()
        current_year = now.year
        current_month = now.month

        # Try to find existing budget for current month
        result = await db.execute(
            select(UserBudget).where(
                and_(
                    UserBudget.user_id == user_id,
                    UserBudget.budget_period_year == current_year,
                    UserBudget.budget_period_month == current_month,
                    UserBudget.is_active == True,
                )
            )
        )
        budget = result.scalar_one_or_none()

        if not budget:
            # Create default budget (0 means no budget set)
            budget = UserBudget(
                id=str(uuid4()),
                user_id=user_id,
                monthly_budget_aud=0.00,
                current_spend_aud=0.00,
                budget_period_year=current_year,
                budget_period_month=current_month,
                is_active=True,
            )
            db.add(budget)
            await db.commit()
            await db.refresh(budget)

        return budget

    @staticmethod
    async def set_user_budget(
        db: AsyncSession,
        budget_data: UserBudgetCreate,
        set_by_user_id: str,
    ) -> UserBudget:
        """
        Set or update a user's budget for a specific month.

        Args:
            db: Database session
            budget_data: Budget creation data
            set_by_user_id: ID of manager setting the budget

        Returns:
            UserBudget: Created or updated budget
        """
        # Check if budget already exists for this period
        result = await db.execute(
            select(UserBudget).where(
                and_(
                    UserBudget.user_id == budget_data.user_id,
                    UserBudget.budget_period_year == budget_data.budget_period_year,
                    UserBudget.budget_period_month == budget_data.budget_period_month,
                )
            )
        )
        existing_budget = result.scalar_one_or_none()

        if existing_budget:
            # Update existing budget
            existing_budget.monthly_budget_aud = budget_data.monthly_budget_aud
            existing_budget.alert_threshold_percent = budget_data.alert_threshold_percent
            existing_budget.set_by_user_id = set_by_user_id
            existing_budget.is_active = True
            existing_budget.updated_at = datetime.utcnow()
            budget = existing_budget
        else:
            # Create new budget
            budget = UserBudget(
                id=str(uuid4()),
                user_id=budget_data.user_id,
                monthly_budget_aud=budget_data.monthly_budget_aud,
                current_spend_aud=0.00,
                budget_period_year=budget_data.budget_period_year,
                budget_period_month=budget_data.budget_period_month,
                alert_threshold_percent=budget_data.alert_threshold_percent,
                is_active=True,
                set_by_user_id=set_by_user_id,
            )
            db.add(budget)

        await db.commit()
        await db.refresh(budget)
        return budget

    @staticmethod
    async def get_user_budget(
        db: AsyncSession,
        user_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Optional[UserBudget]:
        """
        Get a user's budget for a specific period or current month.

        Args:
            db: Database session
            user_id: User ID
            year: Budget year (defaults to current year)
            month: Budget month (defaults to current month)

        Returns:
            UserBudget or None
        """
        now = datetime.utcnow()
        target_year = year or now.year
        target_month = month or now.month

        result = await db.execute(
            select(UserBudget).where(
                and_(
                    UserBudget.user_id == user_id,
                    UserBudget.budget_period_year == target_year,
                    UserBudget.budget_period_month == target_month,
                    UserBudget.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user_budget(
        db: AsyncSession,
        budget_id: str,
        budget_data: UserBudgetUpdate,
    ) -> Optional[UserBudget]:
        """
        Update an existing budget.

        Args:
            db: Database session
            budget_id: Budget ID to update
            budget_data: Update data

        Returns:
            Updated UserBudget or None if not found
        """
        result = await db.execute(
            select(UserBudget).where(UserBudget.id == budget_id)
        )
        budget = result.scalar_one_or_none()

        if not budget:
            return None

        # Update fields if provided
        if budget_data.monthly_budget_aud is not None:
            budget.monthly_budget_aud = budget_data.monthly_budget_aud
        if budget_data.alert_threshold_percent is not None:
            budget.alert_threshold_percent = budget_data.alert_threshold_percent
        if budget_data.is_active is not None:
            budget.is_active = budget_data.is_active

        budget.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(budget)
        return budget

    @staticmethod
    async def add_cost_to_budget(
        db: AsyncSession,
        user_id: str,
        cost_aud: float,
    ) -> UserBudget:
        """
        Add a cost to the user's current month budget.

        Args:
            db: Database session
            user_id: User ID
            cost_aud: Cost to add in AUD

        Returns:
            Updated UserBudget
        """
        budget = await BudgetService.get_or_create_current_budget(db, user_id)
        budget.current_spend_aud = float(budget.current_spend_aud) + cost_aud
        budget.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(budget)
        return budget

    @staticmethod
    async def get_team_budget_overview(
        db: AsyncSession,
        manager_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> TeamBudgetOverview:
        """
        Get budget overview for all users in the manager's department.

        Args:
            db: Database session
            manager_id: Manager user ID
            year: Budget year (defaults to current year)
            month: Budget month (defaults to current month)

        Returns:
            TeamBudgetOverview with all team members' budget status
        """
        now = datetime.utcnow()
        target_year = year or now.year
        target_month = month or now.month

        # Get manager's department
        manager_result = await db.execute(
            select(User).where(User.id == manager_id)
        )
        manager = manager_result.scalar_one_or_none()

        if not manager or not manager.department_id:
            return TeamBudgetOverview(
                total_team_budget=0.0,
                total_team_spend=0.0,
                total_team_remaining=0.0,
                average_utilization_percent=0.0,
                users_over_budget=0,
                users_near_threshold=0,
                team_members=[],
            )

        # Get all users in the same department
        users_result = await db.execute(
            select(User).where(User.department_id == manager.department_id)
        )
        team_users = users_result.scalars().all()

        team_members = []
        total_budget = 0.0
        total_spend = 0.0
        users_over_budget = 0
        users_near_threshold = 0

        for user in team_users:
            budget = await BudgetService.get_user_budget(
                db, user.id, target_year, target_month
            )

            if budget:
                monthly_budget = float(budget.monthly_budget_aud)
                current_spend = float(budget.current_spend_aud)
                budget_remaining = monthly_budget - current_spend
                utilization = (
                    (current_spend / monthly_budget * 100)
                    if monthly_budget > 0
                    else 0.0
                )

                total_budget += monthly_budget
                total_spend += current_spend

                if current_spend > monthly_budget:
                    users_over_budget += 1
                elif utilization >= budget.alert_threshold_percent:
                    users_near_threshold += 1

                team_members.append(
                    TeamMemberBudget(
                        user_id=user.id,
                        user_name=user.name,
                        user_email=user.email,
                        monthly_budget_aud=monthly_budget,
                        current_spend_aud=current_spend,
                        budget_remaining=budget_remaining,
                        budget_utilization_percent=round(utilization, 2),
                        is_over_budget=current_spend > monthly_budget,
                        should_alert=utilization >= budget.alert_threshold_percent,
                        budget_period_year=target_year,
                        budget_period_month=target_month,
                    )
                )

        avg_utilization = (
            (total_spend / total_budget * 100) if total_budget > 0 else 0.0
        )

        return TeamBudgetOverview(
            total_team_budget=round(total_budget, 2),
            total_team_spend=round(total_spend, 2),
            total_team_remaining=round(total_budget - total_spend, 2),
            average_utilization_percent=round(avg_utilization, 2),
            users_over_budget=users_over_budget,
            users_near_threshold=users_near_threshold,
            team_members=team_members,
        )

    @staticmethod
    async def check_budget_exceeded(
        db: AsyncSession,
        user_id: str,
        additional_cost: float = 0.0,
    ) -> tuple[bool, Optional[UserBudget]]:
        """
        Check if user would exceed budget with an additional cost.

        Args:
            db: Database session
            user_id: User ID
            additional_cost: Additional cost to check

        Returns:
            Tuple of (would_exceed, current_budget)
        """
        budget = await BudgetService.get_or_create_current_budget(db, user_id)

        # If no budget set (budget = 0), allow unlimited
        if budget.monthly_budget_aud == 0:
            return (False, budget)

        projected_spend = float(budget.current_spend_aud) + additional_cost
        would_exceed = projected_spend > float(budget.monthly_budget_aud)

        return (would_exceed, budget)
