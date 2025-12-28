import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, Dumbbell, Play, Video, Clock, Flame, ChevronRight } from 'lucide-react';
import { WorkoutCard } from '@/components/WorkoutCard';
import { Paywall } from '@/components/Paywall';
import { DaySelector } from '@/components/DaySelector';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';

const getWeekDays = (t: (key: string) => string) => [
  t('day.mon'), t('day.tue'), t('day.wed'), t('day.thu'), t('day.fri'), t('day.sat'), t('day.sun')
];

const getFreeWorkouts = (t: (key: string) => string) => [
  {
    title: t('workout.homeBasic'),
    duration: '25 ' + t('common.minutes'),
    calories: 180,
    exercises: 8,
  },
  {
    title: t('workout.cardioStretching'),
    duration: '20 ' + t('common.minutes'),
    calories: 150,
    exercises: 6,
  },
  {
    title: t('workout.upperBody'),
    duration: '30 ' + t('common.minutes'),
    calories: 220,
    exercises: 10,
  },
];

const getVideoWorkouts = (t: (key: string) => string) => [
  {
    id: 1,
    title: t('workout.homeCardio'),
    duration: '15 ' + t('common.minutes'),
    thumbnail: null,
    isLocked: false,
  },
  {
    id: 2,
    title: t('workout.abs'),
    duration: '12 ' + t('common.minutes'),
    thumbnail: null,
    isLocked: true,
  },
  {
    id: 3,
    title: t('workout.fullBody'),
    duration: '25 ' + t('common.minutes'),
    thumbnail: null,
    isLocked: true,
  },
];

interface WorkoutScreenProps {
  onNavigate?: (tab: string) => void;
}

export const WorkoutScreen: React.FC<WorkoutScreenProps> = ({ onNavigate }) => {
  const { isPremium, todayLog, markWorkoutDone, getTodayWorkouts, selectedDate, setSelectedDate } = useUser();
  const { t } = useLanguage();
  const { vibrate } = useHaptic();
  const [showPaywall, setShowPaywall] = useState(false);

  const calculateDateStr = (index: number) => {
    const d = new Date();
    d.setDate(d.getDate() + index);
    return d.toISOString().split('T')[0];
  };

  const selectedDateStr = calculateDateStr(selectedDate);
  const todayWorkouts = useUser().getWorkoutsForDate(selectedDateStr);
  const isSelectedToday = selectedDate === 0;
  const workoutDone = isSelectedToday ? (todayLog?.workout_done || todayWorkouts.length > 0) : todayWorkouts.length > 0;

  const weekDays = getWeekDays(t);
  const freeWorkouts = getFreeWorkouts(t);
  const videoWorkouts = getVideoWorkouts(t);

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
    setSelectedDate(index);
  };

  const handleWorkoutClick = (index: number) => {
    vibrate('medium');
    if (!isPremium() && selectedDate > 0) {
      setShowPaywall(true);
      return;
    }
    // Mark workout as done for today
    if (selectedDate === 0 && !workoutDone) {
      markWorkoutDone();
    }
  };

  const handleVideoClick = (isLocked: boolean) => {
    vibrate('medium');
    if (isLocked && !isPremium()) {
      setShowPaywall(true);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
    exit: { opacity: 0, transition: { duration: 0.1 } }
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 220,
        damping: 25
      }
    },
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-5">
          <h1 className="text-2xl font-display font-bold text-foreground">
            {t('workout.title')}
          </h1>
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Dumbbell className="w-4 h-4" />
            <span>{t('menu.weekly')}</span>
          </div>
        </div>

        {/* Day selector */}
        <div className="mb-5">
          <DaySelector
            days={days}
            selectedDay={selectedDate}
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
              <Lock className="w-4 h-4 inline mr-1" />
              {t('workout.premiumInfo')}
            </p>
          </motion.div>
        )}

        {/* Workout Library CTA */}
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={() => onNavigate?.('workout-library')}
          className="w-full p-4 rounded-xl bg-card border border-border/50 flex items-center justify-between group active:scale-[0.98] transition-all"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/20 transition-colors">
              <Dumbbell className="w-5 h-5" />
            </div>
            <div className="text-left">
              <p className="text-sm font-bold text-foreground">{t('explore.workouts')}</p>
              <p className="text-xs text-muted-foreground">{t('explore.workoutsDesc')}</p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-muted-foreground" />
        </motion.button>
      </div>

      {/* Workouts */}
      <AnimatePresence mode="wait">
        <motion.div
          key={selectedDate}
          variants={containerVariants}
          initial="hidden"
          animate="show"
          exit="exit"
          className="px-4 space-y-3"
        >
          <motion.p variants={itemVariants} className="text-sm text-muted-foreground mb-2">
            {t('common.day')} {selectedDate + 1} - {selectedDate === 0 ? t('common.today') : days[selectedDate].day}
          </motion.p>

          {freeWorkouts.map((workout, index) => (
            <motion.div key={index} variants={itemVariants}>
              <WorkoutCard
                {...workout}
                isLocked={selectedDate > 0 && !isPremium()}
                isCompleted={selectedDate === 0 && index === 0 && todayLog?.workout_done}
                onClick={() => handleWorkoutClick(index)}
              />
            </motion.div>
          ))}

          {/* Video mashqlar bo'limi */}
          <motion.div variants={itemVariants} className="mt-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                <Video className="w-5 h-5 text-primary" />
                {t('workout.videoWorkouts')}
              </h2>
              <span className="text-xs text-muted-foreground">{t('workout.comingSoon')}</span>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {videoWorkouts.map((video) => (
                <motion.button
                  key={video.id}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleVideoClick(video.isLocked)}
                  className={`relative w-full rounded-2xl overflow-hidden bg-card border border-border/50 ${video.isLocked && !isPremium() ? 'opacity-60' : ''
                    }`}
                >
                  {/* Thumbnail placeholder */}
                  <div className="aspect-video bg-muted flex items-center justify-center relative">
                    <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />

                    {video.isLocked && !isPremium() ? (
                      <div className="w-14 h-14 rounded-full bg-muted-foreground/20 flex items-center justify-center">
                        <Lock className="w-6 h-6 text-muted-foreground" />
                      </div>
                    ) : (
                      <div className="w-14 h-14 rounded-full bg-primary/90 flex items-center justify-center shadow-glow">
                        <Play className="w-6 h-6 text-primary-foreground ml-1" />
                      </div>
                    )}

                    {/* Video info overlay */}
                    <div className="absolute bottom-3 left-3 right-3">
                      <h3 className="text-sm font-semibold text-foreground text-left">{video.title}</h3>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {video.duration}
                        </span>
                      </div>
                    </div>

                    {video.isLocked && !isPremium() && (
                      <div className="absolute top-2 right-2 px-2 py-1 bg-background/80 rounded-lg text-xs text-muted-foreground flex items-center gap-1">
                        <Lock className="w-3 h-3" />
                        Premium
                      </div>
                    )}
                  </div>
                </motion.button>
              ))}
            </div>

            <p className="text-xs text-muted-foreground text-center mt-3">
              {t('workout.videosSoon')}
            </p>
          </motion.div>

          {/* Tips section */}
          <motion.div
            variants={itemVariants}
            className="mt-6 p-4 rounded-2xl bg-card border border-border/50"
          >
            <div className="flex items-start gap-3">
              <div className="text-2xl">💡</div>
              <div>
                <h3 className="font-semibold text-foreground text-sm mb-1">{t('menu.tip')}</h3>
                <p className="text-sm text-muted-foreground">
                  {t('workout.warmupTip')}
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </AnimatePresence>

      <Paywall
        isOpen={showPaywall}
        onClose={() => setShowPaywall(false)}
        feature={t('paywall.aiWorkout')}
      />
    </div>
  );
};