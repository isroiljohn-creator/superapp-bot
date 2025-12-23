import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import { MealCard } from '@/components/MealCard';
import { Paywall } from '@/components/Paywall';
import { useUser } from '@/contexts/UserContext';

const weekDays = ['Du', 'Se', 'Cho', 'Pa', 'Ju', 'Sha', 'Ya'];

const freeMeals = [
  {
    time: 'Nonushta',
    title: 'Tuxumli salat',
    calories: 350,
    items: ['Tuxum 2 dona', 'Pomidor', 'Bodring', 'Non'],
  },
  {
    time: 'Tushlik',
    title: 'Tovuqli palov',
    calories: 550,
    items: ['Guruch 150g', 'Tovuq 120g', 'Sabzi', 'Piyoz'],
  },
  {
    time: 'Kechki ovqat',
    title: 'Baliq bilan sabzavot',
    calories: 400,
    items: ['Baliq 150g', 'Brokoli', 'Qizil karam'],
  },
  {
    time: 'Snack',
    title: 'Yogurt va meva',
    calories: 150,
    items: ['Yogurt 200g', 'Banan', 'Yong\'oq'],
  },
];

export const MenuScreen: React.FC = () => {
  const { isPremium } = useUser();
  const [selectedDay, setSelectedDay] = useState(0);
  const [showPaywall, setShowPaywall] = useState(false);

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
    if (index > 0 && !isPremium()) {
      setShowPaywall(true);
      return;
    }
    setSelectedDay(index);
  };

  const handleMealClick = (index: number) => {
    if (selectedDay > 0 && !isPremium()) {
      setShowPaywall(true);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-display font-bold text-foreground">
            Kunlik menyu
          </h1>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Calendar className="w-4 h-4" />
            <span>7 kunlik</span>
          </div>
        </div>

        {/* Day selector */}
        <div className="flex items-center gap-2 mb-6">
          <button className="p-2 text-muted-foreground">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="flex-1 flex gap-2 overflow-x-auto no-scrollbar">
            {days.map((day, index) => {
              const isLocked = index > 0 && !isPremium();
              return (
                <button
                  key={index}
                  onClick={() => handleDaySelect(index)}
                  className={`relative flex flex-col items-center min-w-[48px] py-2 px-1 rounded-xl transition-all ${
                    selectedDay === index
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-card text-foreground'
                  } ${isLocked ? 'opacity-60' : ''}`}
                >
                  <span className="text-xs font-medium">{day.day}</span>
                  <span className="text-lg font-bold">{day.date}</span>
                  {day.isToday && (
                    <div className="absolute -bottom-1 w-1.5 h-1.5 rounded-full bg-primary" />
                  )}
                  {isLocked && (
                    <Lock className="absolute -top-1 -right-1 w-3 h-3 text-muted-foreground" />
                  )}
                </button>
              );
            })}
          </div>
          <button className="p-2 text-muted-foreground">
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        {/* Premium info */}
        {!isPremium() && selectedDay === 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-primary/10 border border-primary/30 rounded-xl p-3 mb-4"
          >
            <p className="text-sm text-foreground">
              <Lock className="w-4 h-4 inline mr-1" />
              Faqat 1-kun bepul. 2-7 kunlar uchun Premium rejaga o'ting.
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
        {freeMeals.map((meal, index) => (
          <motion.div key={index} variants={itemVariants}>
            <MealCard
              {...meal}
              isLocked={selectedDay > 0 && !isPremium()}
              onClick={() => handleMealClick(index)}
            />
          </motion.div>
        ))}

        {/* Total calories */}
        <motion.div
          variants={itemVariants}
          className="mt-6 p-4 rounded-2xl bg-gradient-to-r from-primary/20 to-primary/10 border border-primary/30"
        >
          <div className="flex items-center justify-between">
            <span className="text-foreground font-medium">Jami kaloriya</span>
            <span className="text-2xl font-bold text-primary">
              {freeMeals.reduce((sum, meal) => sum + meal.calories, 0)} kkal
            </span>
          </div>
        </motion.div>
      </motion.div>

      <Paywall
        isOpen={showPaywall}
        onClose={() => setShowPaywall(false)}
        feature="7 kunlik menyu"
      />
    </div>
  );
};
