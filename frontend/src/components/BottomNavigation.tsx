import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, UtensilsCrossed, Dumbbell, Target, User } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TabItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

const tabs: TabItem[] = [
  { id: 'home', label: 'Bosh sahifa', icon: <Home /> },
  { id: 'menu', label: 'Menyu', icon: <UtensilsCrossed /> },
  { id: 'workout', label: 'Mashqlar', icon: <Dumbbell /> },
  { id: 'habits', label: 'Odatlar', icon: <Target /> },
  { id: 'profile', label: 'Profil', icon: <User /> },
];

interface BottomNavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const BottomNavigation: React.FC<BottomNavigationProps> = ({
  activeTab,
  onTabChange,
}) => {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 safe-area-bottom">
      <div className="bg-card/95 backdrop-blur-xl border-t border-border/50">
        <div className="flex items-center justify-around px-2 py-2">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={cn(
                  "relative flex flex-col items-center justify-center w-16 py-2 transition-all duration-200",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
              >
                <AnimatePresence mode="wait">
                  {isActive && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute -top-1 w-10 h-1 bg-primary rounded-full"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  )}
                </AnimatePresence>
                <motion.div
                  className="w-6 h-6"
                  animate={{
                    scale: isActive ? 1.1 : 1,
                    y: isActive ? -2 : 0,
                  }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                >
                  {tab.icon}
                </motion.div>
                <span className={cn(
                  "text-[10px] mt-1 font-medium transition-opacity",
                  isActive ? "opacity-100" : "opacity-70"
                )}>
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
