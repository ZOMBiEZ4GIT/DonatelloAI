"""
╔════════════════════════════════════════════════════════╗
║           User Management Admin Endpoints               ║
║         CRUD Operations for User Administration        ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Admin endpoints for user lifecycle management
    - Role assignment and department allocation
    - User activation/deactivation
    - Bulk user operations

Security Considerations:
    - Admin-only access (RBAC enforced)
    - Audit logging for all user changes
    - Cannot self-deactivate
    - Cannot modify super admin roles (except by super admin)

ISO 27001 Controls:
    - A.9.2.1: User registration and de-registration
    - A.9.2.2: User access provisioning
    - A.9.2.5: Review of user access rights
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_async_db
from app.core.logging import logger
from app.api.v1.dependencies.auth import require_admin, require_super_admin
from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserDetailResponse,
    UserListResponse,
    CurrentUser,
)

router = APIRouter()


# ┌─────────────────────────────────────────────────────────┐
# │ List Users                                              │
# └─────────────────────────────────────────────────────────┘


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List Users",
    description="""
    List all users with pagination.

    **Access**: Admin or above

    **Query Parameters**:
    - page: Page number (default: 1)
    - page_size: Users per page (default: 50, max: 100)
    - role: Filter by role
    - department_id: Filter by department
    - is_active: Filter by active status
    - search: Search by email or name
    """,
    tags=["users"],
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Users per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> UserListResponse:
    """
    List users with filtering and pagination.

    ISO 27001 Control: A.9.2.5 - Review of user access rights
    """
    # Build query
    query = select(User)

    # Apply filters
    if role:
        query = query.where(User.role == role)

    if department_id:
        query = query.where(User.department_id == department_id)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) |
            (User.display_name.ilike(search_pattern))
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Order by created_at descending
    query = query.order_by(User.created_at.desc())

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    logger.info(
        "users_listed",
        total=total,
        page=page,
        page_size=page_size,
        filters={
            "role": role.value if role else None,
            "department_id": str(department_id) if department_id else None,
            "is_active": is_active,
            "search": search,
        },
    )

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


# ┌─────────────────────────────────────────────────────────┐
# │ Get Single User                                         │
# └─────────────────────────────────────────────────────────┘


@router.get(
    "/users/{user_id}",
    response_model=UserDetailResponse,
    summary="Get User",
    description="""
    Get detailed information about a specific user.

    **Access**: Admin or above
    """,
    tags=["users"],
)
async def get_user(
    user_id: UUID,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> UserDetailResponse:
    """Get user by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    return UserDetailResponse.model_validate(user)


# ┌─────────────────────────────────────────────────────────┐
# │ Create User                                             │
# └─────────────────────────────────────────────────────────┘


@router.post(
    "/users",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="""
    Create a new user manually.

    **Access**: Admin or above

    **Note**: Most users are auto-created on first Azure AD login.
    This endpoint is for manual provisioning.
    """,
    tags=["users"],
)
async def create_user(
    user_data: UserCreate,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> UserDetailResponse:
    """
    Create a new user.

    ISO 27001 Control: A.9.2.1 - User registration
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(
            (User.email == user_data.email) |
            (User.azure_ad_id == user_data.azure_ad_id)
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or Azure AD ID already exists",
        )

    # Verify department exists if provided
    if user_data.department_id:
        result = await db.execute(
            select(Department).where(Department.id == user_data.department_id)
        )
        department = result.scalar_one_or_none()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department {user_data.department_id} not found",
            )

    # Create user
    new_user = User(
        azure_ad_id=user_data.azure_ad_id,
        email=user_data.email,
        display_name=user_data.display_name,
        role=user_data.role,
        department_id=user_data.department_id,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(
        "user_created",
        user_id=new_user.id,
        email=new_user.email,
        role=new_user.role.value,
        created_by=current_user.id,
    )

    return UserDetailResponse.model_validate(new_user)


# ┌─────────────────────────────────────────────────────────┐
# │ Update User                                             │
# └─────────────────────────────────────────────────────────┘


@router.patch(
    "/users/{user_id}",
    response_model=UserDetailResponse,
    summary="Update User",
    description="""
    Update user information.

    **Access**: Admin or above

    **Restrictions**:
    - Cannot deactivate yourself
    - Only super admin can modify other super admins
    """,
    tags=["users"],
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> UserDetailResponse:
    """
    Update user information.

    ISO 27001 Control: A.9.2.2 - User access provisioning
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Security checks
    if user.id == current_user.id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    if user.role == UserRole.SUPER_ADMIN and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can modify other super admins",
        )

    # Verify department exists if being changed
    if user_data.department_id and user_data.department_id != user.department_id:
        result = await db.execute(
            select(Department).where(Department.id == user_data.department_id)
        )
        department = result.scalar_one_or_none()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department {user_data.department_id} not found",
            )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    logger.info(
        "user_updated",
        user_id=user.id,
        updated_fields=list(update_data.keys()),
        updated_by=current_user.id,
    )

    return UserDetailResponse.model_validate(user)


# ┌─────────────────────────────────────────────────────────┐
# │ Delete User (Soft Delete)                               │
# └─────────────────────────────────────────────────────────┘


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate User",
    description="""
    Deactivate a user (soft delete).

    **Access**: Admin or above

    **Note**: This performs a soft delete. User data is retained for audit.
    """,
    tags=["users"],
)
async def delete_user(
    user_id: UUID,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Deactivate user (soft delete).

    ISO 27001 Control: A.9.2.6 - Removal of access rights
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Cannot delete yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    # Only super admin can delete other super admins
    if user.role == UserRole.SUPER_ADMIN and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can deactivate other super admins",
        )

    # Soft delete
    user.is_active = False
    from datetime import datetime
    user.deactivated_at = datetime.utcnow()

    await db.commit()

    logger.info(
        "user_deactivated",
        user_id=user.id,
        email=user.email,
        deactivated_by=current_user.id,
    )


# ⚠️  USER MANAGEMENT NOTES:
#
# 🔒 Security:
# - All endpoints require admin access
# - Cannot self-deactivate
# - Super admin protected from non-super-admin modifications
# - Department existence validated before assignment
#
# 📊 Audit Trail:
# - All user changes logged
# - Created_by and updated_by tracked
# - Soft delete preserves history
# - Email and role changes audited
#
# 🚦 Access Control:
# - List/Get: Admin or above
# - Create: Admin or above
# - Update: Admin or above (super admin for super admin users)
# - Delete: Admin or above (super admin for super admin users)
#
# 📋 ISO 27001 Control Mapping:
# - A.9.2.1: User registration and de-registration
# - A.9.2.2: User access provisioning
# - A.9.2.5: Review of user access rights
# - A.9.2.6: Removal or adjustment of access rights
# - A.12.4.1: Event logging (all operations logged)
