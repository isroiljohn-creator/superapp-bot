import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Droplets, Footprints, Moon, Smile, Frown, Meh, Plus, Check } from 'lucide-react';
import { HabitCard } from '@/components/HabitCard';
import { Button } from '@/components/ui/button';
import { useUser } from '@/contexts/UserContext';
import { toast } from 'sonner';

const moodOptions = [
  { value: 'bad', label: 'Yomon', icon: Frown, color: 'text-red-400' },
  { value: 'ok', label: 'O\'rtacha', icon: Meh, color: 'text-yellow-400' },
  { value: 'good', label: 'Yaxshi', icon: Smile, color: 'text-green-400' },
];

const supportiveMessages = [
  "Hamma narsa yaxshi bo'ladi! Bugun o'zingizga ko'proq e'tibor bering. 💚",
  "Qiyin kunlar ham o'tadi. Siz kuchlisiz! 💪",
  "Har bir kun yangi imkoniyat. Ertaga yaxshiroq bo'ladi! 🌟",
];

export const HabitsScreen: React.FC = () => {
  const { todayLog, addWater, updateTodayLog, isPremium } = useUser();
  const [showMoodPicker, setShowMoodPicker] = useState(false);
  const [showStepsInput, setShowStepsInput] = useState(false);
  const [showSleepInput, setShowSleepInput] = useState(false);
  const [stepsInput, setStepsInput] = useState('');
  const [sleepInput, setSleepInput] = useState('');

  const handleAddWater = () => {
    addWater(250);
    toast.success('+250 ml suv qo\'shildi! 💧');
  };

  const handleMoodSelect = (mood: 'bad' | 'ok' | 'good') => {
    updateTodayLog({ mood });
    setShowMoodPicker(false);
    
    if (mood === 'bad') {
      const message = supportiveMessages[Math.floor(Math.random() * supportiveMessages.length)];
      toast.info(message, { duration: 5000 });
    } else if (mood === 'good') {
      toast.success('Ajoyib! Bugun yaxshi kun! 🎉');
    }
  };

  const handleAddSteps = () => {
    const steps = parseInt(stepsInput) || 0;
    if (steps > 0) {
      updateTodayLog({ steps: (todayLog?.steps || 0) + steps });
      setStepsInput('');
      setShowStepsInput(false);
      toast.success(`+${steps} qadam qo'shildi! 🚶`);
    }
  };

  const handleSetSleep = () => {
    const hours = parseFloat(sleepInput) || 0;
    if (hours > 0) {
      updateTodayLog({ sleep_hours: hours });
      setSleepInput('');
      setShowSleepInput(false);
      toast.success(`${hours} soat uyqu saqlandi! 😴`);
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
        <h1 className="text-2xl font-display font-bold text-foreground mb-2">
          Kundalik odatlar
        </h1>
        <p className="text-muted-foreground">
          Sog'lom odatlarni kuzatib boring
        </p>
      </div>

      {/* Habits */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4 space-y-4"
      >
        {/* Water */}
        <motion.div variants={itemVariants}>
          <HabitCard
            icon={<Droplets className="w-6 h-6" />}
            title="Suv ichish"
            current={todayLog?.water_ml || 0}
            target={2500}
            unit="ml"
            streak={0}
            onAdd={handleAddWater}
            addAmount={250}
            isCompleted={(todayLog?.water_ml || 0) >= 2500}
          />
        </motion.div>

        {/* Steps */}
        <motion.div variants={itemVariants}>
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                (todayLog?.steps || 0) >= 10000 ? 'bg-success/20' : 'bg-orange-500/20'
              }`}>
                <Footprints className={`w-7 h-7 ${
                  (todayLog?.steps || 0) >= 10000 ? 'text-success' : 'text-orange-400'
                }`} />
              </div>
              
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">Qadamlar</h3>
                <p className="text-sm text-muted-foreground">
                  {todayLog?.steps || 0} / 10,000
                </p>
              </div>

              <AnimatePresence mode="wait">
                {showStepsInput ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="flex items-center gap-2"
                  >
                    <input
                      type="number"
                      value={stepsInput}
                      onChange={(e) => setStepsInput(e.target.value)}
                      placeholder="Qadam"
                      className="w-20 h-10 rounded-lg bg-muted text-center text-foreground"
                    />
                    <Button size="icon-sm" onClick={handleAddSteps}>
                      <Check className="w-4 h-4" />
                    </Button>
                  </motion.div>
                ) : (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setShowStepsInput(true)}
                    className="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center text-orange-400 hover:bg-orange-500/30 transition-colors"
                  >
                    <Plus className="w-6 h-6" />
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* Sleep */}
        <motion.div variants={itemVariants}>
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                (todayLog?.sleep_hours || 0) >= 8 ? 'bg-success/20' : 'bg-purple-500/20'
              }`}>
                <Moon className={`w-7 h-7 ${
                  (todayLog?.sleep_hours || 0) >= 8 ? 'text-success' : 'text-purple-400'
                }`} />
              </div>
              
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">Uyqu</h3>
                <p className="text-sm text-muted-foreground">
                  {todayLog?.sleep_hours || 0} / 8 soat
                </p>
              </div>

              <AnimatePresence mode="wait">
                {showSleepInput ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="flex items-center gap-2"
                  >
                    <input
                      type="number"
                      step="0.5"
                      value={sleepInput}
                      onChange={(e) => setSleepInput(e.target.value)}
                      placeholder="Soat"
                      className="w-16 h-10 rounded-lg bg-muted text-center text-foreground"
                    />
                    <Button size="icon-sm" onClick={handleSetSleep}>
                      <Check className="w-4 h-4" />
                    </Button>
                  </motion.div>
                ) : (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setShowSleepInput(true)}
                    className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center text-purple-400 hover:bg-purple-500/30 transition-colors"
                  >
                    <Plus className="w-6 h-6" />
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* Mood */}
        <motion.div variants={itemVariants}>
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <h3 className="font-semibold text-foreground mb-4">Bugungi kayfiyat</h3>
            
            <div className="flex gap-3">
              {moodOptions.map((option) => {
                const Icon = option.icon;
                const isSelected = todayLog?.mood === option.value;
                return (
                  <button
                    key={option.value}
                    onClick={() => handleMoodSelect(option.value as 'bad' | 'ok' | 'good')}
                    className={`flex-1 p-4 rounded-xl border-2 transition-all ${
                      isSelected
                        ? 'border-primary bg-primary/10'
                        : 'border-border bg-card hover:border-primary/30'
                    }`}
                  >
                    <Icon className={`w-8 h-8 mx-auto mb-2 ${option.color}`} />
                    <p className="text-sm font-medium text-foreground">{option.label}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </motion.div>

        {/* Daily tips */}
        <motion.div
          variants={itemVariants}
          className="mt-6 p-4 rounded-2xl bg-gradient-to-r from-primary/20 to-primary/10 border border-primary/30"
        >
          <h3 className="font-semibold text-foreground mb-2">💡 Kunlik maslahat</h3>
          <p className="text-sm text-muted-foreground">
            Har soatda 1 stakan suv iching. Bu metabolizmni tezlashtiradi va energiya beradi!
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
};
