import React, { createContext, useContext, useState, useCallback } from 'react';

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
}

const UserContext = createContext<UserContextType | undefined>(undefined);

const getTodayDate = () => new Date().toISOString().split('T')[0];

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<UserState>(() => {
    const saved = localStorage.getItem('yasha_user');
    if (saved) {
      const parsed = JSON.parse(saved);
      return {
        ...parsed,
        premiumUntil: parsed.premiumUntil ? new Date(parsed.premiumUntil) : null,
      };
    }
    return {
      isOnboarded: false,
      profile: null,
      planType: 'free' as PlanType,
      premiumUntil: null,
      trialUsed: false,
      points: 0,
      streaks: { water: 0, sleep: 0, mood: 0 },
      todayLog: null,
    };
  });

  const saveState = useCallback((newState: UserState) => {
    localStorage.setItem('yasha_user', JSON.stringify(newState));
    setState(newState);
  }, []);

  const setProfile = useCallback((profile: UserProfile) => {
    const newState = { ...state, profile };
    saveState(newState);
  }, [state, saveState]);

  const completeOnboarding = useCallback(() => {
    // Start 7-day trial
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
    saveState(newState);
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
