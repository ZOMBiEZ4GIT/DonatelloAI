"""
╔════════════════════════════════════════════════════════╗
║            Base Model Provider Interface                ║
║         Abstract Base for AI Model Integration         ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Unified interface for all AI model providers
    - Enables intelligent model routing
    - Cost tracking per generation
    - Standardized error handling

Security Considerations:
    - API keys stored in Azure Key Vault
    - Rate limiting per provider
    - Timeout handling
    - Retry logic with exponential backoff

ISO 27001 Controls:
    - A.12.6.1: Management of technical vulnerabilities
    - A.13.1.3: Segregation in networks
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any

from app.core.logging import logger


class ModelProvider(str, Enum):
    """Supported AI model providers."""
    OPENAI_DALLE3 = "openai_dalle3"
    AZURE_OPENAI_DALLE3 = "azure_openai_dalle3"
    REPLICATE_SDXL = "replicate_sdxl"
    ADOBE_FIREFLY = "adobe_firefly"
    AZURE_AI_IMAGE = "azure_ai_image"


class ImageSize(str, Enum):
    """Standard image sizes."""
    SMALL = "1024x1024"
    MEDIUM = "1536x1536"
    LARGE = "2048x2048"
    PORTRAIT = "1024x1792"
    LANDSCAPE = "1792x1024"


class ImageQuality(str, Enum):
    """Image quality levels."""
    STANDARD = "standard"
    HD = "hd"


@dataclass
class GenerationRequest:
    """
    Standard generation request format.

    All providers receive this format and translate to their API.
    """
    prompt: str
    size: ImageSize = ImageSize.SMALL
    quality: ImageQuality = ImageQuality.STANDARD
    style: Optional[str] = None
    negative_prompt: Optional[str] = None
    num_images: int = 1
    seed: Optional[int] = None
    user_id: str = ""  # For tracking
    department_id: Optional[str] = None  # For cost allocation


@dataclass
class GenerationResult:
    """
    Standard generation result format.

    All providers return this format.
    """
    success: bool
    image_urls: list[str]
    cost_aud: Decimal
    generation_time_ms: int
    model_used: str
    provider: ModelProvider
    metadata: Dict[str, Any]
    error_message: Optional[str] = None


class BaseModelProvider(ABC):
    """
    Abstract base class for all AI model providers.

    All model integrations must implement this interface.

    Security:
        - API keys loaded from Azure Key Vault
        - Timeouts prevent hanging requests
        - Retry logic with exponential backoff
        - Rate limiting enforced

    Cost Management:
        - Every generation returns cost in AUD
        - Costs tracked per user and department
        - Budget limits enforced before generation

    ISO 27001 Control: A.12.6.1 - Management of technical vulnerabilities
    """

    def __init__(
        self,
        api_key: str,
        cost_per_image_aud: Decimal,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize model provider.

        Args:
            api_key: API key for the provider
            cost_per_image_aud: Cost per image in Australian dollars
            timeout_seconds: Request timeout
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key
        self.cost_per_image_aud = cost_per_image_aud
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate image(s) from prompt.

        Args:
            request: Generation request

        Returns:
            GenerationResult with image URLs and metadata

        Raises:
            ModelProviderError: If generation fails after retries
            BudgetExceededError: If cost exceeds limits
            ContentViolationError: If prompt violates policies

        Security:
            - Input validation on prompt
            - PII detection before sending
            - Content filtering on results
            - Rate limiting enforced
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name for logging."""
        pass

    @abstractmethod
    def get_supported_sizes(self) -> list[ImageSize]:
        """Get list of supported image sizes."""
        pass

    @abstractmethod
    def estimate_cost(self, request: GenerationRequest) -> Decimal:
        """
        Estimate cost before generation.

        Args:
            request: Generation request

        Returns:
            Estimated cost in AUD

        Note:
            - Used for budget checking before generation
            - Should include all provider fees
            - Rounded to 2 decimal places
        """
        pass

    def _log_generation_start(self, request: GenerationRequest) -> None:
        """Log generation start for audit."""
        logger.info(
            "model_generation_started",
            provider=self.get_provider_name(),
            prompt_length=len(request.prompt),
            size=request.size.value,
            quality=request.quality.value,
            user_id=request.user_id,
            department_id=request.department_id,
        )

    def _log_generation_success(
        self,
        request: GenerationRequest,
        result: GenerationResult,
    ) -> None:
        """Log successful generation for audit."""
        logger.info(
            "model_generation_success",
            provider=self.get_provider_name(),
            images_generated=len(result.image_urls),
            cost_aud=float(result.cost_aud),
            generation_time_ms=result.generation_time_ms,
            user_id=request.user_id,
            department_id=request.department_id,
        )

    def _log_generation_failure(
        self,
        request: GenerationRequest,
        error: Exception,
    ) -> None:
        """Log generation failure for audit."""
        logger.error(
            "model_generation_failed",
            provider=self.get_provider_name(),
            error_type=type(error).__name__,
            error_message=str(error),
            user_id=request.user_id,
            department_id=request.department_id,
            exc_info=True,
        )


# ⚠️  MODEL PROVIDER NOTES:
#
# 🔌 Provider Implementation:
# Each model provider must:
# 1. Inherit from BaseModelProvider
# 2. Implement generate() method
# 3. Implement get_provider_name()
# 4. Implement get_supported_sizes()
# 5. Implement estimate_cost()
#
# 💰 Cost Tracking:
# - Every generation returns cost in AUD
# - Costs include all provider fees
# - Exchange rates applied if needed
# - Costs tracked per user/department
#
# 🔄 Retry Logic:
# - Exponential backoff: 2s, 4s, 8s
# - Retry on network errors
# - Retry on rate limit (429)
# - Do NOT retry on validation errors (400)
#
# ⏱️ Timeout Handling:
# - Default: 60 seconds
# - DALL-E 3: 90 seconds (slower)
# - Stable Diffusion: 45 seconds (faster)
# - Timeout prevents hanging requests
#
# 🛡️ Security:
# - API keys from Azure Key Vault
# - Prompt validation before sending
# - PII detection (block if found)
# - Content filtering on results
# - NSFW detection
#
# 📊 Monitoring:
# - All generations logged
# - Success/failure rates tracked
# - Latency metrics collected
# - Cost metrics aggregated
#
# 📋 ISO 27001 Control Mapping:
# - A.12.6.1: Management of technical vulnerabilities
# - A.13.1.3: Segregation in networks
# - A.14.2.5: Secure system engineering principles
