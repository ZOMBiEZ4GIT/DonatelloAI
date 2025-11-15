"""
╔════════════════════════════════════════════════════════╗
║        Image Generation Database Models                ║
║          Generation History & Cost Tracking            ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Track all image generations for audit
    - Calculate department/user costs
    - Support budget enforcement
    - Provide usage analytics

Cost Tracking:
    - Per-image cost in AUD (Decimal precision)
    - Department budget tracking
    - User usage metrics
    - Model provider performance

ISO 27001 Controls:
    - A.12.4.1: Event logging (audit trail)
    - A.9.4.1: Information access restriction
    - A.12.1.2: Change management
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class GenerationStatus(str, Enum):
    """
    Generation job status.
    """

    PENDING = "pending"  # Queued but not started
    PROCESSING = "processing"  # Currently generating
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Generation failed
    CANCELLED = "cancelled"  # User cancelled


class ImageGeneration(Base):
    """
    Record of a single image generation.

    Business Context:
        - Complete audit trail of all generations
        - Cost tracking for budget enforcement
        - Performance metrics for optimization
        - User activity monitoring

    Relationships:
        - user: User who created this generation
        - department: Department to charge costs to

    Security:
        - Prompts are stored for audit purposes
        - Image URLs are CDN-backed blob storage
        - Soft delete preserves audit trail
    """

    __tablename__ = "image_generations"

    # ┌─────────────────────────────────────────────────────────┐
    # │ Primary Key & Identity                                  │
    # └─────────────────────────────────────────────────────────┘
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # ┌─────────────────────────────────────────────────────────┐
    # │ Relationships                                           │
    # └─────────────────────────────────────────────────────────┘
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Generation Details                                      │
    # └─────────────────────────────────────────────────────────┘
    prompt = Column(Text, nullable=False)
    prompt_hash = Column(
        String(64),
        nullable=True,
        index=True,
        comment="SHA256 hash for duplicate detection",
    )

    size = Column(String(50), nullable=False)  # "small", "medium", "large"
    quality = Column(String(50), nullable=False)  # "standard", "hd"
    num_images_requested = Column(Integer, nullable=False, default=1)
    num_images_generated = Column(Integer, nullable=False, default=0)

    # ┌─────────────────────────────────────────────────────────┐
    # │ Model & Provider                                        │
    # └─────────────────────────────────────────────────────────┘
    model_used = Column(String(100), nullable=True)  # "dall-e-3", "sdxl", etc.
    provider_used = Column(String(100), nullable=True)  # "azure_openai_dalle3", etc.
    preferred_provider = Column(
        String(100),
        nullable=True,
        comment="User's requested provider",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Cost Tracking (AUD, Decimal precision)                  │
    # └─────────────────────────────────────────────────────────┘
    cost_aud = Column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Actual cost in AUD",
    )
    estimated_cost_aud = Column(
        Numeric(10, 4),
        nullable=True,
        comment="Pre-generation estimate",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Results                                                 │
    # └─────────────────────────────────────────────────────────┘
    image_urls = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="List of generated image URLs",
    )
    storage_paths = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Azure Blob Storage paths",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Status & Performance                                    │
    # └─────────────────────────────────────────────────────────┘
    status = Column(
        SQLEnum(GenerationStatus, name="generation_status_enum"),
        nullable=False,
        default=GenerationStatus.PENDING,
        index=True,
    )
    generation_time_ms = Column(
        Integer,
        nullable=True,
        comment="Time taken to generate (milliseconds)",
    )
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True, index=True)

    # ┌─────────────────────────────────────────────────────────┐
    # │ Metadata                                                │
    # └─────────────────────────────────────────────────────────┘
    metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Model-specific metadata",
    )
    request_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="IP, user agent, etc.",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Audit & Compliance                                      │
    # └─────────────────────────────────────────────────────────┘
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Soft delete timestamp",
    )

    # Relationships
    user = relationship("User", back_populates="generations")
    department = relationship("Department", back_populates="generations")

    def __repr__(self) -> str:
        return (
            f"<ImageGeneration(id={self.id}, "
            f"user_id={self.user_id}, "
            f"status={self.status.value}, "
            f"cost_aud={self.cost_aud})>"
        )

    @property
    def is_deleted(self) -> bool:
        """Check if generation is soft-deleted."""
        return self.deleted_at is not None

    @property
    def cost_per_image_aud(self) -> Decimal:
        """Calculate cost per image."""
        if self.num_images_generated > 0:
            return Decimal(str(self.cost_aud)) / Decimal(str(self.num_images_generated))
        return Decimal("0")

    def soft_delete(self) -> None:
        """Soft delete this generation (preserves audit trail)."""
        self.deleted_at = datetime.utcnow()


class BatchGenerationJob(Base):
    """
    Batch image generation job.

    Business Context:
        - Bulk generation for marketing/content teams
        - Scheduled during off-peak hours
        - Cost-optimized provider selection
        - Progress tracking for large jobs

    Cost Management:
        - Pre-job cost estimation
        - Budget validation before execution
        - Per-image cost tracking
        - Department budget charging
    """

    __tablename__ = "batch_generation_jobs"

    # ┌─────────────────────────────────────────────────────────┐
    # │ Primary Key & Identity                                  │
    # └─────────────────────────────────────────────────────────┘
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # ┌─────────────────────────────────────────────────────────┐
    # │ Relationships                                           │
    # └─────────────────────────────────────────────────────────┘
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Job Configuration                                       │
    # └─────────────────────────────────────────────────────────┘
    prompts = Column(
        JSONB,
        nullable=False,
        comment="List of prompts to generate",
    )
    size = Column(String(50), nullable=False)
    quality = Column(String(50), nullable=False)
    preferred_provider = Column(String(100), nullable=True)
    max_cost_per_image_aud = Column(Numeric(10, 4), nullable=True)

    # ┌─────────────────────────────────────────────────────────┐
    # │ Progress Tracking                                       │
    # └─────────────────────────────────────────────────────────┘
    total_prompts = Column(Integer, nullable=False)
    completed_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    cancelled_count = Column(Integer, nullable=False, default=0)

    # ┌─────────────────────────────────────────────────────────┐
    # │ Cost Tracking                                           │
    # └─────────────────────────────────────────────────────────┘
    estimated_total_cost_aud = Column(Numeric(10, 4), nullable=True)
    actual_total_cost_aud = Column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Status                                                  │
    # └─────────────────────────────────────────────────────────┘
    status = Column(
        SQLEnum(GenerationStatus, name="generation_status_enum"),
        nullable=False,
        default=GenerationStatus.PENDING,
        index=True,
    )
    error_message = Column(Text, nullable=True)

    # ┌─────────────────────────────────────────────────────────┐
    # │ Audit                                                   │
    # └─────────────────────────────────────────────────────────┘
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="batch_jobs")
    department = relationship("Department", back_populates="batch_jobs")

    def __repr__(self) -> str:
        return (
            f"<BatchGenerationJob(id={self.id}, "
            f"total_prompts={self.total_prompts}, "
            f"completed={self.completed_count}, "
            f"status={self.status.value})>"
        )

    @property
    def progress_percent(self) -> float:
        """Calculate job completion percentage."""
        if self.total_prompts == 0:
            return 0.0
        return (self.completed_count / self.total_prompts) * 100

    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in [
            GenerationStatus.COMPLETED,
            GenerationStatus.FAILED,
            GenerationStatus.CANCELLED,
        ]


# ⚠️  COST TRACKING PRECISION:
#
# 💰 Decimal(10, 4) Format:
# - Total: 10 digits
# - Decimal places: 4
# - Max value: 999,999.9999 AUD
# - Precision: $0.0001 (0.01 cents)
#
# Why 4 decimal places?
# - Model costs can be fractional cents ($0.0234)
# - Accurate department budget tracking
# - No floating-point rounding errors
# - ISO standard for financial calculations
#
# 📊 Example Calculations:
# DALL-E 3 Standard: 0.0800 AUD
# SDXL Standard: 0.0200 AUD
# Firefly Premium: 0.1500 AUD
# 100 images @ SDXL: 2.0000 AUD
#
# 📋 ISO 27001 Control Mapping:
# - A.12.4.1: Event logging (complete audit trail)
# - A.9.4.1: Information access restriction (user/dept isolation)
# - A.12.1.2: Change management (status tracking)
# - A.15.1.1: Supplier agreements (provider tracking)
