"""
╔════════════════════════════════════════════════════════╗
║     Image Generation Pydantic Schemas                  ║
║       Request/Response Models for Generation           ║
╚════════════════════════════════════════════════════════╝
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.services.models.base import ImageQuality, ImageSize, ModelProvider


# ┌─────────────────────────────────────────────────────────┐
# │ Generation Request Schemas                              │
# └─────────────────────────────────────────────────────────┘


class GenerateImageRequest(BaseModel):
    """
    Request to generate a single image.

    Validation:
        - Prompt must be 3-1000 characters
        - Size must be valid ImageSize enum
        - Quality must be valid ImageQuality enum
        - num_images: 1-4 (DALL-E limit)
    """

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Image generation prompt",
    )
    size: ImageSize = Field(
        default=ImageSize.MEDIUM,
        description="Image size",
    )
    quality: ImageQuality = Field(
        default=ImageQuality.STANDARD,
        description="Image quality level",
    )
    num_images: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Number of images to generate (1-4)",
    )
    preferred_provider: Optional[ModelProvider] = Field(
        None,
        description="Preferred model provider (optional)",
    )
    max_cost_aud: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Maximum cost limit in AUD (optional)",
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt content."""
        # Strip whitespace
        v = v.strip()

        # Check minimum length
        if len(v) < 3:
            raise ValueError("Prompt must be at least 3 characters")

        # Check for obvious abuse
        if v.lower() in ["test", "testing", "123", "aaa", "xxx"]:
            raise ValueError("Please provide a descriptive prompt")

        return v


class BatchGenerateRequest(BaseModel):
    """
    Request to generate multiple images in batch.

    Business Context:
        - Used for bulk generation jobs
        - Scheduled for off-peak hours
        - Cost-optimized provider selection
    """

    prompts: list[str] = Field(
        ...,
        min_length=2,
        max_length=100,
        description="List of prompts (2-100)",
    )
    size: ImageSize = Field(
        default=ImageSize.MEDIUM,
        description="Image size for all",
    )
    quality: ImageQuality = Field(
        default=ImageQuality.STANDARD,
        description="Quality level for all",
    )
    preferred_provider: Optional[ModelProvider] = Field(
        None,
        description="Preferred provider",
    )
    max_cost_per_image_aud: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Max cost per image",
    )

    @field_validator("prompts")
    @classmethod
    def validate_prompts(cls, v: list[str]) -> list[str]:
        """Validate all prompts."""
        cleaned = []
        for prompt in v:
            prompt = prompt.strip()
            if len(prompt) < 3:
                raise ValueError(f"Prompt too short: {prompt}")
            if len(prompt) > 1000:
                raise ValueError(f"Prompt too long: {prompt[:50]}...")
            cleaned.append(prompt)

        # Check for duplicates
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Duplicate prompts detected")

        return cleaned


# ┌─────────────────────────────────────────────────────────┐
# │ Generation Response Schemas                             │
# └─────────────────────────────────────────────────────────┘


class GeneratedImage(BaseModel):
    """
    Single generated image metadata.
    """

    id: UUID = Field(..., description="Image ID")
    url: str = Field(..., description="Image URL")
    prompt: str = Field(..., description="Generation prompt")
    size: ImageSize = Field(..., description="Image size")
    quality: ImageQuality = Field(..., description="Quality level")
    model_used: str = Field(..., description="Model identifier")
    provider: ModelProvider = Field(..., description="Provider used")
    cost_aud: Decimal = Field(..., description="Generation cost in AUD")
    generation_time_ms: int = Field(..., description="Time taken in milliseconds")
    created_at: datetime = Field(..., description="Creation timestamp")


class GenerateImageResponse(BaseModel):
    """
    Response from single image generation request.
    """

    success: bool = Field(..., description="Generation succeeded")
    images: list[GeneratedImage] = Field(..., description="Generated images")
    total_cost_aud: Decimal = Field(..., description="Total cost in AUD")
    total_time_ms: int = Field(..., description="Total time in milliseconds")
    provider_used: ModelProvider = Field(..., description="Provider used")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    error_message: Optional[str] = Field(None, description="Error if failed")


class BatchGenerateResponse(BaseModel):
    """
    Response from batch generation request.
    """

    job_id: UUID = Field(..., description="Batch job ID")
    status: str = Field(..., description="Job status")
    total_prompts: int = Field(..., description="Total prompts")
    completed: int = Field(default=0, description="Completed count")
    failed: int = Field(default=0, description="Failed count")
    estimated_cost_aud: Decimal = Field(..., description="Estimated total cost")
    created_at: datetime = Field(..., description="Job creation time")


class GenerationHistoryItem(BaseModel):
    """
    Historical generation record.
    """

    id: UUID = Field(..., description="Generation ID")
    prompt: str = Field(..., description="Prompt used")
    image_url: str = Field(..., description="Image URL")
    size: ImageSize = Field(..., description="Size")
    quality: ImageQuality = Field(..., description="Quality")
    model_used: str = Field(..., description="Model")
    provider: ModelProvider = Field(..., description="Provider")
    cost_aud: Decimal = Field(..., description="Cost in AUD")
    created_at: datetime = Field(..., description="Generation time")
    created_by: str = Field(..., description="User email")


class GenerationHistoryResponse(BaseModel):
    """
    Paginated generation history response.
    """

    items: list[GenerationHistoryItem] = Field(..., description="History items")
    total: int = Field(..., description="Total items")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_cost_aud: Decimal = Field(..., description="Total cost across all items")


class GenerationStatsResponse(BaseModel):
    """
    Generation statistics for a user or department.
    """

    total_images: int = Field(..., description="Total images generated")
    total_cost_aud: Decimal = Field(..., description="Total cost in AUD")
    average_cost_per_image_aud: Decimal = Field(..., description="Average cost per image")
    images_by_provider: dict[str, int] = Field(..., description="Count by provider")
    cost_by_provider: dict[str, Decimal] = Field(..., description="Cost by provider")
    images_by_quality: dict[str, int] = Field(..., description="Count by quality")
    period_start: datetime = Field(..., description="Stats period start")
    period_end: datetime = Field(..., description="Stats period end")


# ┌─────────────────────────────────────────────────────────┐
# │ Cost Estimation                                         │
# └─────────────────────────────────────────────────────────┘


class CostEstimateRequest(BaseModel):
    """
    Request for cost estimation.
    """

    prompt: str = Field(..., min_length=3, max_length=1000)
    size: ImageSize = Field(default=ImageSize.MEDIUM)
    quality: ImageQuality = Field(default=ImageQuality.STANDARD)
    num_images: int = Field(default=1, ge=1, le=100)
    provider: Optional[ModelProvider] = Field(None, description="Specific provider (optional)")


class ProviderCostEstimate(BaseModel):
    """
    Cost estimate for a specific provider.
    """

    provider: ModelProvider = Field(..., description="Provider")
    cost_per_image_aud: Decimal = Field(..., description="Cost per image")
    total_cost_aud: Decimal = Field(..., description="Total cost")
    available: bool = Field(..., description="Provider is available")


class CostEstimateResponse(BaseModel):
    """
    Cost estimate response with all providers.
    """

    estimates: list[ProviderCostEstimate] = Field(..., description="Estimates by provider")
    recommended_provider: ModelProvider = Field(..., description="Cheapest available provider")
    cheapest_cost_aud: Decimal = Field(..., description="Cheapest option cost")


# 📋 ISO 27001 Control Mapping:
# - A.14.2.1: Secure development policy (input validation)
# - A.12.4.1: Event logging (cost tracking)
# - A.9.4.1: Information access restriction (user/dept isolation)
