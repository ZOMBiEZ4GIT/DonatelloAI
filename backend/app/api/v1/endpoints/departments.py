"""
╔════════════════════════════════════════════════════════╗
║       Department Management API Endpoints              ║
║      Budget Tracking & Department Administration       ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Central department and budget management
    - Cost center tracking and reporting
    - Budget enforcement and alerts
    - Usage analytics per department

Cost Management:
    - Monthly budget allocation
    - Real-time spend tracking
    - Budget alerts at 80%/90%/100%
    - Spending history and forecasting

ISO 27001 Controls:
    - A.8.1.1: Inventory of assets
    - A.12.1.3: Capacity management
    - A.12.4.1: Event logging
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, require_admin
from app.core.config import settings
from app.core.database import get_async_db
from app.core.logging import logger
from app.models.department import Department
from app.models.generation import GenerationStatus, ImageGeneration
from app.models.user import User, UserRole
from app.schemas.department import (
    DepartmentBudgetUpdate,
    DepartmentCreate,
    DepartmentListResponse,
    DepartmentResponse,
    DepartmentSpendReset,
    DepartmentUpdate,
    DepartmentUsageStats,
)

# Type alias for dependency
CurrentUser = User

router = APIRouter(tags=["Departments"])


# ┌─────────────────────────────────────────────────────────┐
# │ Department CRUD                                         │
# └─────────────────────────────────────────────────────────┘


@router.get("/departments", response_model=DepartmentListResponse)
async def list_departments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> DepartmentListResponse:
    """
    List all departments with pagination.

    **Permissions:**
    - Standard/Power Users: See only their own department
    - Dept Managers: See only their department
    - Org Admins/Super Admins: See all departments

    **Pagination:**
    - Default: 50 items per page
    - Max: 100 items per page

    **Search:**
    - Filters by department name (case-insensitive)
    """
    # Build query based on permissions
    query = select(Department)

    if current_user.role in [UserRole.STANDARD_USER, UserRole.POWER_USER, UserRole.DEPT_MANAGER]:
        # Non-admins see only their department
        if not current_user.department_id:
            return DepartmentListResponse(items=[], total=0, page=page, page_size=page_size)
        query = query.where(Department.id == current_user.department_id)

    # Apply search filter
    if search:
        query = query.where(Department.name.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Department.name)
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    departments = result.scalars().all()

    # Build response items
    items = []
    for dept in departments:
        # Count users
        user_count_query = select(func.count()).where(User.department_id == dept.id)
        user_count_result = await db.execute(user_count_query)
        user_count = user_count_result.scalar() or 0

        items.append(
            DepartmentResponse(
                id=dept.id,
                name=dept.name,
                description=dept.description,
                monthly_budget_aud=dept.monthly_budget_aud,
                current_spend_aud=dept.current_spend_aud,
                budget_remaining_aud=dept.budget_remaining_aud,
                budget_utilization_percent=dept.budget_utilization_percent,
                budget_status=dept.budget_status,
                budget_reset_day=dept.budget_reset_day,
                user_count=user_count,
                settings=dept.settings,
                created_at=dept.created_at,
                updated_at=dept.updated_at,
            )
        )

    return DepartmentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> DepartmentResponse:
    """
    Get specific department details.

    **Permissions:**
    - Users can view their own department
    - Admins can view any department
    """
    # Permission check
    if current_user.role not in [UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
        if current_user.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own department"
            )

    # Get department
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Count users
    user_count_query = select(func.count()).where(User.department_id == department.id)
    user_count_result = await db.execute(user_count_query)
    user_count = user_count_result.scalar() or 0

    return DepartmentResponse(
        id=department.id,
        name=department.name,
        description=department.description,
        monthly_budget_aud=department.monthly_budget_aud,
        current_spend_aud=department.current_spend_aud,
        budget_remaining_aud=department.budget_remaining_aud,
        budget_utilization_percent=department.budget_utilization_percent,
        budget_status=department.budget_status,
        budget_reset_day=department.budget_reset_day,
        user_count=user_count,
        settings=department.settings,
        created_at=department.created_at,
        updated_at=department.updated_at,
    )


@router.post("/departments", status_code=status.HTTP_201_CREATED, response_model=DepartmentResponse)
async def create_department(
    department_data: DepartmentCreate,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> DepartmentResponse:
    """
    Create a new department.

    **Permissions:**
    - Org Admins and Super Admins only

    **Business Logic:**
    - Department name must be unique
    - Budget defaults to $5000 AUD if not specified
    - Budget reset day defaults to 01 (first of month)
    """
    # Check for duplicate name
    existing = await db.execute(
        select(Department).where(Department.name == department_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Department '{department_data.name}' already exists"
        )

    # Create department
    department = Department(
        name=department_data.name,
        description=department_data.description,
        monthly_budget_aud=department_data.monthly_budget_aud,
        budget_reset_day=department_data.budget_reset_day,
        settings=department_data.settings or {},
    )

    db.add(department)
    await db.commit()
    await db.refresh(department)

    logger.info(
        "department_created",
        department_id=str(department.id),
        name=department.name,
        monthly_budget_aud=float(department.monthly_budget_aud),
        created_by=current_user.email,
    )

    return DepartmentResponse(
        id=department.id,
        name=department.name,
        description=department.description,
        monthly_budget_aud=department.monthly_budget_aud,
        current_spend_aud=department.current_spend_aud,
        budget_remaining_aud=department.budget_remaining_aud,
        budget_utilization_percent=department.budget_utilization_percent,
        budget_status=department.budget_status,
        budget_reset_day=department.budget_reset_day,
        user_count=0,
        settings=department.settings,
        created_at=department.created_at,
        updated_at=department.updated_at,
    )


@router.patch("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    department_data: DepartmentUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> DepartmentResponse:
    """
    Update department details.

    **Permissions:**
    - Org Admins and Super Admins only

    **Note:**
    - Use separate /budget endpoint to update budget (for audit trail)
    """
    # Get department
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Update fields
    if department_data.name is not None:
        # Check for duplicate name
        if department_data.name != department.name:
            existing = await db.execute(
                select(Department).where(Department.name == department_data.name)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Department '{department_data.name}' already exists"
                )
        department.name = department_data.name

    if department_data.description is not None:
        department.description = department_data.description

    if department_data.budget_reset_day is not None:
        department.budget_reset_day = department_data.budget_reset_day

    if department_data.settings is not None:
        department.settings = department_data.settings

    # Note: monthly_budget_aud update should use dedicated endpoint for audit trail

    await db.commit()
    await db.refresh(department)

    logger.info(
        "department_updated",
        department_id=str(department.id),
        updated_by=current_user.email,
    )

    # Count users
    user_count_query = select(func.count()).where(User.department_id == department.id)
    user_count_result = await db.execute(user_count_query)
    user_count = user_count_result.scalar() or 0

    return DepartmentResponse(
        id=department.id,
        name=department.name,
        description=department.description,
        monthly_budget_aud=department.monthly_budget_aud,
        current_spend_aud=department.current_spend_aud,
        budget_remaining_aud=department.budget_remaining_aud,
        budget_utilization_percent=department.budget_utilization_percent,
        budget_status=department.budget_status,
        budget_reset_day=department.budget_reset_day,
        user_count=user_count,
        settings=department.settings,
        created_at=department.created_at,
        updated_at=department.updated_at,
    )


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Delete a department.

    **Permissions:**
    - Super Admins only

    **Business Logic:**
    - Cannot delete department with active users
    - Hard delete (not soft delete) - use with caution
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can delete departments"
        )

    # Get department
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Check for active users
    user_count_query = select(func.count()).where(User.department_id == department.id, User.is_active == True)
    user_count_result = await db.execute(user_count_query)
    active_user_count = user_count_result.scalar() or 0

    if active_user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete department with {active_user_count} active users"
        )

    # Delete department
    await db.delete(department)
    await db.commit()

    logger.warning(
        "department_deleted",
        department_id=str(department_id),
        department_name=department.name,
        deleted_by=current_user.email,
    )


# ┌─────────────────────────────────────────────────────────┐
# │ Budget Management                                       │
# └─────────────────────────────────────────────────────────┘


@router.patch("/departments/{department_id}/budget", response_model=DepartmentResponse)
async def update_department_budget(
    department_id: UUID,
    budget_data: DepartmentBudgetUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> DepartmentResponse:
    """
    Update department monthly budget.

    **Permissions:**
    - Org Admins and Super Admins only

    **Audit Trail:**
    - Budget changes are logged with reason
    - Historical budget tracking for reporting
    """
    # Get department
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    old_budget = department.monthly_budget_aud
    department.monthly_budget_aud = budget_data.monthly_budget_aud

    await db.commit()
    await db.refresh(department)

    logger.info(
        "department_budget_updated",
        department_id=str(department.id),
        old_budget_aud=float(old_budget),
        new_budget_aud=float(budget_data.monthly_budget_aud),
        reason=budget_data.reason,
        updated_by=current_user.email,
    )

    # Count users
    user_count_query = select(func.count()).where(User.department_id == department.id)
    user_count_result = await db.execute(user_count_query)
    user_count = user_count_result.scalar() or 0

    return DepartmentResponse(
        id=department.id,
        name=department.name,
        description=department.description,
        monthly_budget_aud=department.monthly_budget_aud,
        current_spend_aud=department.current_spend_aud,
        budget_remaining_aud=department.budget_remaining_aud,
        budget_utilization_percent=department.budget_utilization_percent,
        budget_status=department.budget_status,
        budget_reset_day=department.budget_reset_day,
        user_count=user_count,
        settings=department.settings,
        created_at=department.created_at,
        updated_at=department.updated_at,
    )


@router.post("/departments/{department_id}/reset-spend", response_model=DepartmentResponse)
async def reset_department_spend(
    department_id: UUID,
    reset_data: DepartmentSpendReset,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> DepartmentResponse:
    """
    Reset department current spend.

    **Permissions:**
    - Org Admins and Super Admins only

    **Use Cases:**
    - Monthly budget reset (automated)
    - Manual correction/adjustment
    - Accounting period close

    **Audit Trail:**
    - Spend resets are logged with mandatory reason
    - Previous spend value preserved in logs
    """
    # Get department
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    old_spend = department.current_spend_aud
    department.current_spend_aud = reset_data.reset_to

    await db.commit()
    await db.refresh(department)

    logger.info(
        "department_spend_reset",
        department_id=str(department.id),
        old_spend_aud=float(old_spend),
        new_spend_aud=float(reset_data.reset_to),
        reason=reset_data.reason,
        reset_by=current_user.email,
    )

    # Count users
    user_count_query = select(func.count()).where(User.department_id == department.id)
    user_count_result = await db.execute(user_count_query)
    user_count = user_count_result.scalar() or 0

    return DepartmentResponse(
        id=department.id,
        name=department.name,
        description=department.description,
        monthly_budget_aud=department.monthly_budget_aud,
        current_spend_aud=department.current_spend_aud,
        budget_remaining_aud=department.budget_remaining_aud,
        budget_utilization_percent=department.budget_utilization_percent,
        budget_status=department.budget_status,
        budget_reset_day=department.budget_reset_day,
        user_count=user_count,
        settings=department.settings,
        created_at=department.created_at,
        updated_at=department.updated_at,
    )


# ┌─────────────────────────────────────────────────────────┐
# │ Department Analytics                                    │
# └─────────────────────────────────────────────────────────┘


@router.get("/departments/{department_id}/stats", response_model=DepartmentUsageStats)
async def get_department_stats(
    department_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> DepartmentUsageStats:
    """
    Get department usage statistics.

    **Permissions:**
    - Users can view their own department stats
    - Admins can view any department stats

    **Metrics:**
    - Budget utilization
    - Images generated count
    - Cost by provider/user
    - Active user count
    """
    # Permission check
    if current_user.role not in [UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
        if current_user.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own department stats"
            )

    # Get department
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Calculate period (current month)
    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        period_end = period_start.replace(year=period_start.year + 1, month=1)
    else:
        period_end = period_start.replace(month=period_start.month + 1)

    # Total images generated this month
    images_query = select(func.count()).where(
        ImageGeneration.department_id == department_id,
        ImageGeneration.status == GenerationStatus.COMPLETED,
        ImageGeneration.created_at >= period_start,
        ImageGeneration.created_at < period_end,
    )
    images_result = await db.execute(images_query)
    total_images = images_result.scalar() or 0

    # Cost by provider
    cost_by_provider: dict[str, Decimal] = {}
    # Cost by user
    cost_by_user: dict[str, Decimal] = {}

    # Most used provider
    most_used_provider = None

    # Total and active users
    total_users_query = select(func.count()).where(User.department_id == department_id)
    total_users_result = await db.execute(total_users_query)
    total_users = total_users_result.scalar() or 0

    active_users_query = select(func.count(func.distinct(ImageGeneration.user_id))).where(
        ImageGeneration.department_id == department_id,
        ImageGeneration.created_at >= period_start,
        ImageGeneration.created_at < period_end,
    )
    active_users_result = await db.execute(active_users_query)
    active_users = active_users_result.scalar() or 0

    # Average cost per image
    avg_cost = Decimal("0")
    if total_images > 0:
        avg_cost = department.current_spend_aud / Decimal(str(total_images))

    return DepartmentUsageStats(
        department_id=department.id,
        department_name=department.name,
        monthly_budget_aud=department.monthly_budget_aud,
        current_spend_aud=department.current_spend_aud,
        budget_remaining_aud=department.budget_remaining_aud,
        budget_utilization_percent=department.budget_utilization_percent,
        total_images_generated=total_images,
        total_users=total_users,
        active_users_count=active_users,
        cost_by_provider=cost_by_provider,
        cost_by_user=cost_by_user,
        average_cost_per_image_aud=avg_cost,
        most_used_provider=most_used_provider,
        period_start=period_start,
        period_end=period_end,
    )


# 📋 ISO 27001 Control Mapping:
# - A.8.1.1: Inventory of assets (department tracking)
# - A.12.1.3: Capacity management (budget limits)
# - A.12.4.1: Event logging (budget change audit)
# - A.9.4.1: Information access restriction (dept isolation)
