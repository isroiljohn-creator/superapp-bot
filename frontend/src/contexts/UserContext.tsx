import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { db } from '@/lib/db';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

export interface UserProfile {
  phone: string;
  name: string;
  age: number;
  gender: 'male' | 'female';
  height: number;
  weight: number;
  goal: 'lose' | 'gain' | 'maintain';
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
  allergies: string[];
}

export interface DailyLog {
  date: string;
  water_ml: number;
  steps: number;
  sleep_hours: number;
  mood: 'bad' | 'ok' | 'good';
  calories_consumed: number;
  workout_done: boolean;
}

export type PlanType = 'free' | 'trial' | 'premium' | 'vip';

interface UserState {
  isOnboarded: boolean;
  profile: UserProfile | null;
  planType: PlanType;
  premiumUntil: Date | null;
  trialUsed: boolean;
  points: number;
  streaks: {
    water: number;
    sleep: number;
    mood: number;
  };
  todayLog: DailyLog | null;
}

interface UserContextType extends UserState {
  setProfile: (profile: UserProfile) => void;
  completeOnboarding: () => void;
  updateTodayLog: (log: Partial<DailyLog>) => void;
  addWater: (ml: number) => void;
  isPremium: () => boolean;
  checkAndDowngrade: () => boolean;
  isLoading: boolean;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

const getTodayDate = () => new Date().toISOString().split('T')[0];

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isLoading, setIsLoading] = useState(true);
  const DEFAULT_STATE: UserState = {
    isOnboarded: false,
    profile: null,
    planType: 'free',
    premiumUntil: null,
    trialUsed: false,
    points: 0,
    streaks: { water: 0, sleep: 0, mood: 0 },
    todayLog: null,
  };

  const [state, setState] = useState<UserState>(() => {
    const saved = localStorage.getItem('yasha_user');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return {
          ...DEFAULT_STATE,
          ...parsed,
          premiumUntil: parsed.premiumUntil ? new Date(parsed.premiumUntil) : null,
          streaks: { ...DEFAULT_STATE.streaks, ...(parsed.streaks || {}) }
        };
      } catch (e) {
        console.error("Failed to parse saved user state", e);
        return DEFAULT_STATE;
      }
    }
    return DEFAULT_STATE;
  });

  const saveState = useCallback((newState: UserState) => {
    localStorage.setItem('yasha_user', JSON.stringify(newState));
    setState(newState);
  }, []);

  // Sync with Telegram and Backend
  useEffect(() => {
    const initializeUser = async () => {
      try {
        const tg = (window as any).Telegram?.WebApp;
        if (tg?.initData) {
          // 1. Authenticate with TG initData
          const authRes = await axios.post(`${API_URL}/auth/telegram`, {
            initData: tg.initData
          });

          if (authRes.data.token) {
            localStorage.setItem('token', authRes.data.token);

            // 2. Fetch profile from DB
            const { data: dbUser, error } = await db.select('profiles');

            if (dbUser) {
              // Sync local state with DB
              const updatedState: UserState = {
                ...state,
                isOnboarded: !!(dbUser.age && dbUser.weight),
                planType: (dbUser.plan_type || (dbUser.is_premium ? 'premium' : 'free')) as PlanType,
                points: dbUser.points || 0,
                premiumUntil: dbUser.premium_until ? new Date(dbUser.premium_until) : null,
                trialUsed: !!dbUser.trial_used,
                streaks: {
                  water: dbUser.streak_water || 0,
                  sleep: dbUser.streak_sleep || 0,
                  mood: dbUser.streak_mood || 0,
                },
                profile: {
                  id: dbUser.id,
                  name: dbUser.full_name || '',
                  phone: dbUser.phone || '',
                  age: dbUser.age || 0,
                  gender: dbUser.gender as any || 'male',
                  height: dbUser.height || 0,
                  weight: dbUser.weight || 0,
                  goal: (dbUser.goal?.includes('loss') ? 'lose' : dbUser.goal?.includes('gain') ? 'gain' : 'maintain') as any,
                  activityLevel: (dbUser.activity_level || 'moderate') as any,
                  allergies: dbUser.allergies?.split(',') || [],
                }
              };
              saveState(updatedState);
            }
          }
        }
      } catch (err) {
        console.error("User initialization failed:", err);
      } finally {
        setIsLoading(false);
      }
    };

    initializeUser();
  }, [saveState]);

  const setProfile = useCallback(async (profile: UserProfile) => {
    // 1. Update DB
    await db.insert('profiles', {
      age: profile.age,
      gender: profile.gender,
      height: profile.height,
      weight: profile.weight,
      goal: profile.goal,
      activity_level: profile.activityLevel,
      allergies: profile.allergies.join(',')
    });

    // 2. Update Local
    const newState = { ...state, profile };
    saveState(newState);
  }, [state, saveState]);

  const completeOnboarding = useCallback(async (profileData?: Partial<UserProfile>) => {
    try {
      if (profileData) {
        // Save to backend
        await axios.put(`${API_URL}/user/profile`, profileData);
        // Save to local profile immediately
        setProfile(prev => ({ ...prev, ...profileData } as UserProfile));
      }

      const premiumUntil = new Date();
      premiumUntil.setDate(premiumUntil.getDate() + 7);

      const newState: UserState = {
        ...state,
        isOnboarded: true,
        planType: 'trial',
        premiumUntil,
        trialUsed: true,
        todayLog: {
          date: getTodayDate(),
          water_ml: 0,
          steps: 0,
          sleep_hours: 0,
          mood: 'ok',
          calories_consumed: 0,
          workout_done: false,
        },
      };

      if (profileData) {
        newState.profile = { ...state.profile, ...profileData } as UserProfile;
      }

      saveState(newState);
    } catch (error) {
      console.error("Failed to complete onboarding:", error);
    }
  }, [state, saveState]);

  const updateTodayLog = useCallback((log: Partial<DailyLog>) => {
    const today = getTodayDate();
    const currentLog = state.todayLog?.date === today
      ? state.todayLog
      : {
        date: today,
        water_ml: 0,
        steps: 0,
        sleep_hours: 0,
        mood: 'ok' as const,
        calories_consumed: 0,
        workout_done: false,
      };

    const newLog = { ...currentLog, ...log };
    const newState = { ...state, todayLog: newLog };
    saveState(newState);
  }, [state, saveState]);

  const addWater = useCallback((ml: number) => {
    const today = getTodayDate();
    const currentLog = state.todayLog?.date === today
      ? state.todayLog
      : {
        date: today,
        water_ml: 0,
        steps: 0,
        sleep_hours: 0,
        mood: 'ok' as const,
        calories_consumed: 0,
        workout_done: false,
      };

    const newWater = currentLog.water_ml + ml;
    const wasCompleted = currentLog.water_ml >= 2500;
    const isNowCompleted = newWater >= 2500;

    let newPoints = state.points;
    let newStreaks = { ...state.streaks };

    if (!wasCompleted && isNowCompleted) {
      newPoints += 10;
      newStreaks.water += 1;
    }

    const newState = {
      ...state,
      points: newPoints,
      streaks: newStreaks,
      todayLog: { ...currentLog, water_ml: newWater },
    };
    saveState(newState);
  }, [state, saveState]);

  const isPremium = useCallback(() => {
    if (state.planType === 'free') return false;
    if (!state.premiumUntil) return false;
    return new Date() < state.premiumUntil;
  }, [state.planType, state.premiumUntil]);

  const checkAndDowngrade = useCallback(() => {
    if (state.planType !== 'free' && state.premiumUntil && new Date() >= state.premiumUntil) {
      const newState = { ...state, planType: 'free' as PlanType };
      saveState(newState);
      return true;
    }
    return false;
  }, [state, saveState]);

  return (
    <UserContext.Provider
      value={{
        ...state,
        setProfile,
        completeOnboarding,
        updateTodayLog,
        addWater,
        isPremium,
        checkAndDowngrade,
        isLoading,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within UserProvider');
  }
  return context;
};
