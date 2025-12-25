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
  setProfile: (profile: UserProfile) => void;
  completeOnboarding: () => void;
  updateTodayLog: (log: Partial<DailyLog>) => void;
  addWater: (ml: number) => void;
  isPremium: () => boolean;
  checkAndDowngrade: () => boolean;
  // Meals management
  addMeal: (meal: Omit<Meal, 'id' | 'date'>) => void;
  removeMeal: (id: string) => void;
  getTodayMeals: () => Meal[];
  getTodayCalories: () => number;
  // Workouts management
  addWorkout: (workout: Omit<WorkoutLog, 'id' | 'date'>) => void;
  getTodayWorkouts: () => WorkoutLog[];
  markWorkoutDone: () => void;
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
        meals: parsed.meals || [],
        workouts: parsed.workouts || [],
        streaks: {
          water: parsed.streaks?.water || 0,
          sleep: parsed.streaks?.sleep || 0,
          mood: parsed.streaks?.mood || 0,
          workout: parsed.streaks?.workout || 0,
        },
      };
    }
    return {
      isOnboarded: false,
      profile: null,
      planType: 'free' as PlanType,
      premiumUntil: null,
      trialUsed: false,
      points: 0,
      streaks: { water: 0, sleep: 0, mood: 0, workout: 0 },
      todayLog: null,
      meals: [],
      workouts: [],
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

  // Meals management
  const addMeal = useCallback((meal: Omit<Meal, 'id' | 'date'>) => {
    const today = getTodayDate();
    const newMeal: Meal = {
      ...meal,
      id: Date.now().toString(),
      date: today,
    };
    
    const newMeals = [...state.meals, newMeal];
    const todayMeals = newMeals.filter(m => m.date === today);
    const totalCalories = todayMeals.reduce((sum, m) => sum + m.calories, 0);
    
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
    
    const newState = {
      ...state,
      meals: newMeals,
      todayLog: { ...currentLog, calories_consumed: totalCalories },
    };
    saveState(newState);
  }, [state, saveState]);

  const removeMeal = useCallback((id: string) => {
    const today = getTodayDate();
    const newMeals = state.meals.filter(m => m.id !== id);
    const todayMeals = newMeals.filter(m => m.date === today);
    const totalCalories = todayMeals.reduce((sum, m) => sum + m.calories, 0);
    
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
    
    const newState = {
      ...state,
      meals: newMeals,
      todayLog: { ...currentLog, calories_consumed: totalCalories },
    };
    saveState(newState);
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

  // Workouts management
  const addWorkout = useCallback((workout: Omit<WorkoutLog, 'id' | 'date'>) => {
    const today = getTodayDate();
    const newWorkout: WorkoutLog = {
      ...workout,
      id: Date.now().toString(),
      date: today,
    };
    
    const newWorkouts = [...state.workouts, newWorkout];
    
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
    
    let newPoints = state.points + 15;
    let newStreaks = { ...state.streaks };
    
    if (!currentLog.workout_done) {
      newStreaks.workout += 1;
    }
    
    const newState = {
      ...state,
      workouts: newWorkouts,
      points: newPoints,
      streaks: newStreaks,
      todayLog: { ...currentLog, workout_done: true },
    };
    saveState(newState);
  }, [state, saveState]);

  const getTodayWorkouts = useCallback(() => {
    const today = getTodayDate();
    return state.workouts.filter(w => w.date === today);
  }, [state.workouts]);

  const markWorkoutDone = useCallback(() => {
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
    
    if (currentLog.workout_done) return;
    
    let newPoints = state.points + 15;
    let newStreaks = { ...state.streaks };
    newStreaks.workout += 1;
    
    const newState = {
      ...state,
      points: newPoints,
      streaks: newStreaks,
      todayLog: { ...currentLog, workout_done: true },
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
        addMeal,
        removeMeal,
        getTodayMeals,
        getTodayCalories,
        addWorkout,
        getTodayWorkouts,
        markWorkoutDone,
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
