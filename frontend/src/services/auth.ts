import { PublicClientApplication, AccountInfo, InteractionRequiredAuthError } from '@azure/msal-browser';
import { AZURE_CONFIG } from '@/utils/constants';
import { apiClient } from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import { AuthUser } from '@/types';

const msalConfig = {
  auth: {
    clientId: AZURE_CONFIG.clientId,
    authority: `https://login.microsoftonline.com/${AZURE_CONFIG.tenantId}`,
    redirectUri: AZURE_CONFIG.redirectUri,
  },
  cache: {
    cacheLocation: 'sessionStorage', // More secure than localStorage
    storeAuthStateInCookie: false,
  },
};

const loginRequest = {
  scopes: ['User.Read', 'openid', 'profile', 'email'],
};

export class AuthService {
  private msalInstance: PublicClientApplication;

  constructor() {
    this.msalInstance = new PublicClientApplication(msalConfig);
  }

  async initialize(): Promise<void> {
    await this.msalInstance.initialize();
    await this.msalInstance.handleRedirectPromise();
  }

  /**
   * Get the MSAL instance
   */
  getMsalInstance(): PublicClientApplication {
    return this.msalInstance;
  }

  /**
   * Get all accounts
   */
  getAllAccounts(): AccountInfo[] {
    return this.msalInstance.getAllAccounts();
  }

  /**
   * Get the active account
   */
  getActiveAccount(): AccountInfo | null {
    return this.msalInstance.getActiveAccount();
  }

  /**
   * Login with popup
   */
  async loginPopup(): Promise<AccountInfo> {
    const response = await this.msalInstance.loginPopup(loginRequest);
    this.msalInstance.setActiveAccount(response.account);
    return response.account;
  }

  /**
   * Login with redirect
   */
  async loginRedirect(): Promise<void> {
    await this.msalInstance.loginRedirect(loginRequest);
  }

  /**
   * Logout
   */
  async logout(): Promise<void> {
    const account = this.getActiveAccount();
    if (account) {
      await this.msalInstance.logoutPopup({ account });
    }
  }

  /**
   * Get access token silently
   */
  async getAccessToken(): Promise<string | null> {
    const account = this.getActiveAccount();
    if (!account) {
      return null;
    }

    try {
      const response = await this.msalInstance.acquireTokenSilent({
        ...loginRequest,
        account,
      });
      return response.accessToken;
    } catch (error) {
      if (error instanceof InteractionRequiredAuthError) {
        // Token expired or needs interaction, try popup
        try {
          const response = await this.msalInstance.acquireTokenPopup(loginRequest);
          return response.accessToken;
        } catch (popupError) {
          console.error('Failed to acquire token via popup:', popupError);
          return null;
        }
      }
      console.error('Failed to acquire token silently:', error);
      return null;
    }
  }

  /**
   * Get current user profile from backend
   */
  async getCurrentUser(): Promise<AuthUser> {
    return apiClient.get<AuthUser>(API_ENDPOINTS.ME);
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.getAllAccounts().length > 0;
  }
}

// Export singleton instance
export const authService = new AuthService();

// Set up token provider for API client
apiClient.setTokenProvider(() => authService.getAccessToken());
