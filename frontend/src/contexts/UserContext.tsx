import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';
axios.defaults.baseURL = API_URL;

export interface UserProfile {
  phone: string;
  name: string;
  age: number;
  gender: 'male' | 'female';
  height: number;
  weight: number;
  goal: 'weight_loss' | 'muscle_gain' | 'health';
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'active' | 'athlete';
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
  resetData: () => Promise<void>;
  isLoading: boolean;
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

  const token = localStorage.getItem('token');
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  const [isLoading, setIsLoading] = useState(true); // Start as loading by default! 

  useEffect(() => {
    const initializeUser = async () => {
      try {
        const tg = (window as any).Telegram?.WebApp;
        if (tg?.initData) {
          console.log("Authenticating with Telegram initData...");
          const authRes = await axios.post(`${API_URL}/auth/telegram`, {
            initData: tg.initData
          });

          if (authRes.data.token) {
            const token = authRes.data.token;
            localStorage.setItem('token', token);
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

            // Fetch latest profile
            const profileRes = await axios.get(`${API_URL}/user/profile`);
            const userData = profileRes.data;

            console.log("DEBUG: Initial User Profile Fetched:", userData);

            // Construct new state from backend data mapping snake_case to camelCase
            const profile: UserProfile = {
              phone: userData.phone || '',
              name: userData.full_name || userData.username || 'Foydalanuvchi',
              age: userData.age || 0,
              gender: userData.gender as 'male' | 'female',
              height: userData.height || 0,
              weight: userData.weight || 0,
              goal: (userData.goal as 'weight_loss' | 'muscle_gain' | 'health') || 'weight_loss',
              activityLevel: (userData.activity_level as any) || 'sedentary',
              allergies: userData.allergies ? String(userData.allergies).split(',') : [],
            };

            // Trust backend is_onboarded flag, but fallback to our logic if it is false (e.g. legacy users)
            const isOnboarded = !!(userData.is_onboarded || (
              profile.age > 0 ||
              profile.weight > 0 ||
              profile.name !== 'Foydalanuvchi' ||
              profile.phone
            ));
            console.log("DEBUG: Determined isOnboarded:", isOnboarded);

            setState(prev => {
              // Merge with previous state to keep streaks/logs if valuable?
              // But usually backend logic rules.
              // Let's assume backend is source of truth for Plan/Points too.

              const newState: UserState = {
                ...prev,
                isOnboarded: isOnboarded,
                profile: profile,
                planType: (userData.plan_type || 'free').toLowerCase() as PlanType,
                premiumUntil: userData.premium_until ? new Date(userData.premium_until) : null,
                points: userData.points || 0,
                // Streaks from backend
                streaks: {
                  ...prev.streaks,
                  water: userData.streak_water || 0,
                  sleep: userData.streak_sleep || 0,
                  mood: userData.streak_mood || 0,
                },
                // trialUsed from backend? Not in profile response explicitly but handled via planType logic usually
                // Backend profile has "plan_type"

                // Sync Today's Log
                todayLog: {
                  ...prev.todayLog,
                  date: getTodayDate(),
                  water_ml: userData.today_water || 0,
                  steps: userData.today_steps || 0,
                  sleep_hours: userData.today_sleep || 0,
                  // calories/workout status might need separate sync or included in profile stats
                  calories_consumed: prev.todayLog?.calories_consumed || 0, // Backend doesn't send meal logs sum in profile yet
                  workout_done: prev.todayLog?.workout_done || false, // Should ideally come from backend
                  mood: prev.todayLog?.mood || 'ok'
                } as DailyLog
              };

              localStorage.setItem('yasha_user', JSON.stringify(newState));
              return newState;
            });
          }
        }
      } catch (error) {
        console.error("Auth Error:", error);
      } finally {
        setIsLoading(false); // Stop loading regardless of success/error
      }
    };

    initializeUser();
  }, []);

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
      planType: (state.planType || 'trial').toLowerCase() as PlanType,
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

  const addWater = useCallback(async (ml: number) => {
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

    try {
      await axios.post(`${API_URL}/entry/water`, { amount: ml });
    } catch (e) {
      console.error("Sync water failed", e);
    }
  }, [state, saveState]);

  // Meals management
  const addMeal = useCallback(async (meal: Omit<Meal, 'id' | 'date'>) => {
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

    try {
      await axios.post(`${API_URL}/entry/meals`, {
        name: meal.name,
        calories: meal.calories,
        protein: meal.protein,
        carbs: meal.carbs,
        fat: meal.fat,
        meal_type: meal.mealType, // Camel to Snake? Backend expects meal_type, Pydantic handles validation? 
        // Backend Pydantic uses 'meal_type'. 
        // Check UserContext 'mealType' vs Backend expected. 
        // Frontend interface Meal has 'mealType'.
        // Backend MealEntry has 'meal_type'.
        // So I must map it.
        date: today
      });
    } catch (e) {
      console.error("Sync meal failed", e);
    }
  }, [state, saveState]);

  const removeMeal = useCallback((id: string) => {
    // Sync removal is tricky as backend might rely on ID? 
    // Backend API doesn't support DELETE yet. 
    // Skipping sync for removal for MVP or add TODO.
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
  const addWorkout = useCallback(async (workout: Omit<WorkoutLog, 'id' | 'date'>) => {
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

    try {
      await axios.post(`${API_URL}/entry/workouts`, {
        name: workout.name,
        duration: workout.duration,
        calories_burned: workout.caloriesBurned, // Frontend camelCase to Snake?
        // Backend expects 'calories_burned'
        date: today
      });
    } catch (e) {
      console.error("Sync workout failed", e);
    }
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
    const type = state.planType?.toLowerCase();
    if (type === 'premium' || type === 'vip' || type === 'trial') return true;
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
    return false;
  }, [state, saveState]);

  const resetData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await axios.post(`${API_URL}/user/reset`);
      }
    } catch (e) {
      console.error("Reset failed", e);
    } finally {
      localStorage.clear();
      // Optional: don't reload immediately if caller handles it, but implementation plan said reload.
      // Actually PrivacySheet handles reload. 
      // UserContext should just reset state.

      const resetState: UserState = {
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
      saveState(resetState);
    }
  }, [saveState]);

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
        resetData,
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
