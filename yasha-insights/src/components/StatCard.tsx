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
    default: 'border-border',
    primary: 'border-primary/30 glow-primary',
    success: 'border-success/30',
    warning: 'border-warning/30',
    destructive: 'border-destructive/30',
  };

  const iconStyles = {
    default: 'text-muted-foreground',
    primary: 'text-primary',
    success: 'text-success',
    warning: 'text-warning',
    destructive: 'text-destructive',
  };

  if (isLoading) {
    return (
      <div className={cn('stat-card animate-fade-in', className)}>
        <div className="flex items-start justify-between mb-3">
          <div className="skeleton h-4 w-24 rounded" />
          <div className="skeleton h-8 w-8 rounded-lg" />
        </div>
        <div className="skeleton h-8 w-32 rounded mb-2" />
        <div className="skeleton h-4 w-20 rounded" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        'stat-card animate-fade-in',
        variantStyles[variant],
        className
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="stat-label">{title}</span>
        {Icon && (
          <div
            className={cn(
              'p-2 rounded-lg bg-secondary/50 shrink-0',
              iconStyles[variant]
            )}
          >
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>

      <div className="stat-value animate-count-up">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>

      {(change !== undefined || changeLabel) && (
        <div className="mt-2 flex items-center gap-2">
          {change !== undefined && (
            <span
              className={cn(
                change >= 0 ? 'stat-change-positive' : 'stat-change-negative'
              )}
            >
              {change >= 0 ? '↑' : '↓'} {Math.abs(change).toFixed(1)}%
            </span>
          )}
          {changeLabel && (
            <span className="text-xs text-muted-foreground">{changeLabel}</span>
          )}
        </div>
      )}
    </div>
  );
}

export default StatCard;
