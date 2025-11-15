"""
╔════════════════════════════════════════════════════════╗
║            Application Configuration                    ║
║         🔒 Security-Critical Settings                  ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Central configuration for all application settings
    - Loads secrets from Azure Key Vault in production
    - Validates all environment variables at startup

Security Considerations:
    - All secrets loaded from environment variables (never hardcoded)
    - Azure Key Vault integration for production secrets
    - Pydantic validation ensures type safety
    - Sensitive values masked in logs

ISO 27001 Controls:
    - A.9.4.5: Access control to source code
    - A.12.4.1: Event logging
    - A.14.2.1: Secure development policy

Modifications:
    - Add new settings to appropriate section below
    - Update .env.example when adding new env vars
    - Never commit actual secrets to repository
"""

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings are validated at startup. Missing required settings
    will cause the application to fail fast with clear error messages.

    Security Notes:
        - Secrets are loaded from Azure Key Vault in production
        - Local development uses .env file (gitignored)
        - Validation prevents misconfiguration
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🌍 Environment Configuration                            │
    # └─────────────────────────────────────────────────────────┘
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )
    DEBUG: bool = Field(default=False, description="Enable debug mode (NEVER in production)")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🚀 Application Settings                                 │
    # └─────────────────────────────────────────────────────────┘
    APP_NAME: str = Field(
        default="Enterprise Image Generation Platform",
        description="Application name",
    )
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 route prefix")

    BACKEND_URL: str = Field(default="http://localhost:8000", description="Backend URL")
    FRONTEND_URL: str = Field(default="http://localhost:5173", description="Frontend URL")

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🔐 Azure Active Directory / Entra ID                    │
    # └─────────────────────────────────────────────────────────┘
    AZURE_TENANT_ID: str = Field(..., description="Azure AD tenant ID (required)")
    AZURE_CLIENT_ID: str = Field(..., description="Azure AD client ID (required)")
    AZURE_CLIENT_SECRET: str = Field(..., description="Azure AD client secret (required)")
    AZURE_AUTHORITY: str = Field(..., description="Azure AD authority URL")
    AZURE_REDIRECT_URI: str = Field(..., description="OAuth redirect URI")

    REQUIRE_MFA: bool = Field(default=True, description="Require multi-factor authentication")
    MFA_GRACE_PERIOD_DAYS: int = Field(
        default=7,
        description="Days allowed without MFA before enforcement",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🗄️ Database Configuration                               │
    # └─────────────────────────────────────────────────────────┘
    DATABASE_URL: str = Field(..., description="Database connection URL (required)")
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Max connections above pool size")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Pool connection timeout (seconds)")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries (debug only)")

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🌐 Azure Cosmos DB (Audit Logs)                         │
    # └─────────────────────────────────────────────────────────┘
    COSMOS_ENDPOINT: str = Field(..., description="Cosmos DB endpoint (required)")
    COSMOS_KEY: str = Field(..., description="Cosmos DB primary key (required)")
    COSMOS_DATABASE_NAME: str = Field(
        default="eig-audit-logs",
        description="Cosmos DB database name",
    )
    COSMOS_CONTAINER_NAME: str = Field(
        default="audit-events",
        description="Cosmos DB container name",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ 💾 Azure Blob Storage (Images)                          │
    # └─────────────────────────────────────────────────────────┘
    AZURE_STORAGE_ACCOUNT_NAME: str = Field(..., description="Storage account name (required)")
    AZURE_STORAGE_ACCOUNT_KEY: str = Field(..., description="Storage account key (required)")
    AZURE_STORAGE_CONTAINER_NAME: str = Field(
        default="generated-images",
        description="Blob container name",
    )
    AZURE_STORAGE_CDN_ENDPOINT: str = Field(
        default="",
        description="CDN endpoint for image delivery",
    )

    STORAGE_HOT_DAYS: int = Field(default=30, description="Days to keep in hot tier")
    STORAGE_COOL_DAYS: int = Field(default=60, description="Days before moving to cool tier")
    STORAGE_ARCHIVE_DAYS: int = Field(default=90, description="Days before archiving")

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🔑 Azure Key Vault                                      │
    # └─────────────────────────────────────────────────────────┘
    KEY_VAULT_URL: str = Field(..., description="Key Vault URL (required)")
    KEY_VAULT_TENANT_ID: str = Field(..., description="Key Vault tenant ID")
    KEY_VAULT_CLIENT_ID: str = Field(default="", description="Managed identity client ID")
    KEY_VAULT_CLIENT_SECRET: str = Field(default="", description="Client secret (local dev only)")

    # ┌─────────────────────────────────────────────────────────┐
    # │ 💰 Cost Management                                      │
    # └─────────────────────────────────────────────────────────┘
    DEFAULT_DEPARTMENT_BUDGET_AUD: float = Field(
        default=5000.00,
        description="Default monthly department budget (AUD)",
    )
    BUDGET_ENFORCEMENT: Literal["hard", "soft", "warn"] = Field(
        default="hard",
        description="Budget enforcement mode",
    )
    COST_ALERT_THRESHOLD_PERCENT: int = Field(
        default=80,
        description="Alert when budget reaches this percentage",
    )
    MAX_COST_PER_IMAGE_AUD: float = Field(
        default=0.50,
        description="Maximum allowed cost per image (safety limit)",
    )

    # Model costs (AUD per image)
    COST_DALLE3: float = Field(default=0.08, description="DALL-E 3 cost per image")
    COST_SDXL: float = Field(default=0.02, description="Stable Diffusion XL cost per image")
    COST_FIREFLY: float = Field(default=0.10, description="Adobe Firefly cost per image")
    COST_AZURE_AI: float = Field(default=0.05, description="Azure AI Image cost per image")

    # ┌─────────────────────────────────────────────────────────┐
    # │ ⏱️ Rate Limiting                                        │
    # └─────────────────────────────────────────────────────────┘
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_FREE_TIER: int = Field(default=10, description="Free tier: requests per hour")
    RATE_LIMIT_STANDARD: int = Field(default=100, description="Standard: requests per hour")
    RATE_LIMIT_ENTERPRISE: int = Field(default=1000, description="Enterprise: requests per hour")
    RATE_LIMIT_POWER_USER: int = Field(default=500, description="Power user: requests per hour")

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🔒 Security Settings                                    │
    # └─────────────────────────────────────────────────────────┘
    SECRET_KEY: str = Field(..., min_length=32, description="Secret key for JWT (required, min 32 chars)")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration (minutes)",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration (days)",
    )

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")

    # Encryption
    ENCRYPTION_KEY: str = Field(..., description="Fernet encryption key (required)")
    HASH_ALGORITHM: str = Field(default="bcrypt", description="Password hashing algorithm")
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt rounds (10-14 recommended)")

    # ┌─────────────────────────────────────────────────────────┐
    # │ 📊 Monitoring & Logging                                 │
    # └─────────────────────────────────────────────────────────┘
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = Field(
        default="",
        description="Application Insights connection string",
    )
    APPLICATIONINSIGHTS_INSTRUMENTATION_KEY: str = Field(
        default="",
        description="Application Insights instrumentation key",
    )

    LOG_ANALYTICS_WORKSPACE_ID: str = Field(default="", description="Log Analytics workspace ID")
    LOG_ANALYTICS_SHARED_KEY: str = Field(default="", description="Log Analytics shared key")

    ENABLE_SENTINEL_INTEGRATION: bool = Field(
        default=True,
        description="Enable Azure Sentinel integration",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🔄 Background Jobs                                      │
    # └─────────────────────────────────────────────────────────┘
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL",
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/1",
        description="Celery result backend",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🔍 PII Detection & Content Moderation                   │
    # └─────────────────────────────────────────────────────────┘
    ENABLE_PII_DETECTION: bool = Field(default=True, description="Enable PII detection")
    PII_DETECTION_THRESHOLD: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="PII detection confidence threshold",
    )
    PII_ACTION: Literal["block", "warn", "anonymize"] = Field(
        default="block",
        description="Action when PII detected",
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ 📋 Compliance & Audit                                   │
    # └─────────────────────────────────────────────────────────┘
    AUDIT_LOG_RETENTION_DAYS: int = Field(
        default=2555,
        description="Audit log retention (7 years = 2555 days)",
    )
    ENABLE_IMMUTABLE_AUDIT_LOGS: bool = Field(
        default=True,
        description="Enable immutable audit logs",
    )
    DATA_RESIDENCY_REGION: str = Field(
        default="australiaeast",
        description="Enforce data residency region",
    )

    ISO27001_MODE: bool = Field(default=True, description="Enable ISO 27001 compliance mode")
    GDPR_MODE: bool = Field(default=True, description="Enable GDPR compliance mode")
    PRIVACY_ACT_MODE: bool = Field(default=True, description="Enable Privacy Act compliance mode")

    # ┌─────────────────────────────────────────────────────────┐
    # │ 🧪 Development & Testing                                │
    # └─────────────────────────────────────────────────────────┘
    TESTING_MODE: bool = Field(default=False, description="Enable testing mode")
    MOCK_EXTERNAL_APIS: bool = Field(
        default=False,
        description="Mock external APIs for development",
    )
    ENABLE_API_DOCS: bool = Field(default=True, description="Enable API documentation")

    # Feature flags
    FEATURE_BATCH_GENERATION: bool = Field(default=True, description="Enable batch generation")
    FEATURE_PROMPT_TEMPLATES: bool = Field(default=True, description="Enable prompt templates")
    FEATURE_CUSTOM_STYLES: bool = Field(default=True, description="Enable custom styles")
    FEATURE_API_ACCESS: bool = Field(default=True, description="Enable API access")

    # ┌─────────────────────────────────────────────────────────┐
    # │ ✅ Validators                                           │
    # └─────────────────────────────────────────────────────────┘

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment setting."""
        if v not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be development, staging, or production")
        return v

    @field_validator("DEBUG")
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        """Ensure DEBUG is False in production."""
        if info.data.get("ENVIRONMENT") == "production" and v is True:
            raise ValueError("DEBUG must be False in production environment")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v == "generate-a-secure-random-key-here-min-32-chars":
            raise ValueError("SECRET_KEY must be changed from default value")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings

    Notes:
        - Settings are cached for performance
        - Clear cache if settings need to be reloaded
        - In production, secrets are loaded from Azure Key Vault
    """
    return Settings()


# Global settings instance
settings = get_settings()

# ⚠️  SECURITY NOTES:
# - Never log sensitive settings values
# - All secrets must be loaded from environment variables
# - Production uses Azure Key Vault for secret management
# - Local development uses .env file (gitignored)
#
# 📋 ISO 27001 Control Mapping:
# - A.9.4.5: Access control to source code
# - A.12.4.1: Event logging
# - A.14.2.1: Secure development policy
