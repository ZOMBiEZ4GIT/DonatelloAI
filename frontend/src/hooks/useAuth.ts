import { useEffect } from 'react';
import { useMsal } from '@azure/msal-react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store';
import { authService } from '@/services';
import { QUERY_KEYS } from '@/utils/constants';

export const useAuth = () => {
  const { instance, accounts } = useMsal();
  const { user, isAuthenticated, setUser, setLoading, setError, clearAuth } = useAuthStore();

  // Fetch user profile from backend
  const { data: userData, isLoading, error } = useQuery({
    queryKey: QUERY_KEYS.AUTH_USER,
    queryFn: () => authService.getCurrentUser(),
    enabled: accounts.length > 0,
    retry: 1,
  });

  useEffect(() => {
    if (userData) {
      setUser(userData);
    } else if (accounts.length === 0) {
      clearAuth();
    }
  }, [userData, accounts, setUser, clearAuth]);

  useEffect(() => {
    setLoading(isLoading);
  }, [isLoading, setLoading]);

  useEffect(() => {
    if (error) {
      setError(error instanceof Error ? error.message : 'Authentication failed');
    }
  }, [error, setError]);

  const login = async () => {
    try {
      await authService.loginPopup();
    } catch (error) {
      console.error('Login failed:', error);
      setError(error instanceof Error ? error.message : 'Login failed');
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      clearAuth();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const getAccessToken = async () => {
    return authService.getAccessToken();
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error: useAuthStore((state) => state.error),
    login,
    logout,
    getAccessToken,
    accounts,
    instance,
  };
};
