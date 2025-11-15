"""
╔════════════════════════════════════════════════════════╗
║         Adobe Firefly Model Provider                   ║
║           Enterprise-Grade AI Image Generation         ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Enterprise-grade quality and licensing
    - Commercial-safe content generation
    - Adobe Creative Cloud integration ready
    - Premium pricing for premium quality

Cost Structure (AUD):
    - Standard: $0.10 per image
    - Premium: $0.15 per image
    - Most expensive but commercially safe

Licensing Benefits:
    - Commercial usage rights included
    - IP indemnification from Adobe
    - Safe for enterprise customers
    - No attribution required

Technical Details:
    - API: Adobe Firefly REST API
    - Auth: OAuth 2.0 client credentials
    - Timeout: 60 seconds
    - Sizes: Multiple aspect ratios supported

ISO 27001 Controls:
    - A.12.6.1: Secure API integration
    - A.14.2.1: Secure development policy
    - A.18.1.2: Intellectual property rights (licensing)
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


class FireflyProvider(BaseModelProvider):
    """
    Adobe Firefly provider.

    Features:
        - Enterprise-grade image quality
        - Commercial licensing included
        - IP indemnification
        - Creative Cloud integration ready

    Licensing:
        - Full commercial usage rights
        - No attribution required
        - Adobe IP indemnification
        - Safe for enterprise customers

    Cost Optimization:
        - Most expensive option
        - Recommended for customer-facing content
        - Critical commercial applications
        - Risk-averse departments
    """

    # Adobe Firefly API endpoints
    FIREFLY_API_BASE = "https://firefly-api.adobe.io/v2"
    GENERATE_ENDPOINT = f"{FIREFLY_API_BASE}/images/generate"
    TOKEN_ENDPOINT = "https://ims-na1.adobelogin.com/ims/token/v3"

    # Cost per image in AUD
    COST_STANDARD_AUD = Decimal("0.10")
    COST_PREMIUM_AUD = Decimal("0.15")

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        timeout_seconds: int = 60,
    ):
        """
        Initialize Adobe Firefly provider.

        Args:
            client_id: Adobe API client ID
            client_secret: Adobe API client secret
            timeout_seconds: Max wait time for generation (default: 60s)
        """
        super().__init__(
            cost_per_image_aud=self.COST_STANDARD_AUD,
            timeout_seconds=timeout_seconds,
        )
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
        )

        logger.info(
            "firefly_provider_initialized",
            timeout_seconds=timeout_seconds,
        )

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Adobe Firefly"

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
            self.COST_PREMIUM_AUD
            if request.quality == ImageQuality.HD
            else self.COST_STANDARD_AUD
        )

        total_cost = cost_per_image * request.num_images

        logger.debug(
            "firefly_cost_estimated",
            num_images=request.num_images,
            quality=request.quality.value,
            cost_per_image_aud=float(cost_per_image),
            total_cost_aud=float(total_cost),
        )

        return total_cost

    async def _get_access_token(self) -> str:
        """
        Get Adobe API access token (with caching).

        Returns:
            Valid access token

        Raises:
            httpx.HTTPError: If token request fails
        """
        # Return cached token if still valid
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        # Request new token
        logger.debug("firefly_requesting_token")

        response = await self.client.post(
            self.TOKEN_ENDPOINT,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "openid,creative_sdk",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = time.time() + expires_in - 60  # 60s buffer

        logger.info(
            "firefly_token_obtained",
            expires_in=expires_in,
        )

        return self.access_token

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate images using Adobe Firefly.

        Args:
            request: Generation request

        Returns:
            Generation result with image URLs and metadata

        Flow:
            1. Obtain OAuth access token
            2. Submit generation request
            3. Extract image URLs from response
            4. Calculate cost and generation time
        """
        start_time = time.time()
        image_urls = []

        try:
            # Get access token
            access_token = await self._get_access_token()

            # Map our size enum to Firefly dimensions
            width, height = self._map_size_to_dimensions(request.size)

            # Prepare Firefly request
            firefly_request = {
                "prompt": request.prompt,
                "n": request.num_images,
                "size": {
                    "width": width,
                    "height": height,
                },
                "contentClass": "art" if request.quality == ImageQuality.HD else "photo",
                "style": {
                    "strength": 60 if request.quality == ImageQuality.HD else 40,
                },
            }

            logger.info(
                "firefly_generating",
                prompt_length=len(request.prompt),
                num_images=request.num_images,
                size=request.size.value,
                quality=request.quality.value,
            )

            # Submit generation request
            response = await self.client.post(
                self.GENERATE_ENDPOINT,
                json=firefly_request,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "x-api-key": self.client_id,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()

            result_data = response.json()

            # Extract image URLs
            if "outputs" in result_data:
                for output in result_data["outputs"]:
                    if "image" in output and "url" in output["image"]:
                        image_urls.append(output["image"]["url"])

            if not image_urls:
                logger.error(
                    "firefly_no_images",
                    response_data=result_data,
                )
                return self._error_result(
                    "Firefly returned no images",
                    start_time,
                )

            # Calculate cost and time
            generation_time_ms = int((time.time() - start_time) * 1000)
            actual_cost = self.estimate_cost(request)

            logger.info(
                "firefly_generation_success",
                num_images=len(image_urls),
                generation_time_ms=generation_time_ms,
                cost_aud=float(actual_cost),
            )

            return GenerationResult(
                success=True,
                image_urls=image_urls,
                cost_aud=actual_cost,
                generation_time_ms=generation_time_ms,
                model_used="adobe-firefly",
                provider=ModelProvider.ADOBE_FIREFLY,
                metadata={
                    "width": width,
                    "height": height,
                    "content_class": firefly_request["contentClass"],
                    "style_strength": firefly_request["style"]["strength"],
                    "commercial_license": True,
                    "ip_indemnification": True,
                },
            )

        except httpx.HTTPError as e:
            logger.error(
                "firefly_http_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return self._error_result(
                f"Firefly API error: {str(e)}",
                start_time,
            )

        except Exception as e:
            logger.error(
                "firefly_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return self._error_result(
                f"Unexpected error: {str(e)}",
                start_time,
            )

    def _map_size_to_dimensions(self, size: ImageSize) -> tuple[int, int]:
        """
        Map ImageSize enum to Firefly dimensions.

        Firefly supports various aspect ratios and sizes.

        Args:
            size: ImageSize enum

        Returns:
            (width, height) tuple
        """
        size_map = {
            ImageSize.SMALL: (1024, 1024),  # 1:1 square
            ImageSize.MEDIUM: (1408, 1024),  # 4:3 landscape
            ImageSize.LARGE: (1792, 1024),  # 16:9 landscape
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
            model_used="adobe-firefly",
            provider=ModelProvider.ADOBE_FIREFLY,
            metadata={},
            error_message=error_message,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources."""
        await self.client.aclose()


# ⚠️  COST ANALYSIS:
#
# 💰 Adobe Firefly Pricing:
# Standard quality: $0.10 AUD per image (~$0.075 USD)
# Premium quality: $0.15 AUD per image (~$0.11 USD)
#
# 📊 Comparison vs Other Providers:
# DALL-E 3: $0.08 AUD standard, $0.12 AUD HD
# SDXL: $0.02 AUD standard, $0.04 AUD HD
# Firefly: $0.10 AUD standard, $0.15 AUD HD (most expensive)
#
# 🏆 Firefly Advantages:
# ✅ Full commercial usage rights included
# ✅ Adobe IP indemnification
# ✅ No attribution required
# ✅ Enterprise-grade licensing
# ✅ Safe for customer-facing content
# ✅ Creative Cloud integration ready
#
# ⚠️  When to Use Firefly:
# - Customer-facing marketing materials
# - Commercial products/services
# - Legal risk-averse projects
# - Enterprise compliance requirements
# - High-value commercial applications
#
# 🎯 Recommended For:
# - Marketing departments
# - Product teams
# - Customer-facing content
# - Commercial applications
# - Enterprises requiring IP protection
#
# 📋 ISO 27001 Control Mapping:
# - A.12.6.1: Management of technical vulnerabilities (secure API)
# - A.14.2.1: Secure development policy (cost tracking)
# - A.18.1.2: Intellectual property rights (commercial licensing)
# - A.15.1.1: Supplier agreements (Adobe terms)
