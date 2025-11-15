"""
╔════════════════════════════════════════════════════════╗
║         Image Generation API Endpoints                 ║
║      Single & Batch Generation with Cost Tracking      ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Core feature: AI image generation
    - Multi-provider routing for cost optimization
    - Department budget enforcement
    - Usage tracking and analytics

Cost Management:
    - Real-time cost estimation
    - Budget validation before generation
    - Per-image cost tracking
    - Department spend updates

ISO 27001 Controls:
    - A.9.4.1: Information access restriction
    - A.12.4.1: Event logging
    - A.14.2.1: Secure development policy
"""

import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.core.config import settings
from app.core.database import get_async_db
from app.core.logging import logger
from app.models.department import Department
from app.models.generation import BatchGenerationJob, GenerationStatus, ImageGeneration
from app.models.user import User, UserRole
from app.schemas.generation import (
    BatchGenerateRequest,
    BatchGenerateResponse,
    CostEstimateRequest,
    CostEstimateResponse,
    GeneratedImage,
    GenerateImageRequest,
    GenerateImageResponse,
    GenerationHistoryResponse,
    GenerationStatsResponse,
    ProviderCostEstimate,
)
from app.services.models.base import GenerationRequest, ImageQuality, ImageSize, ModelProvider
from app.services.models.router import get_model_router

# Type alias for dependency
CurrentUser = User

router = APIRouter(tags=["Image Generation"])


# ┌─────────────────────────────────────────────────────────┐
# │ Single Image Generation                                 │
# └─────────────────────────────────────────────────────────┘


@router.post("/generate", response_model=GenerateImageResponse)
async def generate_image(
    request_data: GenerateImageRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> GenerateImageResponse:
    """
    Generate images using AI models.

    **Business Logic:**
    - Routes to optimal model based on cost/quality
    - Validates department budget before generation
    - Tracks costs and updates budget in real-time
    - Stores generation history for audit

    **Cost Management:**
    - Estimates cost before generation
    - Checks department budget limits
    - Enforces max cost per image safety limit
    - Updates department spend immediately

    **Permissions:**
    - All active users with valid MFA
    - Department budget must have available funds
    - User must have generation permissions

    **Rate Limits:**
    - Standard User: 10 requests/hour
    - Power User: 500 requests/hour
    - Org Admin: 1000 requests/hour

    **ISO 27001:** A.9.4.1 - Information access restriction
    """
    # Check if user can generate
    if not current_user.can_generate_images:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA required to generate images"
        )

    # Get department for budget checking
    department = None
    if current_user.department_id:
        result = await db.execute(
            select(Department).where(Department.id == current_user.department_id)
        )
        department = result.scalar_one_or_none()

    # Create generation request
    gen_request = GenerationRequest(
        prompt=request_data.prompt,
        size=request_data.size,
        quality=request_data.quality,
        num_images=request_data.num_images,
        user_id=str(current_user.id),
        department_id=str(department.id) if department else None,
    )

    # Get model router
    router_instance = get_model_router()

    # Estimate cost
    estimated_cost = Decimal("0")
    if request_data.preferred_provider:
        provider = router_instance.providers.get(request_data.preferred_provider)
        if provider:
            estimated_cost = provider.estimate_cost(gen_request)
    else:
        # Find cheapest provider
        for provider in router_instance.providers.values():
            cost = provider.estimate_cost(gen_request)
            if estimated_cost == 0 or cost < estimated_cost:
                estimated_cost = cost

    # Check max cost safety limit
    if estimated_cost > Decimal(str(settings.MAX_COST_PER_IMAGE_AUD)) * request_data.num_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estimated cost ${float(estimated_cost):.4f} exceeds safety limit"
        )

    # Check department budget
    if department:
        budget_remaining = department.budget_remaining_aud
        if estimated_cost > budget_remaining:
            # Check enforcement mode
            enforcement = department.settings.get("budget_enforcement", settings.BUDGET_ENFORCEMENT)
            if enforcement == "hard":
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Insufficient budget. Remaining: ${float(budget_remaining):.2f}, "
                           f"Required: ${float(estimated_cost):.2f}"
                )
            elif enforcement == "soft":
                logger.warning(
                    "budget_exceeded_soft_enforcement",
                    user_id=str(current_user.id),
                    department_id=str(department.id),
                    estimated_cost=float(estimated_cost),
                    budget_remaining=float(budget_remaining),
                )

    # Create database record
    prompt_hash = hashlib.sha256(request_data.prompt.encode()).hexdigest()

    generation = ImageGeneration(
        user_id=current_user.id,
        department_id=department.id if department else None,
        prompt=request_data.prompt,
        prompt_hash=prompt_hash,
        size=request_data.size.value,
        quality=request_data.quality.value,
        num_images_requested=request_data.num_images,
        preferred_provider=request_data.preferred_provider.value if request_data.preferred_provider else None,
        estimated_cost_aud=estimated_cost,
        status=GenerationStatus.PROCESSING,
        request_metadata={
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    )

    db.add(generation)
    await db.commit()
    await db.refresh(generation)

    try:
        # Generate images
        result = await router_instance.generate(
            request=gen_request,
            preferred_provider=request_data.preferred_provider,
            max_cost_aud=request_data.max_cost_aud,
        )

        if not result.success:
            # Generation failed
            generation.status = GenerationStatus.FAILED
            generation.error_message = result.error_message
            generation.generation_time_ms = result.generation_time_ms
            await db.commit()

            logger.error(
                "image_generation_failed",
                user_id=str(current_user.id),
                error=result.error_message,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error_message or "Image generation failed"
            )

        # Update generation record with results
        generation.status = GenerationStatus.COMPLETED
        generation.num_images_generated = len(result.image_urls)
        generation.image_urls = result.image_urls
        generation.model_used = result.model_used
        generation.provider_used = result.provider.value
        generation.cost_aud = result.cost_aud
        generation.generation_time_ms = result.generation_time_ms
        generation.metadata = result.metadata
        generation.completed_at = datetime.utcnow()

        # Update department budget
        if department:
            department.current_spend_aud += result.cost_aud

        await db.commit()
        await db.refresh(generation)

        logger.info(
            "image_generated_successfully",
            generation_id=str(generation.id),
            user_id=str(current_user.id),
            num_images=len(result.image_urls),
            cost_aud=float(result.cost_aud),
            provider=result.provider.value,
        )

        # Build response
        generated_images = [
            GeneratedImage(
                id=generation.id,
                url=url,
                prompt=generation.prompt,
                size=request_data.size,
                quality=request_data.quality,
                model_used=result.model_used,
                provider=result.provider,
                cost_aud=result.cost_aud / len(result.image_urls),
                generation_time_ms=result.generation_time_ms,
                created_at=generation.created_at,
            )
            for url in result.image_urls
        ]

        return GenerateImageResponse(
            success=True,
            images=generated_images,
            total_cost_aud=result.cost_aud,
            total_time_ms=result.generation_time_ms,
            provider_used=result.provider,
            metadata=result.metadata,
        )

    except Exception as e:
        # Update generation status
        generation.status = GenerationStatus.FAILED
        generation.error_message = str(e)
        await db.commit()

        logger.error(
            "image_generation_exception",
            user_id=str(current_user.id),
            error=str(e),
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation error: {str(e)}"
        )


# ┌─────────────────────────────────────────────────────────┐
# │ Cost Estimation                                         │
# └─────────────────────────────────────────────────────────┘


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_generation_cost(
    request_data: CostEstimateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> CostEstimateResponse:
    """
    Estimate cost for image generation without actually generating.

    **Use Cases:**
    - Cost comparison across providers
    - Budget planning
    - User education about costs

    **Returns:**
    - Cost estimate for each available provider
    - Recommended (cheapest) provider
    - Provider availability status
    """
    gen_request = GenerationRequest(
        prompt=request_data.prompt,
        size=request_data.size,
        quality=request_data.quality,
        num_images=request_data.num_images,
        user_id=str(current_user.id),
    )

    router_instance = get_model_router()
    estimates = []
    cheapest_cost = None
    recommended_provider = None

    for provider_type, provider in router_instance.providers.items():
        # Skip if user requested specific provider
        if request_data.provider and provider_type != request_data.provider:
            continue

        cost_per_image = provider.estimate_cost(
            GenerationRequest(
                prompt=request_data.prompt,
                size=request_data.size,
                quality=request_data.quality,
                num_images=1,
                user_id=str(current_user.id),
            )
        )
        total_cost = cost_per_image * request_data.num_images

        estimates.append(
            ProviderCostEstimate(
                provider=provider_type,
                cost_per_image_aud=cost_per_image,
                total_cost_aud=total_cost,
                available=True,
            )
        )

        if cheapest_cost is None or total_cost < cheapest_cost:
            cheapest_cost = total_cost
            recommended_provider = provider_type

    if not estimates:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No model providers available"
        )

    return CostEstimateResponse(
        estimates=estimates,
        recommended_provider=recommended_provider,
        cheapest_cost_aud=cheapest_cost,
    )


# ┌─────────────────────────────────────────────────────────┐
# │ Generation History                                      │
# └─────────────────────────────────────────────────────────┘


@router.get("/generations", response_model=GenerationHistoryResponse)
async def list_generations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> GenerationHistoryResponse:
    """
    List user's generation history.

    **Permissions:**
    - Users see only their own generations
    - Dept Managers see department generations
    - Org Admins see all generations

    **Pagination:**
    - Default: 20 items per page
    - Max: 100 items per page

    **Ordering:**
    - Most recent first (created_at DESC)
    """
    # Build query based on permissions
    query = select(ImageGeneration).where(
        ImageGeneration.deleted_at.is_(None),
        ImageGeneration.status == GenerationStatus.COMPLETED,
    )

    if current_user.role == UserRole.STANDARD_USER or current_user.role == UserRole.POWER_USER:
        # Regular users see only their own
        query = query.where(ImageGeneration.user_id == current_user.id)
    elif current_user.role == UserRole.DEPT_MANAGER:
        # Dept managers see department generations
        query = query.where(ImageGeneration.department_id == current_user.department_id)
    # Org admins and super admins see all (no additional filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(desc(ImageGeneration.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    generations = result.scalars().all()

    # Calculate total cost
    cost_query = select(func.sum(ImageGeneration.cost_aud)).where(
        ImageGeneration.user_id == current_user.id,
        ImageGeneration.status == GenerationStatus.COMPLETED,
        ImageGeneration.deleted_at.is_(None),
    )
    cost_result = await db.execute(cost_query)
    total_cost = cost_result.scalar() or Decimal("0")

    # Build response items
    from app.schemas.generation import GenerationHistoryItem
    items = [
        GenerationHistoryItem(
            id=gen.id,
            prompt=gen.prompt,
            image_url=gen.image_urls[0] if gen.image_urls else "",
            size=ImageSize(gen.size),
            quality=ImageQuality(gen.quality),
            model_used=gen.model_used or "unknown",
            provider=ModelProvider(gen.provider_used) if gen.provider_used else ModelProvider.OPENAI_DALLE3,
            cost_aud=gen.cost_aud,
            created_at=gen.created_at,
            created_by=current_user.email,
        )
        for gen in generations
    ]

    return GenerationHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_cost_aud=total_cost,
    )


# 📋 ISO 27001 Control Mapping:
# - A.9.4.1: Information access restriction (RBAC)
# - A.12.4.1: Event logging (audit trail)
# - A.14.2.1: Secure development policy (input validation)
# - A.12.1.3: Capacity management (budget enforcement)
