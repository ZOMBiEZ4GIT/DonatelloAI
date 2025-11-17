import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { ApiError, ApiResponse } from '@/types';

class ApiClient {
  private client: AxiosInstance;
  private tokenProvider?: () => Promise<string | null>;

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Include cookies for CSRF protection
    });

    this.setupInterceptors();
  }

  /**
   * Set the token provider function
   * This will be called by MSAL to get the access token
   */
  setTokenProvider(provider: () => Promise<string | null>) {
    this.tokenProvider = provider;
  }

  private setupInterceptors() {
    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      async (config) => {
        // Get token from provider (MSAL)
        if (this.tokenProvider) {
          try {
            const token = await this.tokenProvider();
            if (token) {
              config.headers.Authorization = `Bearer ${token}`;
            }
          } catch (error) {
            console.error('Failed to get access token:', error);
          }
        }

        // Add CSRF token if available
        const csrfToken = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content;
        if (csrfToken) {
          config.headers['X-CSRF-Token'] = csrfToken;
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle errors globally
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error: AxiosError<ApiError>) => {
        if (error.response) {
          const { status, data } = error.response;

          // Handle specific error cases
          switch (status) {
            case 401:
              // Unauthorized - redirect to login
              window.dispatchEvent(new CustomEvent('auth:unauthorized'));
              break;
            case 403:
              // Forbidden - show permission error
              window.dispatchEvent(new CustomEvent('auth:forbidden'));
              break;
            case 429:
              // Rate limited
              window.dispatchEvent(new CustomEvent('api:rate-limited'));
              break;
            case 500:
            case 502:
            case 503:
              // Server error
              window.dispatchEvent(new CustomEvent('api:server-error', { detail: data }));
              break;
          }
        } else if (error.request) {
          // Network error
          window.dispatchEvent(new CustomEvent('api:network-error'));
        }

        return Promise.reject(error);
      }
    );
  }

  // Generic request method
  async request<T>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.client.request<ApiResponse<T>>(config);
    return response.data.data;
  }

  // GET request
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  // POST request
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  // PUT request
  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  }

  // PATCH request
  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PATCH', url, data });
  }

  // DELETE request
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  }

  // Upload file
  async upload<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      },
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
