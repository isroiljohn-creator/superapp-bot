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
    return webApp?.initData || '';
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
