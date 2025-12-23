import React from 'react';
import { motion } from 'framer-motion';
import { Droplets, Footprints, Moon, Smile, Flame, Trophy } from 'lucide-react';
import { StatCard } from '@/components/StatCard';
import { useUser } from '@/contexts/UserContext';
import yashaLogo from '@/assets/yasha-logo.png';

export const HomeScreen: React.FC = () => {
  const { profile, todayLog, points, streaks, planType, premiumUntil } = useUser();

  const waterProgress = todayLog ? (todayLog.water_ml / 2500) * 100 : 0;
  const stepsProgress = todayLog ? (todayLog.steps / 10000) * 100 : 0;
  const sleepProgress = todayLog ? (todayLog.sleep_hours / 8) * 100 : 0;

  const getDaysRemaining = () => {
    if (!premiumUntil) return 0;
    const now = new Date();
    const diff = premiumUntil.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
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
          <div className="flex items-center gap-3">
            <img src={yashaLogo} alt="YASHA" className="w-10 h-10" />
            <div>
              <h1 className="text-lg font-bold text-foreground">
                Salom, {profile?.name || 'Foydalanuvchi'}!
              </h1>
              <p className="text-sm text-muted-foreground">
                Bugun qanday his qilyapsiz?
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-primary/10 px-3 py-1.5 rounded-full">
            <Trophy className="w-4 h-4 text-primary" />
            <span className="text-sm font-bold text-primary">{points}</span>
          </div>
        </div>

        {/* Trial/Premium Banner */}
        {(planType === 'trial' || planType === 'premium' || planType === 'vip') && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-r from-primary/20 to-primary/10 border border-primary/30 rounded-2xl p-4 mb-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs text-primary font-medium uppercase tracking-wide">
                  {planType === 'trial' ? 'Sinov muddati' : planType.toUpperCase()}
                </span>
                <p className="text-lg font-bold text-foreground">
                  {getDaysRemaining()} kun qoldi
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                <Flame className="w-6 h-6 text-primary" />
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Today's Stats */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4"
      >
        <motion.h2 variants={itemVariants} className="text-lg font-bold text-foreground mb-4">
          Bugungi ko'rsatkichlar
        </motion.h2>

        <div className="grid grid-cols-2 gap-3">
          <motion.div variants={itemVariants}>
            <StatCard
              icon={Droplets}
              label="Suv"
              value={todayLog?.water_ml || 0}
              target="2500"
              unit="ml"
              progress={waterProgress}
              color="blue"
            />
          </motion.div>

          <motion.div variants={itemVariants}>
            <StatCard
              icon={Footprints}
              label="Qadamlar"
              value={todayLog?.steps || 0}
              target="10,000"
              progress={stepsProgress}
              color="orange"
            />
          </motion.div>

          <motion.div variants={itemVariants}>
            <StatCard
              icon={Moon}
              label="Uyqu"
              value={todayLog?.sleep_hours || 0}
              target="8"
              unit="soat"
              progress={sleepProgress}
              color="purple"
            />
          </motion.div>

          <motion.div variants={itemVariants}>
            <StatCard
              icon={Smile}
              label="Kayfiyat"
              value={
                todayLog?.mood === 'good' ? 'Yaxshi' :
                  todayLog?.mood === 'bad' ? 'Yomon' :
                    'O\'rtacha'
              }
              color="primary"
            />
          </motion.div>
        </div>

        {/* Streaks */}
        <motion.div variants={itemVariants} className="mt-6">
          <h2 className="text-lg font-bold text-foreground mb-4">
            Streak'lar 🔥
          </h2>
          <div className="flex gap-3">
            <div className="flex-1 p-4 rounded-2xl bg-card border border-border/50 text-center">
              <Droplets className="w-6 h-6 text-blue-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-foreground">{streaks.water}</p>
              <p className="text-xs text-muted-foreground">Suv kun</p>
            </div>
            <div className="flex-1 p-4 rounded-2xl bg-card border border-border/50 text-center">
              <Moon className="w-6 h-6 text-purple-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-foreground">{streaks.sleep}</p>
              <p className="text-xs text-muted-foreground">Uyqu kun</p>
            </div>
            <div className="flex-1 p-4 rounded-2xl bg-card border border-border/50 text-center">
              <Smile className="w-6 h-6 text-primary mx-auto mb-2" />
              <p className="text-2xl font-bold text-foreground">{streaks.mood}</p>
              <p className="text-xs text-muted-foreground">Kayfiyat</p>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};
