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
        // Token invalid, clear it and continue to normal auth
        console.warn('Stored token invalid, re-authenticating...');
        api.clearToken();
        // Do NOT return here, allow fall-through to initData auth
      }
    }

    // No initData
    if (!initData) {
      if (import.meta.env.DEV) {
        console.warn('No Telegram initData. Using development mode.');
        setAuthState({
          isAuthenticated: true,
          isLoading: false,
          error: null,
          user: telegramUser,
        });
        return;
      } else {
        // Production: Require Telegram environment
        const tgType = typeof window.Telegram;
        const waType = window.Telegram?.WebApp ? 'Obj' : 'Undefined';
        const hashLen = window.location.hash.length;
        const hashStart = window.location.hash.slice(0, 50);
        const unsafeUser = window.Telegram?.WebApp?.initDataUnsafe?.user ? 'Yes' : 'No';

        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          error: `Access Denied. Open in Telegram.\nDebug: TG=${tgType}, WA=${waType}, InitData=${initData.length}, HashLen=${hashLen}, HashStart=${hashStart}, UnsafeUser=${unsafeUser}`,
          user: null,
        });
        return;
      }
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
