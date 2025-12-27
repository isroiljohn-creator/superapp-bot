import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { useTelegram } from './useTelegram';
import type { TelegramUser } from '@/types/telegram';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  user: TelegramUser | null;
}

export function useAuth() {
  const { getInitData, user: telegramUser, isReady } = useTelegram();
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    error: null,
    user: null,
  });

  const authenticate = useCallback(async () => {
    const initData = getInitData();

    // Check if already authenticated
    const existingToken = api.getToken();
    if (existingToken) {
      // Validate token by making a test request
      try {
        await api.getOverview();
        setAuthState({
          isAuthenticated: true,
          isLoading: false,
          error: null,
          user: telegramUser,
        });
        return;
      } catch (error: unknown) {
        // Token invalid, clear it
        api.clearToken();
        const apiError = error as { status?: number; response?: { data?: { detail?: string } } };
        if (apiError.status === 403 || apiError.response?.data?.detail) {
          setAuthState({
            isAuthenticated: false,
            isLoading: false,
            error: apiError.response?.data?.detail || 'Access Denied. Admin privileges required.',
            user: null,
          });
          return;
        }
      }
    }

    // No initData in development mode - use mock auth
    if (!initData) {
      console.warn('No Telegram initData. Using development mode.');
      // In dev mode, simulate authentication
      setAuthState({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        user: telegramUser,
      });
      return;
    }

    try {
      await api.authenticate(initData);
      setAuthState({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        user: telegramUser,
      });
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: { detail?: string } }; status?: number; detail?: string };
      let errorMessage = 'Authentication failed';

      if (apiError.response?.data?.detail) {
        errorMessage = apiError.response.data.detail;
      } else if (apiError.status === 403) {
        errorMessage = 'Access Denied. Admin privileges required.';
      } else if (apiError.detail) {
        errorMessage = apiError.detail;
      }

      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        error: errorMessage,
        user: null,
      });
    }
  }, [getInitData, telegramUser]);

  const logout = useCallback(() => {
    api.clearToken();
    setAuthState({
      isAuthenticated: false,
      isLoading: false,
      error: null,
      user: null,
    });
  }, []);

  useEffect(() => {
    if (isReady) {
      authenticate();
    }
  }, [isReady, authenticate]);

  return {
    ...authState,
    authenticate,
    logout,
  };
}

export default useAuth;
