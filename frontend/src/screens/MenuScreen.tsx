import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, Calendar, Plus, Coffee, Apple, Moon, Cookie } from 'lucide-react';
import { Paywall } from '@/components/Paywall';
import { DaySelector } from '@/components/DaySelector';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';

const getWeekDays = (t: (key: string) => string) => [
  t('day.mon'), t('day.tue'), t('day.wed'), t('day.thu'), t('day.fri'), t('day.sat'), t('day.sun')
];

// Suggested meals template for the weekly menu
const getSuggestedMealTemplates = (t: (key: string) => string) => ({
  breakfast: [
    { title: t('menu.breakfast'), calories: 350, items: ['2x', '1x', '1x', '1x'] },
    { title: t('menu.breakfast'), calories: 280, items: ['50g', '200ml', '1x', '1x'] },
    { title: t('menu.breakfast'), calories: 320, items: ['150g', '1x', '1x'] },
  ],
  lunch: [
    { title: t('menu.lunch'), calories: 550, items: ['150g', '120g', '1x', '1x'] },
    { title: t('menu.lunch'), calories: 480, items: ['100g', '100g', '1x'] },
    { title: t('menu.lunch'), calories: 420, items: ['150g', '1x', '1x', '1x'] },
  ],
  dinner: [
    { title: t('menu.dinner'), calories: 400, items: ['150g', '1x', '1x'] },
    { title: t('menu.dinner'), calories: 380, items: ['150g', '1x', '1x'] },
    { title: t('menu.dinner'), calories: 300, items: ['1x', '1x', '1x'] },
  ],
  snack: [
    { title: t('menu.snack'), calories: 150, items: ['200g', '1x', '1x'] },
    { title: t('menu.snack'), calories: 100, items: ['2x'] },
    { title: t('menu.snack'), calories: 180, items: ['1x', '1x', '1x'] },
  ],
});

const getMealIcon = (type: string) => {
  switch (type) {
    case 'breakfast': return <Coffee className="w-5 h-5 text-amber-400" />;
    case 'lunch': return <Apple className="w-5 h-5 text-green-400" />;
    case 'dinner': return <Moon className="w-5 h-5 text-purple-400" />;
    case 'snack': return <Cookie className="w-5 h-5 text-orange-400" />;
    default: return <Coffee className="w-5 h-5" />;
  }
};

const getMealTimeLabel = (type: string, t: (key: string) => string) => {
  switch (type) {
    case 'breakfast': return t('menu.breakfast');
    case 'lunch': return t('menu.lunch');
    case 'dinner': return t('menu.dinner');
    case 'snack': return t('menu.snack');
    default: return '';
  }
};

export const MenuScreen: React.FC = () => {
  const { isPremium, getTodayMeals, getTodayCalories, profile } = useUser();
  const { t } = useLanguage();
  const { vibrate } = useHaptic();
  const [selectedDay, setSelectedDay] = useState(0);
  const [showPaywall, setShowPaywall] = useState(false);

  const weekDays = getWeekDays(t);

  const today = new Date();
  const days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    return {
      day: weekDays[date.getDay() === 0 ? 6 : date.getDay() - 1],
      date: date.getDate(),
      isToday: i === 0,
    };
  });

  const handleDaySelect = (index: number) => {
    vibrate('light');
    if (index > 0 && !isPremium()) {
      setShowPaywall(true);
      return;
    }
    setSelectedDay(index);
  };

  // Get today's actual meals from context
  const todayMeals = getTodayMeals();
  const todayCalories = getTodayCalories();

  // Calculate daily goal based on profile
  const calculateDailyGoal = () => {
    if (!profile) return 2000;
    
    let bmr: number;
    if (profile.gender === 'male') {
      bmr = 88.362 + (13.397 * profile.weight) + (4.799 * profile.height) - (5.677 * profile.age);
    } else {
      bmr = 447.593 + (9.247 * profile.weight) + (3.098 * profile.height) - (4.330 * profile.age);
    }
    
    const activityMultipliers = {
      sedentary: 1.2,
      light: 1.375,
      moderate: 1.55,
      active: 1.725,
      very_active: 1.9,
    };
    
    let tdee = bmr * activityMultipliers[profile.activityLevel];
    
    if (profile.goal === 'lose') tdee -= 500;
    else if (profile.goal === 'gain') tdee += 300;
    
    return Math.round(tdee);
  };

  const dailyGoal = calculateDailyGoal();
  const suggestedMealTemplates = getSuggestedMealTemplates(t);

  // Generate suggested meals for the selected day
  const getSuggestedMeals = (dayIndex: number) => {
    const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack'] as const;
    return mealTypes.map(type => {
      const templates = suggestedMealTemplates[type];
      const template = templates[dayIndex % templates.length];
      return {
        type,
        ...template,
      };
    });
  };

  const suggestedMeals = getSuggestedMeals(selectedDay);
  const suggestedTotalCalories = suggestedMeals.reduce((sum, m) => sum + m.calories, 0);

  // For today (selectedDay === 0), show actual meals if any, otherwise show suggested
  const displayMeals = selectedDay === 0 && todayMeals.length > 0
    ? todayMeals.map(m => ({
        type: m.mealType,
        title: m.name,
        calories: m.calories,
        items: [`${m.protein}g ${t('menu.protein')}`, `${m.carbs}g ${t('menu.carbs')}`, `${m.fat}g ${t('menu.fat')}`],
      }))
    : suggestedMeals;

  const displayTotalCalories = selectedDay === 0 && todayMeals.length > 0
    ? todayCalories
    : suggestedTotalCalories;

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-5">
          <h1 className="text-2xl font-display font-bold text-foreground">
            {t('menu.title')}
          </h1>
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Calendar className="w-4 h-4" />
            <span>{t('menu.weekly')}</span>
          </div>
        </div>

        {/* Day selector - unified component */}
        <div className="mb-5">
          <DaySelector
            days={days}
            selectedDay={selectedDay}
            onDaySelect={handleDaySelect}
            isPremium={isPremium()}
          />
        </div>

        {/* Premium info */}
        {!isPremium() && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-primary/10 border border-primary/30 rounded-xl p-3 mb-4"
          >
            <p className="text-sm text-foreground">
              <Lock className="w-4 h-4 inline mr-1.5" />
              {t('menu.premiumInfo')}
            </p>
          </motion.div>
        )}
      </div>

      {/* Meals */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4 space-y-3"
      >
        <motion.div variants={itemVariants} className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {t('common.day')} {selectedDay + 1} - {selectedDay === 0 ? t('common.today') : days[selectedDay].day}
          </p>
          {selectedDay === 0 && todayMeals.length > 0 && (
            <span className="text-xs bg-success/20 text-success px-2 py-0.5 rounded-full">
              {t('menu.actualData')}
            </span>
          )}
        </motion.div>

        {displayMeals.map((meal, index) => (
          <motion.div
            key={index}
            variants={itemVariants}
            className={`p-4 rounded-xl bg-card border border-border/50 ${
              selectedDay > 0 && !isPremium() ? 'opacity-60' : ''
            }`}
          >
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-xl bg-muted shrink-0">
                {getMealIcon(meal.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs text-muted-foreground">{getMealTimeLabel(meal.type, t)}</p>
                  <p className="font-semibold text-foreground">{meal.calories} kcal</p>
                </div>
                <p className="font-semibold text-foreground mb-1">{meal.title}</p>
                <p className="text-sm text-muted-foreground truncate">
                  {meal.items.slice(0, 3).join(' • ')}
                  {meal.items.length > 3 && ` +${meal.items.length - 3}`}
                </p>
              </div>
              {selectedDay > 0 && !isPremium() && (
                <Lock className="w-4 h-4 text-muted-foreground shrink-0" />
              )}
            </div>
          </motion.div>
        ))}

        {/* Daily summary - improved */}
        <motion.div
          variants={itemVariants}
          className="p-4 rounded-xl bg-gradient-to-r from-primary/15 to-primary/5 border border-primary/30"
        >
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-foreground">{t('menu.dailyTotal')}</p>
            {selectedDay === 0 && todayMeals.length > 0 && (
              <span className="text-xs bg-success/20 text-success px-2 py-0.5 rounded-full">
                {t('menu.actual')}
              </span>
            )}
          </div>
          <div className="flex items-end justify-between">
            <div>
              <p className="text-3xl font-bold text-foreground">
                {displayTotalCalories.toLocaleString()}
              </p>
              <p className="text-xs text-muted-foreground">{t('menu.consumed')}</p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-primary">
                {dailyGoal.toLocaleString()}
              </p>
              <p className="text-xs text-muted-foreground">{t('menu.recommended')}</p>
            </div>
          </div>
          {/* Progress bar */}
          <div className="mt-3 h-2 bg-muted rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${displayTotalCalories > dailyGoal ? 'bg-red-400' : 'bg-primary'}`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min((displayTotalCalories / dailyGoal) * 100, 100)}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            {displayTotalCalories > dailyGoal 
              ? `${(displayTotalCalories - dailyGoal).toLocaleString()} kcal ${t('menu.excess')}`
              : `${(dailyGoal - displayTotalCalories).toLocaleString()} kcal ${t('menu.remaining')}`
            }
          </p>
        </motion.div>

        {/* Tips */}
        <motion.div
          variants={itemVariants}
          className="p-4 rounded-xl bg-card border border-border/50"
        >
          <div className="flex items-start gap-3">
            <div className="text-xl">💡</div>
            <div>
              <h3 className="font-semibold text-foreground text-sm mb-1">{t('menu.tip')}</h3>
              <p className="text-sm text-muted-foreground">
                {t('menu.tipText')}
              </p>
            </div>
          </div>
        </motion.div>
      </motion.div>

      <Paywall
        isOpen={showPaywall}
        onClose={() => setShowPaywall(false)}
        feature={t('paywall.aiMenu')}
      />
    </div>
  );
};