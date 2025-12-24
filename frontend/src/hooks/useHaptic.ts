import { useCallback } from 'react';

export type HapticType = 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' | 'success' | 'warning' | 'error';

export const useHaptic = () => {
  const vibrate = useCallback((type: HapticType = 'light') => {
    const tg = (window as any).Telegram?.WebApp;
    if (!tg?.hapticFeedback) return;

    switch (type) {
      case 'light':
      case 'medium':
      case 'heavy':
      case 'rigid':
      case 'soft':
        tg.hapticFeedback.impactOccurred(type);
        break;
      case 'success':
      case 'warning':
      case 'error':
        tg.hapticFeedback.notificationOccurred(type);
        break;
    }
  }, []);

  return { vibrate };
};
