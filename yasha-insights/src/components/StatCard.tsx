import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: LucideIcon;
  change?: number;
  changeLabel?: string;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'destructive';
  isLoading?: boolean;
  className?: string;
}

export function StatCard({
  title,
  value,
  icon: Icon,
  change,
  changeLabel,
  variant = 'default',
  isLoading = false,
  className,
}: StatCardProps) {
  const variantStyles = {
    default: '',
    primary: 'border-primary/20 bg-primary/5',
    success: 'border-success/20 bg-success/5',
    warning: 'border-warning/20 bg-warning/5',
    destructive: 'border-destructive/20 bg-destructive/5',
  };

  const iconStyles = {
    default: 'text-muted-foreground bg-muted/20',
    primary: 'text-primary bg-primary/10',
    success: 'text-success bg-success/10',
    warning: 'text-warning bg-warning/10',
    destructive: 'text-destructive bg-destructive/10',
  };

  if (isLoading) {
    return (
      <div className={cn('glass-card animate-pulse shadow-none', className)}>
        <div className="flex items-start justify-between mb-4">
          <div className="skeleton h-4 w-24" />
          <div className="skeleton h-10 w-10" />
        </div>
        <div className="skeleton h-10 w-32 mb-2" />
        <div className="skeleton h-4 w-20" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        'glass-card group',
        variantStyles[variant],
        className
      )}
    >
      <div className="flex items-center justify-between mb-4 gap-4">
        <span className="stat-label truncate group-hover:text-foreground transition-colors pr-2">{title}</span>
        {Icon && (
          <div
            className={cn(
              'p-2.5 rounded-2xl transition-all duration-500 group-hover:scale-110 group-hover:rotate-12 shadow-xl shadow-black/20 shrink-0',
              iconStyles[variant]
            )}
          >
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>

      <div className="flex flex-col gap-1.5 mt-auto">
        <div className="stat-value truncate leading-tight">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>

        {(change !== undefined || changeLabel) && (
          <div className="mt-3 flex items-center gap-2.5 flex-wrap">
            {change !== undefined && (
              <span
                className={cn(
                  change >= 0 ? 'stat-change-positive' : 'stat-change-negative',
                  "shadow-lg"
                )}
              >
                {change >= 0 ? '↑' : '↓'} {Math.abs(change).toFixed(1)}%
              </span>
            )}
            {changeLabel && (
              <span className="text-[10px] text-muted-foreground font-black uppercase tracking-widest opacity-40 group-hover:opacity-100 transition-opacity whitespace-nowrap">{changeLabel}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default StatCard;
