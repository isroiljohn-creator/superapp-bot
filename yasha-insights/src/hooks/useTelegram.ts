import { useEffect, useState, useCallback } from 'react';
import type { TelegramWebApp, TelegramUser } from '@/types/telegram';

export function useTelegram() {
  const [webApp, setWebApp] = useState<TelegramWebApp | null>(null);
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [colorScheme, setColorScheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    const tg = window.Telegram?.WebApp;

    if (tg) {
      setWebApp(tg);
      setUser(tg.initDataUnsafe?.user || null);
      setColorScheme(tg.colorScheme);
      setIsReady(true);

      // Expand the webapp
      tg.expand();
      tg.ready();

      // Set theme colors
      tg.setHeaderColor('#0f1012');
      tg.setBackgroundColor('#0f1012');

      // Listen for theme changes
      const handleThemeChanged = () => {
        setColorScheme(tg.colorScheme);
      };

      tg.onEvent('themeChanged', handleThemeChanged);

      return () => {
        tg.offEvent('themeChanged', handleThemeChanged);
      };
    } else {
      // Development mode - simulate Telegram environment
      console.warn('Telegram WebApp not available. Running in development mode.');
      setIsReady(true);
      setUser({
        id: 123456789,
        first_name: 'Dev',
        last_name: 'User',
        username: 'devuser',
      });
    }
  }, []);

  const getInitData = useCallback((): string => {
    if (webApp?.initData) return webApp.initData;

    // Fallback: Manually parse from hash
    let hash = window.location.hash.slice(1);
    if (!hash) return '';

    // Attempt to extract tgWebAppData if usage of standard param
    const params = new URLSearchParams(hash);
    if (params.has('tgWebAppData')) {
      return params.get('tgWebAppData') || '';
    }

    // Heuristic: If it contains "user=" or "user%3D", it's likely the data
    // Try decoding up to 2 times to handle double encoding
    let decoded = hash;
    let found = false;
    for (let i = 0; i < 2; i++) {
      if (decoded.includes('user=') || decoded.includes('auth_date=')) {
        found = true;
        break;
      }
      try {
        decoded = decodeURIComponent(decoded);
      } catch (e) { break; }
    }

    if (found || decoded.includes('user=') || decoded.includes('"id":')) {
      // Return the decoded version if it looks like initData
      // But keep original hash if decoding messed up the format expected by backend?
      // Backend expects standard URL encoded string: key=value&key=value
      // If we decoded it too much (e.g. turned %3D into =), parse_qsl might be fine or not.
      // SAFE BET: Return the one that matched, but ensure it's in key=value format.

      // If the original hash started with query_id or user, return it.
      // If it was encoded, returning decoded is better.
      return decoded;
    }

    // Last ditch: just return the hash if it's long enough
    if (hash.length > 100) return hash;

    return '';
  }, [webApp]);

  const hapticFeedback = useCallback(
    (type: 'light' | 'medium' | 'heavy' | 'success' | 'error' | 'warning') => {
      if (webApp?.HapticFeedback) {
        if (['success', 'error', 'warning'].includes(type)) {
          webApp.HapticFeedback.notificationOccurred(
            type as 'success' | 'error' | 'warning'
          );
        } else {
          webApp.HapticFeedback.impactOccurred(
            type as 'light' | 'medium' | 'heavy'
          );
        }
      }
    },
    [webApp]
  );

  const showAlert = useCallback(
    (message: string) => {
      if (webApp) {
        webApp.showAlert(message);
      } else {
        alert(message);
      }
    },
    [webApp]
  );

  const close = useCallback(() => {
    webApp?.close();
  }, [webApp]);

  return {
    webApp,
    user,
    isReady,
    colorScheme,
    getInitData,
    hapticFeedback,
    showAlert,
    close,
  };
}

export default useTelegram;
