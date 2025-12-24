import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

export interface UserProfile {
  id?: number;
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

export interface Meal {
  id: string;
  name: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  date: string;
}

export interface WorkoutLog {
  id: string;
  name: string;
  duration: number;
  caloriesBurned: number;
  date: string;
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
    workout: number;
  };
  todayLog: DailyLog | null;
  meals: Meal[];
  workouts: WorkoutLog[];
}

interface UserContextType extends UserState {
  setProfile: (profile: UserProfile) => Promise<void>;
  completeOnboarding: (data?: any) => Promise<void>;
  updateTodayLog: (log: Partial<DailyLog>) => void;
  addWater: (ml: number) => void;
  isPremium: () => boolean;
  checkAndDowngrade: () => boolean;
  // Meals management
  addMeal: (meal: Omit<Meal, 'id' | 'date'>) => Promise<void>;
  removeMeal: (id: string) => void;
  getTodayMeals: () => Meal[];
  getTodayCalories: () => number;
  // Workouts management
  addWorkout: (workout: Omit<WorkoutLog, 'id' | 'date'>) => Promise<void>;
  getTodayWorkouts: () => WorkoutLog[];
  markWorkoutDone: () => void;
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
    streaks: { water: 0, sleep: 0, mood: 0, workout: 0 },
    todayLog: null,
    meals: [],
    workouts: [],
  };

  const [state, setState] = useState<UserState>(() => {
    const saved = localStorage.getItem('yash_user');
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
        return DEFAULT_STATE;
      }
    }
    return DEFAULT_STATE;
  });

  const saveState = useCallback((newState: UserState) => {
    localStorage.setItem('yash_user', JSON.stringify(newState));
    setState(newState);
  }, []);

  // --- Telegram & Backend Sync ---
  useEffect(() => {
    const initializeUser = async () => {
      try {
        const tg = (window as any).Telegram?.WebApp;
        if (tg?.initData) {
          const authRes = await axios.post(`${API_URL}/auth/telegram`, {
            initData: tg.initData
          });

          if (authRes.data.token) {
            localStorage.setItem('token', authRes.data.token);
            axios.defaults.headers.common['Authorization'] = `Bearer ${authRes.data.token}`;

            // Fetch full profile and status
            const userRes = await axios.get(`${API_URL}/user/profile`);
            const dbUser = userRes.data;

            if (dbUser) {
              const today = getTodayDate();

              // Fetch today's logs
              const mealLogs = await axios.get(`${API_URL}/entry/meals/${today}`);
              const workoutLogs = await axios.get(`${API_URL}/entry/workouts/${today}`);

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
                  workout: dbUser.streak_workout || 0,
                },
                meals: mealLogs.data || [],
                workouts: workoutLogs.data || [],
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
                },
                todayLog: {
                  date: today,
                  water_ml: dbUser.today_water || 0,
                  steps: dbUser.today_steps || 0,
                  sleep_hours: dbUser.today_sleep || 0,
                  mood: 'ok',
                  calories_consumed: mealLogs.data?.reduce((s: number, m: any) => s + m.calories, 0) || 0,
                  workout_done: !!workoutLogs.data?.length,
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
    try {
      await axios.put(`${API_URL}/user/profile`, {
        age: profile.age,
        gender: profile.gender,
        height: profile.height,
        weight: profile.weight,
        goal: profile.goal,
        activity_level: profile.activityLevel,
        allergies: profile.allergies.join(',')
      });
      const newState = { ...state, profile };
      saveState(newState);
    } catch (err) {
      console.error("Failed to update profile", err);
    }
  }, [state, saveState]);

  const completeOnboarding = useCallback(async (profileData?: any) => {
    try {
      if (profileData) {
        await axios.put(`${API_URL}/user/profile`, profileData);
      }
      // Re-trigger sync
      window.location.reload();
    } catch (error) {
      console.error("Onboarding failed", error);
    }
  }, []);

  const updateTodayLog = useCallback(async (log: Partial<DailyLog>) => {
    const today = getTodayDate();
    const currentLog = state.todayLog?.date === today ? state.todayLog : DEFAULT_STATE.todayLog;
    const newLog = { ...currentLog, ...log } as DailyLog;

    // Optional: Sync with backend immediately or debounced
    try {
      await axios.post(`${API_URL}/user/stats`, {
        water_ml: newLog.water_ml,
        steps: newLog.steps,
        sleep_hours: newLog.sleep_hours
      });
    } catch (e) { }

    const newState = { ...state, todayLog: newLog };
    saveState(newState);
  }, [state, saveState]);

  const addWater = useCallback((ml: number) => {
    const today = getTodayDate();
    const currentLog = state.todayLog?.date === today ? state.todayLog : { ...DEFAULT_STATE.todayLog, date: today };
    const newWater = (currentLog?.water_ml || 0) + ml;
    updateTodayLog({ water_ml: newWater });
  }, [state, updateTodayLog]);

  const addMeal = useCallback(async (meal: Omit<Meal, 'id' | 'date'>) => {
    const today = getTodayDate();
    try {
      await axios.post(`${API_URL}/entry/meals`, { ...meal, date: today });
      const res = await axios.get(`${API_URL}/entry/meals/${today}`);
      const newState = {
        ...state,
        meals: res.data,
        todayLog: {
          ...state.todayLog!,
          calories_consumed: res.data.reduce((s: number, m: any) => s + m.calories, 0)
        }
      };
      saveState(newState);
    } catch (e) { }
  }, [state, saveState]);

  const addWorkout = useCallback(async (workout: Omit<WorkoutLog, 'id' | 'date'>) => {
    const today = getTodayDate();
    try {
      await axios.post(`${API_URL}/entry/workouts`, { ...workout, date: today });
      const res = await axios.get(`${API_URL}/entry/workouts/${today}`);
      const newState = {
        ...state,
        workouts: res.data,
        todayLog: { ...state.todayLog!, workout_done: true }
      };
      saveState(newState);
    } catch (e) { }
  }, [state, saveState]);

  const getTodayMeals = useCallback(() => {
    const today = getTodayDate();
    return state.meals.filter(m => m.date === today);
  }, [state.meals]);

  const getTodayCalories = useCallback(() => {
    const today = getTodayDate();
    return state.meals
      .filter(m => m.date === today)
      .reduce((sum, m) => sum + m.calories, 0);
  }, [state.meals]);

  const getTodayWorkouts = useCallback(() => {
    const today = getTodayDate();
    return state.workouts.filter(w => w.date === today);
  }, [state.workouts]);

  const markWorkoutDone = useCallback(() => {
    updateTodayLog({ workout_done: true });
  }, [updateTodayLog]);

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
        addMeal,
        removeMeal: () => { }, // TODO
        getTodayMeals,
        getTodayCalories,
        addWorkout,
        getTodayWorkouts,
        markWorkoutDone,
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
