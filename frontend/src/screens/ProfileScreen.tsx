import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  User, Crown, Settings, ChevronRight, LogOut, 
  Bell, Moon, HelpCircle, Shield, Star, Trophy
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Paywall } from '@/components/Paywall';
import { useUser } from '@/contexts/UserContext';
import yashaLogo from '@/assets/yasha-logo.png';

export const ProfileScreen: React.FC = () => {
  const { profile, planType, premiumUntil, points, isPremium } = useUser();
  const [showPaywall, setShowPaywall] = useState(false);

  const getDaysRemaining = () => {
    if (!premiumUntil) return 0;
    const now = new Date();
    const diff = premiumUntil.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  };

  const getPlanLabel = () => {
    switch (planType) {
      case 'vip': return 'VIP';
      case 'premium': return 'Premium';
      case 'trial': return 'Sinov (Premium)';
      default: return 'Bepul';
    }
  };

  const menuItems = [
    { icon: User, label: 'Profilni tahrirlash', action: () => {} },
    { icon: Bell, label: 'Bildirishnomalar', action: () => {} },
    { icon: Shield, label: 'Maxfiylik', action: () => {} },
    { icon: HelpCircle, label: 'Yordam', action: () => {} },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    show: { opacity: 1, x: 0 },
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-display font-bold text-foreground">
            Profil
          </h1>
          <button className="p-2 text-muted-foreground hover:text-foreground">
            <Settings className="w-6 h-6" />
          </button>
        </div>

        {/* Profile card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-card border border-border/50 rounded-2xl p-5 mb-6"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
              <User className="w-8 h-8 text-primary" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-foreground">{profile?.name}</h2>
              <p className="text-sm text-muted-foreground">{profile?.phone}</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="text-center p-3 rounded-xl bg-muted/50">
              <p className="text-lg font-bold text-foreground">{profile?.age}</p>
              <p className="text-xs text-muted-foreground">Yosh</p>
            </div>
            <div className="text-center p-3 rounded-xl bg-muted/50">
              <p className="text-lg font-bold text-foreground">{profile?.height}</p>
              <p className="text-xs text-muted-foreground">Bo'y (sm)</p>
            </div>
            <div className="text-center p-3 rounded-xl bg-muted/50">
              <p className="text-lg font-bold text-foreground">{profile?.weight}</p>
              <p className="text-xs text-muted-foreground">Vazn (kg)</p>
            </div>
          </div>
        </motion.div>

        {/* Subscription status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className={`rounded-2xl p-5 mb-6 ${
            isPremium()
              ? 'bg-gradient-to-r from-primary/20 to-primary/10 border border-primary/30'
              : 'bg-card border border-border/50'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                isPremium() ? 'bg-primary/20' : 'bg-muted'
              }`}>
                <Crown className={`w-6 h-6 ${isPremium() ? 'text-primary' : 'text-muted-foreground'}`} />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Hozirgi reja</p>
                <p className="text-lg font-bold text-foreground">{getPlanLabel()}</p>
              </div>
            </div>
            {isPremium() && (
              <div className="text-right">
                <p className="text-2xl font-bold text-primary">{getDaysRemaining()}</p>
                <p className="text-xs text-muted-foreground">kun qoldi</p>
              </div>
            )}
          </div>

          {!isPremium() && (
            <Button
              variant="hero"
              className="w-full mt-4"
              onClick={() => setShowPaywall(true)}
            >
              <Crown className="w-5 h-5" />
              Premium olish
            </Button>
          )}
        </motion.div>

        {/* Points */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-card border border-border/50 rounded-2xl p-5 mb-6"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-yellow-500/20 flex items-center justify-center">
                <Trophy className="w-6 h-6 text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Ballaringiz</p>
                <p className="text-lg font-bold text-foreground">{points} ball</p>
              </div>
            </div>
            <Star className="w-8 h-8 text-yellow-400" />
          </div>
        </motion.div>

        {/* Menu */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="bg-card border border-border/50 rounded-2xl overflow-hidden"
        >
          {menuItems.map((item, index) => (
            <motion.button
              key={index}
              variants={itemVariants}
              onClick={item.action}
              className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors border-b border-border/30 last:border-b-0"
            >
              <div className="flex items-center gap-3">
                <item.icon className="w-5 h-5 text-muted-foreground" />
                <span className="text-foreground">{item.label}</span>
              </div>
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            </motion.button>
          ))}
        </motion.div>

        {/* Logout */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-6"
        >
          <Button variant="ghost" className="w-full text-destructive hover:text-destructive hover:bg-destructive/10">
            <LogOut className="w-5 h-5" />
            Chiqish
          </Button>
        </motion.div>

        {/* App info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 text-center"
        >
          <img src={yashaLogo} alt="YASHA" className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm text-muted-foreground">YASHA AI v1.0.0</p>
        </motion.div>
      </div>

      <Paywall
        isOpen={showPaywall}
        onClose={() => setShowPaywall(false)}
      />
    </div>
  );
};
