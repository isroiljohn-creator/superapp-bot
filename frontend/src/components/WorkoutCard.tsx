import React from 'react';
import { motion } from 'framer-motion';
import { Play, Lock, Clock, Flame, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface WorkoutCardProps {
  title: string;
  duration: string;
  calories: number;
  exercises: number;
  isLocked?: boolean;
  isCompleted?: boolean;
  onClick?: () => void;
}

export const WorkoutCard: React.FC<WorkoutCardProps> = ({
  title,
  duration,
  calories,
  exercises,
  isLocked = false,
  isCompleted = false,
  onClick,
}) => {
  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        "w-full p-4 rounded-2xl bg-card border border-border/50 text-left transition-all",
        isLocked && "opacity-60",
        isCompleted && "border-success/30 bg-success/5",
        !isLocked && !isCompleted && "hover:border-primary/30"
      )}
    >
      <div className="flex items-center gap-4">
        <div className={cn(
          "w-14 h-14 rounded-xl flex items-center justify-center",
          isCompleted ? "bg-success/20" : isLocked ? "bg-muted" : "bg-primary/20"
        )}>
          {isCompleted ? (
            <CheckCircle2 className="w-7 h-7 text-success" />
          ) : isLocked ? (
            <Lock className="w-6 h-6 text-muted-foreground" />
          ) : (
            <Play className="w-6 h-6 text-primary" />
          )}
        </div>
        
        <div className="flex-1">
          <h3 className="text-base font-semibold text-foreground mb-1">{title}</h3>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {duration}
            </span>
            <span className="flex items-center gap-1">
              <Flame className="w-4 h-4" />
              {calories} kkal
            </span>
          </div>
        </div>
        
        <div className="text-right">
          <span className="text-2xl font-bold text-foreground">{exercises}</span>
          <p className="text-xs text-muted-foreground">mashqlar</p>
        </div>
      </div>
    </motion.button>
  );
};
