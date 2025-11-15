"""
╔════════════════════════════════════════════════════════╗
║         Stable Diffusion XL Model Provider             ║
║              via Replicate API                         ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Lower cost alternative to DALL-E 3
    - Open-source model for flexible usage
    - Good quality for standard use cases
    - Longer generation times acceptable for batch jobs

Cost Structure (AUD):
    - Standard: $0.02 per image
    - HD: $0.04 per image
    - ~75% cheaper than DALL-E 3

Technical Details:
    - Model: stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc
    - API: Replicate HTTP API
    - Timeout: 180 seconds (3 minutes)
    - Max size: 1024x1024

ISO 27001 Controls:
    - A.12.6.1: Secure API integration
    - A.14.2.1: Secure development policy
"""

import time
from decimal import Decimal
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services.models.base import (
    BaseModelProvider,
    GenerationRequest,
    GenerationResult,
    ImageQuality,
    ImageSize,
    ModelProvider,
)


class SDXLProvider(BaseModelProvider):
    """
    Stable Diffusion XL provider via Replicate.

    Features:
        - Cost-effective open-source alternative
        - Good quality for standard images
        - Longer generation times (60-180s)
        - Batch-friendly for non-urgent requests

    Cost Optimization:
        - 75% cheaper than DALL-E 3
        - Recommended for high-volume standard quality
        - Budget-conscious departments
    """

    # Model version hash
    SDXL_MODEL_VERSION = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"

    # Replicate API endpoints
    REPLICATE_API_BASE = "https://api.replicate.com/v1"
    PREDICTIONS_ENDPOINT = f"{REPLICATE_API_BASE}/predictions"

    # Cost per image in AUD
    COST_STANDARD_AUD = Decimal("0.02")
    COST_HD_AUD = Decimal("0.04")

    def __init__(
        self,
        api_key: str,
        timeout_seconds: int = 180,
    ):
        """
        Initialize Stable Diffusion XL provider.

        Args:
            api_key: Replicate API key
            timeout_seconds: Max wait time for generation (default: 180s)
        """
        super().__init__(
            cost_per_image_aud=self.COST_STANDARD_AUD,
            timeout_seconds=timeout_seconds,
        )
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout_seconds),
        )

        logger.info(
            "sdxl_provider_initialized",
            timeout_seconds=timeout_seconds,
        )

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Replicate SDXL"

    def estimate_cost(self, request: GenerationRequest) -> Decimal:
        """
        Estimate generation cost in AUD.

        Args:
            request: Generation request

        Returns:
            Estimated cost in AUD
        """
        # Select cost based on quality
        cost_per_image = (
            self.COST_HD_AUD
            if request.quality == ImageQuality.HD
            else self.COST_STANDARD_AUD
        )

        total_cost = cost_per_image * request.num_images

        logger.debug(
            "sdxl_cost_estimated",
            num_images=request.num_images,
            quality=request.quality.value,
            cost_per_image_aud=float(cost_per_image),
            total_cost_aud=float(total_cost),
        )

        return total_cost

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate images using Stable Diffusion XL.

        Args:
            request: Generation request

        Returns:
            Generation result with image URLs and metadata

        Flow:
            1. Create prediction with Replicate API
            2. Poll for completion (max timeout_seconds)
            3. Extract image URLs from response
            4. Calculate actual cost and generation time
        """
        start_time = time.time()
        image_urls = []

        try:
            # Map our size enum to SDXL dimensions
            width, height = self._map_size_to_dimensions(request.size)

            # Prepare SDXL input parameters
            input_params = {
                "prompt": request.prompt,
                "width": width,
                "height": height,
                "num_outputs": request.num_images,
                "scheduler": "K_EULER",
                "num_inference_steps": 50 if request.quality == ImageQuality.HD else 25,
                "guidance_scale": 7.5,
                "prompt_strength": 0.8,
            }

            # Create prediction
            logger.info(
                "sdxl_generating",
                prompt_length=len(request.prompt),
                num_images=request.num_images,
                size=request.size.value,
                quality=request.quality.value,
            )

            response = await self.client.post(
                self.PREDICTIONS_ENDPOINT,
                json={
                    "version": self.SDXL_MODEL_VERSION.split(":")[1],
                    "input": input_params,
                },
            )
            response.raise_for_status()

            prediction = response.json()
            prediction_id = prediction["id"]

            # Poll for completion
            max_polls = self.timeout_seconds // 5  # Poll every 5 seconds
            for poll_count in range(max_polls):
                await self._sleep(5)  # Wait 5 seconds between polls

                status_response = await self.client.get(
                    f"{self.PREDICTIONS_ENDPOINT}/{prediction_id}"
                )
                status_response.raise_for_status()
                status_data = status_response.json()

                status = status_data.get("status")

                if status == "succeeded":
                    # Extract image URLs
                    output = status_data.get("output", [])
                    if isinstance(output, list):
                        image_urls = output
                    else:
                        image_urls = [output]
                    break

                elif status == "failed":
                    error_msg = status_data.get("error", "Unknown error")
                    logger.error(
                        "sdxl_generation_failed",
                        prediction_id=prediction_id,
                        error=error_msg,
                    )
                    return self._error_result(
                        f"SDXL generation failed: {error_msg}",
                        start_time,
                    )

                elif status in ["starting", "processing"]:
                    # Still processing, continue polling
                    logger.debug(
                        "sdxl_processing",
                        prediction_id=prediction_id,
                        status=status,
                        poll_count=poll_count + 1,
                    )
                    continue

                else:
                    # Unexpected status
                    logger.warning(
                        "sdxl_unexpected_status",
                        prediction_id=prediction_id,
                        status=status,
                    )

            # Check if we got images
            if not image_urls:
                logger.error(
                    "sdxl_timeout",
                    prediction_id=prediction_id,
                    polls=max_polls,
                )
                return self._error_result(
                    "SDXL generation timed out",
                    start_time,
                )

            # Calculate cost and time
            generation_time_ms = int((time.time() - start_time) * 1000)
            actual_cost = self.estimate_cost(request)

            logger.info(
                "sdxl_generation_success",
                num_images=len(image_urls),
                generation_time_ms=generation_time_ms,
                cost_aud=float(actual_cost),
            )

            return GenerationResult(
                success=True,
                image_urls=image_urls,
                cost_aud=actual_cost,
                generation_time_ms=generation_time_ms,
                model_used="stable-diffusion-xl",
                provider=ModelProvider.REPLICATE_SDXL,
                metadata={
                    "version": self.SDXL_MODEL_VERSION,
                    "width": width,
                    "height": height,
                    "inference_steps": input_params["num_inference_steps"],
                    "guidance_scale": input_params["guidance_scale"],
                },
            )

        except httpx.HTTPError as e:
            logger.error(
                "sdxl_http_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return self._error_result(
                f"SDXL API error: {str(e)}",
                start_time,
            )

        except Exception as e:
            logger.error(
                "sdxl_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return self._error_result(
                f"Unexpected error: {str(e)}",
                start_time,
            )

    def _map_size_to_dimensions(self, size: ImageSize) -> tuple[int, int]:
        """
        Map ImageSize enum to SDXL dimensions.

        SDXL supports various aspect ratios, we use common ones.

        Args:
            size: ImageSize enum

        Returns:
            (width, height) tuple
        """
        size_map = {
            ImageSize.SMALL: (1024, 1024),  # 1:1 square
            ImageSize.MEDIUM: (1024, 1024),  # 1:1 square
            ImageSize.LARGE: (1024, 1024),  # 1:1 square
        }

        return size_map.get(size, (1024, 1024))

    def _error_result(self, error_message: str, start_time: float) -> GenerationResult:
        """
        Create error result.

        Args:
            error_message: Error description
            start_time: Generation start timestamp

        Returns:
            GenerationResult with error
        """
        generation_time_ms = int((time.time() - start_time) * 1000)

        return GenerationResult(
            success=False,
            image_urls=[],
            cost_aud=Decimal("0"),
            generation_time_ms=generation_time_ms,
            model_used="stable-diffusion-xl",
            provider=ModelProvider.REPLICATE_SDXL,
            metadata={},
            error_message=error_message,
        )

    async def _sleep(self, seconds: int) -> None:
        """
        Async sleep helper.

        Args:
            seconds: Sleep duration
        """
        import asyncio

        await asyncio.sleep(seconds)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources."""
        await self.client.aclose()


# ⚠️  COST ANALYSIS:
#
# 💰 Stable Diffusion XL Pricing (Replicate):
# Standard quality: $0.02 AUD per image (~$0.015 USD)
# HD quality: $0.04 AUD per image (~$0.03 USD)
#
# 📊 Comparison vs DALL-E 3:
# DALL-E 3 Standard: $0.08 AUD
# SDXL Standard: $0.02 AUD (75% savings)
#
# DALL-E 3 HD: $0.12 AUD
# SDXL HD: $0.04 AUD (67% savings)
#
# ⏱️  Performance Characteristics:
# Generation time: 60-180 seconds (vs 10-30s for DALL-E)
# Quality: Good for most use cases, slightly lower than DALL-E
# Best for: Batch jobs, budget-conscious departments, high-volume
#
# 🎯 Recommended Use Cases:
# - Department with tight budgets
# - Bulk image generation (>10 images)
# - Non-urgent requests
# - Standard quality requirements
#
# 📋 ISO 27001 Control Mapping:
# - A.12.6.1: Management of technical vulnerabilities (API security)
# - A.14.2.1: Secure development policy (cost tracking)
# - A.12.1.2: Change management (version pinning)
