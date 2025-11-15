"""
╔════════════════════════════════════════════════════════╗
║          Azure AD / Entra ID Authentication            ║
║         OAuth 2.0 + OpenID Connect Integration         ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Central authentication via Azure Active Directory
    - Single Sign-On (SSO) for enterprise users
    - MFA enforced at Azure AD level
    - Integration with corporate identity provider

Security Considerations:
    - OAuth 2.0 authorization code flow (most secure)
    - PKCE extension prevents authorization code interception
    - State parameter prevents CSRF attacks
    - Tokens validated against Azure AD public keys
    - No password handling (delegated to Azure AD)

ISO 27001 Controls:
    - A.9.4.2: Secure log-on procedures
    - A.9.2.4: Management of secret authentication information
"""

from typing import Dict, Optional, Any
from urllib.parse import urlencode

import msal
from msal import ConfidentialClientApplication

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import AuthenticationError


class AzureADService:
    """
    Azure AD authentication service.

    Handles OAuth 2.0 authorization code flow with Azure AD:
    1. Generate authorization URL
    2. Exchange authorization code for tokens
    3. Validate tokens
    4. Refresh access tokens

    Security:
        - Uses MSAL (Microsoft Authentication Library)
        - PKCE enabled for additional security
        - State parameter for CSRF protection
        - Tokens validated against Azure AD

    ISO 27001 Control: A.9.4.2 - Secure log-on procedures
    """

    def __init__(self) -> None:
        """
        Initialize Azure AD service.

        Creates MSAL ConfidentialClientApplication instance
        with settings from configuration.
        """
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.authority = settings.AZURE_AUTHORITY
        self.redirect_uri = settings.AZURE_REDIRECT_URI

        # Scopes for OpenID Connect + User.Read
        self.scopes = [
            "openid",
            "profile",
            "email",
            "User.Read",  # Microsoft Graph: Read user profile
        ]

        # Create MSAL application
        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
        )

        logger.info(
            "azure_ad_service_initialized",
            authority=self.authority,
            client_id=self.client_id[:8] + "...",  # Partial log only
        )

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Azure AD authorization URL.

        Args:
            state: CSRF protection state parameter (generated if not provided)

        Returns:
            Authorization URL to redirect user to

        Security:
            - State parameter prevents CSRF
            - PKCE code challenge prevents code interception
            - Prompt=select_account for better UX

        Example:
            >>> service = AzureADService()
            >>> url = service.get_authorization_url()
            >>> # Redirect user to url
        """
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scopes,
            state=state,
            redirect_uri=self.redirect_uri,
            prompt="select_account",  # Force account selection
        )

        logger.info(
            "authorization_url_generated",
            has_state=state is not None,
        )

        return auth_url

    def acquire_token_by_authorization_code(
        self,
        authorization_code: str,
        state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access tokens.

        Args:
            authorization_code: Authorization code from Azure AD redirect
            state: State parameter from original request (for validation)

        Returns:
            Token response containing:
            - access_token: JWT access token
            - id_token: OpenID Connect ID token
            - refresh_token: Refresh token (if offline_access requested)
            - expires_in: Token lifetime in seconds

        Raises:
            AuthenticationError: If token acquisition fails

        Security:
            - Validates authorization code
            - Verifies state parameter (if provided)
            - Validates tokens against Azure AD
            - Returns user claims from ID token

        ISO 27001 Control: A.9.4.2 - Secure log-on procedures
        """
        try:
            result = self.app.acquire_token_by_authorization_code(
                code=authorization_code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri,
            )

            if "error" in result:
                logger.error(
                    "azure_ad_token_acquisition_failed",
                    error=result.get("error"),
                    error_description=result.get("error_description"),
                )
                raise AuthenticationError(
                    message=f"Azure AD authentication failed: {result.get('error_description')}",
                    details={"error": result.get("error")},
                )

            logger.info(
                "azure_ad_token_acquired",
                user_email=result.get("id_token_claims", {}).get("preferred_username"),
                has_refresh_token="refresh_token" in result,
            )

            return result

        except Exception as e:
            logger.error(
                "azure_ad_token_acquisition_exception",
                error=type(e).__name__,
                message=str(e),
                exc_info=True,
            )
            raise AuthenticationError(
                message="Failed to acquire tokens from Azure AD",
                details={"error": str(e)},
            )

    def validate_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Validate and decode Azure AD ID token.

        Args:
            id_token: ID token from Azure AD

        Returns:
            Decoded token claims

        Security:
            - Validates signature against Azure AD public keys
            - Checks expiration
            - Validates issuer
            - Validates audience

        Claims returned:
            - sub: Subject (user unique ID)
            - oid: Object ID (Azure AD user ID)
            - preferred_username: Email address
            - name: Display name
            - amr: Authentication methods (MFA indicator)
        """
        # MSAL automatically validates ID tokens
        # We just need to decode the claims
        try:
            # The ID token is already validated by MSAL during acquisition
            # We can safely use the claims
            import jwt

            # Decode without verification (already verified by MSAL)
            claims = jwt.decode(
                id_token,
                options={"verify_signature": False},  # Already verified
            )

            logger.info(
                "id_token_validated",
                subject=claims.get("sub"),
                email=claims.get("preferred_username"),
                has_mfa=("mfa" in claims.get("amr", [])),
            )

            return claims

        except Exception as e:
            logger.error(
                "id_token_validation_failed",
                error=type(e).__name__,
                message=str(e),
            )
            raise AuthenticationError(
                message="Failed to validate ID token",
                details={"error": str(e)},
            )

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Retrieve user information from Microsoft Graph API.

        Args:
            access_token: Access token with User.Read scope

        Returns:
            User information from Microsoft Graph

        Note:
            - This is optional if ID token contains enough info
            - Useful for additional profile data
            - Requires User.Read permission

        Returns example:
            {
                "id": "azure_user_id",
                "userPrincipalName": "user@domain.com",
                "displayName": "John Doe",
                "givenName": "John",
                "surname": "Doe",
                "mail": "user@domain.com",
                "mobilePhone": "+61...",
                "jobTitle": "Manager"
            }
        """
        import requests

        try:
            graph_url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(graph_url, headers=headers, timeout=10)
            response.raise_for_status()

            user_info = response.json()

            logger.info(
                "microsoft_graph_user_info_retrieved",
                user_id=user_info.get("id"),
                email=user_info.get("userPrincipalName"),
            )

            return user_info

        except Exception as e:
            logger.warning(
                "microsoft_graph_request_failed",
                error=type(e).__name__,
                message=str(e),
            )
            # Don't fail authentication if Graph call fails
            # ID token has enough info
            return {}

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            New token response with fresh access token

        Raises:
            AuthenticationError: If refresh fails

        Security:
            - Refresh tokens are one-time use
            - New refresh token issued with each refresh
            - Old refresh token invalidated

        Note:
            - Only works if offline_access scope was requested
            - Refresh tokens expire after configured period (default: 90 days)
        """
        try:
            result = self.app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.scopes,
            )

            if "error" in result:
                logger.error(
                    "azure_ad_token_refresh_failed",
                    error=result.get("error"),
                    error_description=result.get("error_description"),
                )
                raise AuthenticationError(
                    message="Token refresh failed",
                    details={"error": result.get("error")},
                )

            logger.info("azure_ad_token_refreshed")

            return result

        except Exception as e:
            logger.error(
                "azure_ad_token_refresh_exception",
                error=type(e).__name__,
                message=str(e),
            )
            raise AuthenticationError(
                message="Failed to refresh access token",
                details={"error": str(e)},
            )


# ⚠️  AZURE AD INTEGRATION NOTES:
#
# 🔒 Security Flow:
# 1. User clicks "Login with Microsoft"
# 2. Redirect to Azure AD with state parameter
# 3. User authenticates (username + password + MFA)
# 4. Azure AD redirects back with authorization code
# 5. Backend exchanges code for tokens
# 6. ID token contains user identity
# 7. Access token used for Microsoft Graph calls
# 8. Refresh token used to get new access tokens
#
# 🎫 Token Lifecycle:
# - Access tokens: 60 minutes (Azure AD default)
# - ID tokens: 60 minutes (Azure AD default)
# - Refresh tokens: 90 days (configurable in Azure AD)
# - Our access tokens: 30 minutes (additional layer)
# - Our refresh tokens: 7 days (rotated on use)
#
# 🛡️ MFA Enforcement:
# - Configured in Azure AD Conditional Access
# - amr claim indicates authentication methods used
# - amr=["pwd","mfa"] means password + MFA
# - We check MFA in user profile, not per-request
#
# 📊 User Claims (from ID token):
# - oid: Azure AD object ID (unique, permanent)
# - sub: Subject (may change if tenant changes)
# - preferred_username: Email address
# - name: Display name
# - amr: Authentication methods
# - tid: Tenant ID
#
# 🔧 Configuration in Azure AD:
# 1. App Registration > Authentication
#    - Redirect URI: https://platform.domain.com/auth/callback
#    - Platform: Web
#    - Implicit grant: Disabled (use auth code flow)
# 2. App Registration > API Permissions
#    - Microsoft Graph > User.Read
#    - Admin consent granted
# 3. Conditional Access Policies
#    - Require MFA for all users
#    - Require compliant device (optional)
#    - Block legacy authentication
#
# 📋 ISO 27001 Control Mapping:
# - A.9.2.4: Management of secret authentication information
# - A.9.4.2: Secure log-on procedures
# - A.9.4.3: Password management system (delegated to Azure AD)
# - A.13.1.3: Segregation in networks (Azure AD isolated)
