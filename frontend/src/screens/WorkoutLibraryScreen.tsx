import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Play, Pause, RotateCcw, Dumbbell, Clock, Flame, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useLanguage } from '@/contexts/LanguageContext';
import { useToast } from '@/hooks/use-toast';

interface Workout {
  id: string;
  titleKey: string;
  descKey: string;
  category: 'cardio' | 'strength' | 'flexibility' | 'hiit';
  duration: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  caloriesBurn: number;
}

interface WorkoutLibraryScreenProps {
  onBack?: () => void;
}

export const WorkoutLibraryScreen: React.FC<WorkoutLibraryScreenProps> = ({ onBack }) => {
  const { t } = useLanguage();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('all');
  const [activeWorkout, setActiveWorkout] = useState<Workout | null>(null);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);

  const workouts: Workout[] = [
    { id: '1', titleKey: 'workoutLib.morningStretch', descKey: 'workoutLib.morningStretchDesc', category: 'flexibility', duration: 10, difficulty: 'beginner', caloriesBurn: 50 },
    { id: '2', titleKey: 'workoutLib.hiitCardio', descKey: 'workoutLib.hiitCardioDesc', category: 'hiit', duration: 20, difficulty: 'intermediate', caloriesBurn: 250 },
    { id: '3', titleKey: 'workoutLib.strengthTraining', descKey: 'workoutLib.strengthTrainingDesc', category: 'strength', duration: 30, difficulty: 'intermediate', caloriesBurn: 200 },
    { id: '4', titleKey: 'workoutLib.yogaBasics', descKey: 'workoutLib.yogaBasicsDesc', category: 'flexibility', duration: 25, difficulty: 'beginner', caloriesBurn: 100 },
    { id: '5', titleKey: 'workoutLib.absWorkout', descKey: 'workoutLib.absWorkoutDesc', category: 'strength', duration: 15, difficulty: 'beginner', caloriesBurn: 120 },
    { id: '6', titleKey: 'workoutLib.tabata', descKey: 'workoutLib.tabataDesc', category: 'hiit', duration: 4, difficulty: 'advanced', caloriesBurn: 80 },
  ];

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'cardio': return 'from-red-500/20 to-red-500/5 border-red-500/30';
      case 'strength': return 'from-blue-500/20 to-blue-500/5 border-blue-500/30';
      case 'flexibility': return 'from-purple-500/20 to-purple-500/5 border-purple-500/30';
      case 'hiit': return 'from-orange-500/20 to-orange-500/5 border-orange-500/30';
      default: return 'from-primary/20 to-primary/5 border-primary/30';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'cardio': return t('workoutLib.cardio');
      case 'strength': return t('workoutLib.strength');
      case 'flexibility': return t('workoutLib.flexibility');
      case 'hiit': return t('workoutLib.hiit');
      default: return category;
    }
  };

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return t('workoutLib.beginner');
      case 'intermediate': return t('workoutLib.intermediate');
      case 'advanced': return t('workoutLib.advanced');
      default: return difficulty;
    }
  };

  const filteredWorkouts = activeTab === 'all' 
    ? workouts 
    : workouts.filter(w => w.category === activeTab);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startWorkout = (workout: Workout) => {
    setActiveWorkout(workout);
    setTimerSeconds(0);
    setIsTimerRunning(false);
  };

  const toggleTimer = () => {
    setIsTimerRunning(!isTimerRunning);
  };

  const resetTimer = () => {
    setTimerSeconds(0);
    setIsTimerRunning(false);
  };

  const completeWorkout = () => {
    if (activeWorkout) {
      toast({
        title: `${t('workoutLib.completed')} 🎉`,
        description: `${t(activeWorkout.titleKey)} - ${activeWorkout.caloriesBurn} ${t('workoutLib.caloriesBurned')}`,
      });
      setActiveWorkout(null);
      setTimerSeconds(0);
      setIsTimerRunning(false);
    }
  };

  React.useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isTimerRunning) {
      interval = setInterval(() => {
        setTimerSeconds(s => s + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning]);

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

  // Active Workout View
  if (activeWorkout) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <div className="px-4 pt-6 pb-4 safe-area-top">
          <div className="flex items-center gap-3 mb-6">
            <button onClick={() => setActiveWorkout(null)} className="p-2 rounded-full bg-card">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-foreground">{t(activeWorkout.titleKey)}</h1>
              <p className="text-sm text-muted-foreground">{t(activeWorkout.descKey)}</p>
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center px-4">
          {/* Timer Display */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-64 h-64 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 border-4 border-primary/50 flex items-center justify-center mb-8"
          >
            <p className="text-5xl font-bold text-foreground">{formatTime(timerSeconds)}</p>
          </motion.div>

          {/* Controls */}
          <div className="flex gap-4 mb-8">
            <Button
              size="lg"
              variant="outline"
              onClick={resetTimer}
              className="w-14 h-14 rounded-full"
            >
              <RotateCcw className="w-6 h-6" />
            </Button>
            <Button
              size="lg"
              onClick={toggleTimer}
              className="w-20 h-20 rounded-full"
            >
              {isTimerRunning ? <Pause className="w-8 h-8" /> : <Play className="w-8 h-8 ml-1" />}
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={completeWorkout}
              className="w-14 h-14 rounded-full text-green-500 border-green-500"
            >
              <CheckCircle className="w-6 h-6" />
            </Button>
          </div>

          {/* Stats */}
          <div className="flex gap-6">
            <div className="text-center">
              <Clock className="w-6 h-6 text-muted-foreground mx-auto mb-1" />
              <p className="text-lg font-bold">{activeWorkout.duration} {t('workoutLib.min')}</p>
              <p className="text-xs text-muted-foreground">{t('workoutLib.recommendation')}</p>
            </div>
            <div className="text-center">
              <Flame className="w-6 h-6 text-orange-400 mx-auto mb-1" />
              <p className="text-lg font-bold">{activeWorkout.caloriesBurn}</p>
              <p className="text-xs text-muted-foreground">{t('workoutLib.calorie')}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-24">
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={onBack} className="p-2 rounded-full bg-card">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-foreground">{t('workoutLib.title')}</h1>
            <p className="text-sm text-muted-foreground">{t('workoutLib.subtitle')}</p>
          </div>
        </div>

        {/* Category Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full overflow-x-auto">
            <TabsTrigger value="all" className="flex-1">{t('workoutLib.all')}</TabsTrigger>
            <TabsTrigger value="hiit" className="flex-1">{t('workoutLib.hiit')}</TabsTrigger>
            <TabsTrigger value="strength" className="flex-1">{t('workoutLib.strength')}</TabsTrigger>
            <TabsTrigger value="flexibility" className="flex-1">{t('workoutLib.yoga')}</TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab} className="mt-4">
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="show"
              className="space-y-3"
            >
              {filteredWorkouts.map((workout) => (
                <motion.div
                  key={workout.id}
                  variants={itemVariants}
                  className={`p-4 rounded-2xl bg-gradient-to-br ${getCategoryColor(workout.category)} border`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Dumbbell className="w-4 h-4 text-primary" />
                        <span className="text-xs font-medium text-primary">
                          {getCategoryLabel(workout.category)}
                        </span>
                      </div>
                      <p className="font-semibold text-foreground mb-1">{t(workout.titleKey)}</p>
                      <p className="text-sm text-muted-foreground mb-2">{t(workout.descKey)}</p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {workout.duration} {t('workoutLib.min')}
                        </span>
                        <span className="flex items-center gap-1">
                          <Flame className="w-3 h-3" />
                          {workout.caloriesBurn} kcal
                        </span>
                        <span>{getDifficultyLabel(workout.difficulty)}</span>
                      </div>
                    </div>
                    <Button onClick={() => startWorkout(workout)} size="icon" className="ml-4">
                      <Play className="w-5 h-5" />
                    </Button>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};
