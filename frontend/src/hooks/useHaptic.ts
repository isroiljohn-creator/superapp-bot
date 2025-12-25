import { Haptics, ImpactStyle, NotificationType } from '@capacitor/haptics';

// Vibratsiya hook - barcha tugmalar uchun
export const useHaptic = () => {
  const vibrate = async (pattern: 'light' | 'medium' | 'heavy' | 'success' | 'error' | 'selection' = 'light') => {
    try {
      switch (pattern) {
        case 'light':
          await Haptics.impact({ style: ImpactStyle.Light });
          break;
        case 'medium':
          await Haptics.impact({ style: ImpactStyle.Medium });
          break;
        case 'heavy':
          await Haptics.impact({ style: ImpactStyle.Heavy });
          break;
        case 'success':
          await Haptics.notification({ type: NotificationType.Success });
          break;
        case 'error':
          await Haptics.notification({ type: NotificationType.Error });
          break;
        case 'selection':
          await Haptics.selectionStart();
          break;
      }
    } catch {
      // Fallback to navigator.vibrate for web
      if (navigator.vibrate) {
        const patterns: Record<string, number | number[]> = {
          light: 10,
          medium: 25,
          heavy: 50,
          success: [10, 50, 20],
          error: [50, 30, 50],
          selection: 5
        };
        navigator.vibrate(patterns[pattern]);
      }
    }
  };

  return { vibrate };
};
