import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, Calendar, Dumbbell, Play, ExternalLink } from 'lucide-react';
import { WorkoutCard } from '@/components/WorkoutCard';
import axios from 'axios';

import { Paywall } from '@/components/Paywall';
import { useUser } from '@/contexts/UserContext';

const weekDays = ['Du', 'Se', 'Cho', 'Pa', 'Ju', 'Sha', 'Ya'];

const freeWorkouts = [
  {
    title: 'Uyda mashq - Boshlang\'ich',
    duration: '25 daqiqa',
    calories: 180,
    exercises: 8,
  },
  {
    title: 'Kardio va stretching',
    duration: '20 daqiqa',
    calories: 150,
    exercises: 6,
  },
  {
    title: 'Tananing yuqori qismi',
    duration: '30 daqiqa',
    calories: 220,
    exercises: 10,
  },
];

interface Exercise {
  id: number;
  name: string;
  video_url: string;
  category: string;
  difficulty: string;
}

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';


export const WorkoutScreen: React.FC = () => {
  const { isPremium, todayLog, updateTodayLog } = useUser();
  const [selectedDay, setSelectedDay] = useState(0);
  const [showPaywall, setShowPaywall] = useState(false);
  const [exercises, setExercises] = useState<Exercise[]>([]);

  React.useEffect(() => {
    const fetchExercises = async () => {
      try {
        const res = await axios.get(`${API_URL}/content/exercises`);
        setExercises(res.data);
      } catch (e) {
        console.error("Failed to fetch exercises", e);
      }
    };
    fetchExercises();
  }, []);


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

  const handleWorkoutClick = (index: number) => {
    if (!isPremium() && selectedDay > 0) {
      setShowPaywall(true);
      return;
    }
    // Toggle workout completion for today
    if (selectedDay === 0) {
      updateTodayLog({ workout_done: !todayLog?.workout_done });
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
            Mashqlar
          </h1>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Dumbbell className="w-4 h-4" />
            <span>7 kunlik</span>
          </div>
        </div>

        {/* Day selector */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar mb-6">
          {days.map((day, index) => {
            const isLocked = index > 0 && !isPremium();
            return (
              <button
                key={index}
                onClick={() => handleDaySelect(index)}
                className={`relative flex flex-col items-center min-w-[48px] py-2 px-1 rounded-xl transition-all ${selectedDay === index
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

        {/* Premium info */}
        {!isPremium() && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-primary/10 border border-primary/30 rounded-xl p-3 mb-4"
          >
            <p className="text-sm text-foreground">
              <Lock className="w-4 h-4 inline mr-1" />
              Bepul rejada 3 ta asosiy mashq mavjud. AI shaxsiy dastur uchun Premium kerak.
            </p>
          </motion.div>
        )}
      </div>

      {/* Workouts */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4 space-y-3"
      >
        <motion.p variants={itemVariants} className="text-sm text-muted-foreground mb-2">
          Kun {selectedDay + 1} - {selectedDay === 0 ? 'Bugun' : days[selectedDay].day}
        </motion.p>

        {freeWorkouts.map((workout, index) => (
          <motion.div key={index} variants={itemVariants}>
            <WorkoutCard
              {...workout}
              isLocked={selectedDay > 0 && !isPremium()}
              isCompleted={selectedDay === 0 && index === 0 && todayLog?.workout_done}
              onClick={() => handleWorkoutClick(index)}
            />
          </motion.div>
        ))}

        {/* Tips section */}
        <motion.div
          variants={itemVariants}
          className="mt-6 p-4 rounded-2xl bg-card border border-border/50"
        >
          <h3 className="font-semibold text-foreground mb-2">💡 Maslahat</h3>
          <p className="text-sm text-muted-foreground">
            Har bir mashqdan oldin 5 daqiqa isitish mashqlari qiling. Bu jarohatlarning oldini oladi.
          </p>
        </motion.div>
      </motion.div>

      {/* Video Library */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4 mt-8"
      >
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center text-red-500">
            <Play className="w-5 h-5 fill-current" />
          </div>
          <h2 className="text-lg font-bold text-foreground">Mashqlar Kutubxonasi</h2>
        </div>

        <div className="space-y-3">
          {exercises.length === 0 ? (
            <p className="text-sm text-muted-foreground">Videolar yuklanmoqda...</p>
          ) : (
            exercises.map((ex) => (
              <motion.div
                key={ex.id}
                variants={itemVariants}
                className="bg-card border border-border/50 rounded-xl p-4 flex items-center justify-between"
              >
                <div>
                  <h3 className="font-semibold text-foreground">{ex.name}</h3>
                  <div className="flex gap-2 text-xs text-muted-foreground mt-1">
                    <span className="bg-muted px-2 py-0.5 rounded">{ex.category}</span>
                    <span className="bg-muted px-2 py-0.5 rounded">{ex.difficulty}</span>
                  </div>
                </div>
                <a
                  href={ex.video_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary hover:bg-primary/20 transition-colors"
                >
                  <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                    <Play className="w-5 h-5 fill-current" />
                  </motion.div>
                </a>
              </motion.div>
            ))
          )}
        </div>
      </motion.div>


      <Paywall
        isOpen={showPaywall}
        onClose={() => setShowPaywall(false)}
        feature="AI mashq dasturi"
      />
    </div>
  );
};
