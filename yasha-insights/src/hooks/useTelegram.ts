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
    // 1. Try generic WebApp.initData
    if (webApp?.initData) return webApp.initData;

    // 2. Fallback: Parse from hash OR search (query params)
    const hash = window.location.hash.slice(1);
    const search = window.location.search.slice(1);
    // Combine them to look everywhere
    const combined = hash + '&' + search;

    if (!combined) return '';

    // Function to extract valid initData from a string
    const extract = (str: string): string | null => {
      // Option A: data is in tgWebAppData param
      try {
        const params = new URLSearchParams(str);
        const data = params.get('tgWebAppData');
        if (data) {
          // If it looks encoded, decode it
          if (data.includes('%') || !data.includes('hash=')) {
            try { return decodeURIComponent(data); } catch (e) { return data; }
          }
          return data;
        }
      } catch (e) { }

      // Option B: manual split if URLSearchParams fails
      if (str.includes('tgWebAppData=')) {
        const parts = str.split('&');
        for (const part of parts) {
          if (part.startsWith('tgWebAppData=')) {
            let val = part.substring('tgWebAppData='.length);
            try { val = decodeURIComponent(val); } catch (e) { }
            return val;
          }
        }
      }

      // Option C: the string ITSELF is the data (contains user=... & hash=...)
      // Check for key indicators of init data
      if (str.includes('hash=') && (str.includes('user=') || str.includes('auth_date='))) {
        return str;
      }

      return null;
    };

    // Try parsing raw hash
    let result = extract(hash);
    if (result) return result;

    result = extract(search);
    if (result) return result;

    // Try decoding hash once and parsing
    try {
      const decoded = decodeURIComponent(hash);
      result = extract(decoded);
      if (result) return result;
    } catch (e) { }

    // Try decoding search
    try {
      const decoded = decodeURIComponent(search);
      result = extract(decoded);
      if (result) return result;
    } catch (e) { }

    // Last resort: Return raw hash if it's long, but this usually fails backend validation if keys are wrong.
    // But better than nothing for debug.
    if (hash.length > 50) return hash;

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
