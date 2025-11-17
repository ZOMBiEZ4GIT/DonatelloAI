"""
Generation model for tracking image generation requests.

Tracks all image generation requests with costs, status, and metadata.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from app.db.base import Base


class GenerationStatus(str, Enum):
    """Generation status enumeration."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ModelType(str, Enum):
    """AI model type enumeration."""

    DALLE3 = "DALLE3"
    SDXL = "SDXL"
    FIREFLY = "FIREFLY"
    AZURE_AI = "AZURE_AI"


class Generation(Base):
    """
    Generation model for image generation tracking.

    Attributes:
        id: Unique generation identifier
        user_id: Foreign key to user who created the generation
        prompt: Text prompt for image generation
        negative_prompt: Negative prompt (what to avoid)
        model_used: AI model used for generation
        status: Current generation status
        image_url: URL to generated image (Azure Blob Storage)
        thumbnail_url: URL to thumbnail image
        cost_aud: Cost of this generation in AUD
        generation_time_ms: Time taken to generate (milliseconds)
        metadata: Additional metadata (parameters, settings, etc.)
        error_message: Error message if generation failed
        created_at: Generation request timestamp
        completed_at: Generation completion timestamp
    """

    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_used: Mapped[ModelType] = mapped_column(
        SQLEnum(ModelType),
        nullable=False,
        index=True,
    )
    status: Mapped[GenerationStatus] = mapped_column(
        SQLEnum(GenerationStatus),
        default=GenerationStatus.PENDING,
        nullable=False,
        index=True,
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    cost_aud: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
    )
    generation_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(
        String,  # Store JSON as string for SQLite compatibility
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="generations",
    )

    def __repr__(self) -> str:
        return (
            f"<Generation(id={self.id}, user_id={self.user_id}, "
            f"model={self.model_used}, status={self.status}, cost={self.cost_aud})>"
        )

    @property
    def is_completed(self) -> bool:
        """Check if generation is completed."""
        return self.status == GenerationStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if generation failed."""
        return self.status == GenerationStatus.FAILED
