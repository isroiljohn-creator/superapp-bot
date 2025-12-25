import React from 'react';
import { Lock } from 'lucide-react';

interface Day {
  day: string;
  date: number;
  isToday: boolean;
}

interface DaySelectorProps {
  days: Day[];
  selectedDay: number;
  onDaySelect: (index: number) => void;
  isPremium?: boolean;
}

export const DaySelector: React.FC<DaySelectorProps> = ({
  days,
  selectedDay,
  onDaySelect,
  isPremium = false
}) => {
  return (
    <div className="flex gap-2 overflow-x-auto no-scrollbar">
      {days.map((day, index) => {
        const isLocked = index > 0 && !isPremium;
        const isSelected = selectedDay === index;
        
        return (
          <button
            key={index}
            onClick={() => onDaySelect(index)}
            className={`relative flex flex-col items-center min-w-[48px] py-2.5 px-2 rounded-xl transition-all border ${
              isSelected
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card text-foreground border-border/50'
            } ${isLocked ? 'opacity-60' : ''}`}
          >
            <span className="text-[10px] font-medium mb-0.5">{day.day}</span>
            <span className="text-base font-bold">{day.date}</span>
            {day.isToday && (
              <div className={`absolute -bottom-0.5 w-1 h-1 rounded-full ${isSelected ? 'bg-primary-foreground' : 'bg-primary'}`} />
            )}
            {isLocked && (
              <Lock className="absolute -top-1 -right-1 w-3 h-3 text-muted-foreground" />
            )}
          </button>
        );
      })}
    </div>
  );
};