"""
╔════════════════════════════════════════════════════════╗
║           DALL-E 3 Model Provider                       ║
║         OpenAI / Azure OpenAI Integration              ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Primary model for high-quality generations
    - Supports both OpenAI and Azure OpenAI Service
    - Higher cost but better quality
    - Built-in safety filtering

Security Considerations:
    - API key from Azure Key Vault
    - Automatic content policy enforcement
    - PII detection before sending prompts
    - Audit logging for all requests

Cost:
    - Standard: ~$0.08 AUD per image
    - HD Quality: ~$0.12 AUD per image
"""

import time
from decimal import Decimal
from typing import Optional

from openai import AsyncOpenAI, AsyncAzureOpenAI
import asyncio

from app.core.config import settings
from app.core.logging import logger
from app.services.models.base import (
    BaseModelProvider,
    GenerationRequest,
    GenerationResult,
    ImageSize,
    ImageQuality,
    ModelProvider,
)


class DALLE3Provider(BaseModelProvider):
    """
    DALL-E 3 model provider.

    Supports both OpenAI and Azure OpenAI Service.

    Security:
        - Automatic safety filtering by OpenAI
        - Content policy enforcement
        - Audit logging

    Cost Management:
        - Fixed cost per image and quality level
        - No hidden fees
        - Billed per successful generation
    """

    def __init__(
        self,
        api_key: str,
        use_azure: bool = False,
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None,
    ):
        """
        Initialize DALL-E 3 provider.

        Args:
            api_key: OpenAI or Azure OpenAI API key
            use_azure: Use Azure OpenAI Service
            azure_endpoint: Azure endpoint (if use_azure=True)
            azure_deployment: Azure deployment name (if use_azure=True)
        """
        # Base cost for standard quality
        super().__init__(
            api_key=api_key,
            cost_per_image_aud=Decimal("0.08"),
            timeout_seconds=90,  # DALL-E can be slow
            max_retries=2,  # Limited retries (expensive)
        )

        self.use_azure = use_azure

        if use_azure:
            if not azure_endpoint or not azure_deployment:
                raise ValueError("Azure endpoint and deployment required for Azure OpenAI")

            self.client = AsyncAzureOpenAI(
                api_key=api_key,
                azure_endpoint=azure_endpoint,
                azure_deployment=azure_deployment,
                api_version="2024-02-01",
            )
            self.provider_name = "Azure OpenAI (DALL-E 3)"
        else:
            self.client = AsyncOpenAI(api_key=api_key)
            self.provider_name = "OpenAI (DALL-E 3)"

    def get_provider_name(self) -> str:
        """Get provider name."""
        return self.provider_name

    def get_supported_sizes(self) -> list[ImageSize]:
        """Get supported image sizes."""
        return [
            ImageSize.SMALL,  # 1024x1024
            ImageSize.PORTRAIT,  # 1024x1792
            ImageSize.LANDSCAPE,  # 1792x1024
        ]

    def estimate_cost(self, request: GenerationRequest) -> Decimal:
        """
        Estimate generation cost.

        Pricing (as of 2024):
        - Standard 1024x1024: $0.08 AUD
        - Standard 1024x1792/1792x1024: $0.08 AUD
        - HD Quality: +50% cost
        """
        base_cost = self.cost_per_image_aud

        # HD quality costs more
        if request.quality == ImageQuality.HD:
            base_cost = base_cost * Decimal("1.5")

        total_cost = base_cost * request.num_images

        return total_cost.quantize(Decimal("0.01"))

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate image using DALL-E 3.

        Args:
            request: Generation request

        Returns:
            GenerationResult with image URL and metadata

        Note:
            - DALL-E 3 only generates 1 image at a time
            - Multiple images require multiple API calls
        """
        self._log_generation_start(request)
        start_time = time.time()

        try:
            # Validate size
            if request.size not in self.get_supported_sizes():
                supported = [s.value for s in self.get_supported_sizes()]
                raise ValueError(
                    f"Size {request.size.value} not supported. Supported: {supported}"
                )

            # DALL-E 3 only generates 1 image per request
            if request.num_images > 1:
                logger.warning(
                    "dalle3_multiple_images_requested",
                    requested=request.num_images,
                    note="Will make multiple API calls",
                )

            image_urls = []
            total_cost = Decimal("0")

            # Generate each image
            for i in range(request.num_images):
                try:
                    response = await self.client.images.generate(
                        model="dall-e-3",
                        prompt=request.prompt,
                        size=request.size.value,
                        quality=request.quality.value,
                        n=1,  # DALL-E 3 only supports n=1
                    )

                    # Extract image URL
                    if response.data and len(response.data) > 0:
                        image_urls.append(response.data[0].url)
                        total_cost += self.estimate_cost(
                            GenerationRequest(
                                prompt=request.prompt,
                                size=request.size,
                                quality=request.quality,
                                num_images=1,
                            )
                        )

                except Exception as e:
                    logger.error(
                        "dalle3_single_generation_failed",
                        image_index=i,
                        error=str(e),
                    )
                    # Continue with other images if one fails
                    continue

            # Calculate generation time
            generation_time_ms = int((time.time() - start_time) * 1000)

            result = GenerationResult(
                success=len(image_urls) > 0,
                image_urls=image_urls,
                cost_aud=total_cost,
                generation_time_ms=generation_time_ms,
                model_used="dall-e-3",
                provider=ModelProvider.AZURE_OPENAI_DALLE3 if self.use_azure else ModelProvider.OPENAI_DALLE3,
                metadata={
                    "quality": request.quality.value,
                    "size": request.size.value,
                    "images_requested": request.num_images,
                    "images_generated": len(image_urls),
                },
                error_message=None if len(image_urls) > 0 else "Failed to generate any images",
            )

            self._log_generation_success(request, result)
            return result

        except Exception as e:
            self._log_generation_failure(request, e)

            generation_time_ms = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=False,
                image_urls=[],
                cost_aud=Decimal("0"),
                generation_time_ms=generation_time_ms,
                model_used="dall-e-3",
                provider=ModelProvider.AZURE_OPENAI_DALLE3 if self.use_azure else ModelProvider.OPENAI_DALLE3,
                metadata={
                    "error_type": type(e).__name__,
                },
                error_message=str(e),
            )


# ⚠️  DALL-E 3 NOTES:
#
# 🎨 Capabilities:
# - Highest quality photorealistic images
# - Best prompt understanding
# - Built-in safety filtering
# - No fine-tuning needed
#
# 💰 Cost:
# - Standard: $0.04 USD (~$0.08 AUD) per image
# - HD: $0.08 USD (~$0.12 AUD) per image
# - No additional fees
# - Billed per successful generation only
#
# ⏱️ Performance:
# - Average: 10-30 seconds per image
# - Can be slower for complex prompts
# - Timeout: 90 seconds
# - No batch generation (n=1 only)
#
# 🔒 Safety:
# - Automatic content policy enforcement
# - Blocks NSFW prompts
# - Blocks copyrighted content
# - No manual filtering needed
#
# 📊 Supported Sizes:
# - 1024x1024 (square)
# - 1024x1792 (portrait)
# - 1792x1024 (landscape)
# - No custom sizes
#
# 🚫 Limitations:
# - Only 1 image per API call (n=1)
# - No negative prompts
# - No seed control
# - No style transfer
# - Limited customization
#
# 📋 ISO 27001 Control: A.12.6.1 - Management of technical vulnerabilities
