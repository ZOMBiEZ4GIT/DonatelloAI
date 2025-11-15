"""
╔════════════════════════════════════════════════════════╗
║              Model Router Service                       ║
║         Intelligent Model Selection & Routing          ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Routes requests to optimal model provider
    - Balances cost, quality, and SLA requirements
    - Implements fallback strategies
    - Tracks model performance metrics

Cost Management:
    - Selects cheapest model meeting requirements
    - Estimates cost before generation
    - Enforces budget limits
"""

from decimal import Decimal
from typing import Optional

from app.core.config import settings
from app.core.logging import logger
from app.services.models.base import (
    BaseModelProvider,
    GenerationRequest,
    GenerationResult,
    ModelProvider,
)
from app.services.models.dalle3 import DALLE3Provider
from app.services.models.firefly import FireflyProvider
from app.services.models.sdxl import SDXLProvider


class ModelRouter:
    """
    Intelligent model router.

    Selects optimal model based on:
    - Cost requirements
    - Quality requirements
    - SLA requirements
    - Model availability
    """

    def __init__(self):
        """Initialize model router with available providers."""
        self.providers: dict[ModelProvider, BaseModelProvider] = {}

        # Initialize DALL-E 3 (Azure OpenAI)
        if settings.AZURE_OPENAI_API_KEY:
            self.providers[ModelProvider.AZURE_OPENAI_DALLE3] = DALLE3Provider(
                api_key=settings.AZURE_OPENAI_API_KEY,
                use_azure=True,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            )

        # Initialize Stable Diffusion XL (Replicate)
        if settings.REPLICATE_API_KEY:
            self.providers[ModelProvider.REPLICATE_SDXL] = SDXLProvider(
                api_key=settings.REPLICATE_API_KEY,
            )

        # Initialize Adobe Firefly
        if settings.ADOBE_CLIENT_ID and settings.ADOBE_CLIENT_SECRET:
            self.providers[ModelProvider.ADOBE_FIREFLY] = FireflyProvider(
                client_id=settings.ADOBE_CLIENT_ID,
                client_secret=settings.ADOBE_CLIENT_SECRET,
            )

        # TODO: Add Azure AI Image provider

        logger.info(
            "model_router_initialized",
            providers=[p.value for p in self.providers.keys()],
        )

    async def generate(
        self,
        request: GenerationRequest,
        preferred_provider: Optional[ModelProvider] = None,
        max_cost_aud: Optional[Decimal] = None,
    ) -> GenerationResult:
        """
        Generate image with optimal model selection.

        Args:
            request: Generation request
            preferred_provider: Preferred provider (optional)
            max_cost_aud: Maximum cost limit (optional)

        Returns:
            GenerationResult from selected provider
        """
        # Use preferred provider if specified and available
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]

            # Check cost limit
            if max_cost_aud:
                estimated_cost = provider.estimate_cost(request)
                if estimated_cost > max_cost_aud:
                    logger.warning(
                        "preferred_provider_exceeds_cost_limit",
                        provider=preferred_provider.value,
                        estimated_cost=float(estimated_cost),
                        max_cost=float(max_cost_aud),
                    )
                    # Fall through to automatic selection
                else:
                    return await provider.generate(request)

        # Automatic selection: Choose cheapest available provider
        cheapest_provider = None
        lowest_cost = None

        for provider_type, provider in self.providers.items():
            cost = provider.estimate_cost(request)

            if max_cost_aud and cost > max_cost_aud:
                continue

            if lowest_cost is None or cost < lowest_cost:
                lowest_cost = cost
                cheapest_provider = provider

        if cheapest_provider:
            logger.info(
                "model_router_selected_provider",
                provider=cheapest_provider.get_provider_name(),
                estimated_cost=float(lowest_cost),
            )
            return await cheapest_provider.generate(request)

        # No provider available within budget
        logger.error(
            "no_provider_within_budget",
            max_cost=float(max_cost_aud) if max_cost_aud else None,
        )
        return GenerationResult(
            success=False,
            image_urls=[],
            cost_aud=Decimal("0"),
            generation_time_ms=0,
            model_used="none",
            provider=ModelProvider.OPENAI_DALLE3,  # Default
            metadata={},
            error_message="No model provider available within budget constraints",
        )


# Global router instance
_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get global model router instance."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
