import {
  Users,
  Activity,
  Crown,
  Sparkles,
  Clock,
  TrendingUp,
} from 'lucide-react';
import { StatCard } from '@/components/StatCard';
import { mockOverview as data } from '@/hooks/useAnalytics';

interface OverviewTabProps {
  isLoading?: boolean;
}

export function OverviewTab({ isLoading = false }: OverviewTabProps) {
  const conversionRate = ((data.premium_users / data.total_users) * 100).toFixed(1);
  const trialConversion = ((data.premium_users / (data.trial_users + data.premium_users)) * 100).toFixed(1);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Overview</h2>
          <p className="text-sm text-muted-foreground">
            Real-time user metrics
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
          Live
        </div>
      </div>

      {/* Primary KPIs */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          title="Total Users"
          value={data.total_users}
          icon={Users}
          variant="primary"
          change={12.5}
          changeLabel="vs last month"
          isLoading={isLoading}
        />
        <StatCard
          title="Active 24h"
          value={data.active_24h}
          icon={Activity}
          change={8.3}
          changeLabel="vs yesterday"
          isLoading={isLoading}
        />
      </div>

      {/* Activity Breakdown */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard
          title="24h Active"
          value={data.active_24h}
          icon={Clock}
          isLoading={isLoading}
          className="text-center"
        />
        <StatCard
          title="7d Active"
          value={data.active_7d}
          icon={TrendingUp}
          isLoading={isLoading}
          className="text-center"
        />
        <StatCard
          title="30d Active"
          value={data.active_30d}
          icon={Activity}
          isLoading={isLoading}
          className="text-center"
        />
      </div>

      {/* User Segments */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider">
          User Segments
        </h3>
        <div className="grid grid-cols-3 gap-3">
          <StatCard
            title="Free"
            value={data.free_users}
            icon={Users}
            isLoading={isLoading}
          />
          <StatCard
            title="Trial"
            value={data.trial_users}
            icon={Sparkles}
            variant="warning"
            isLoading={isLoading}
          />
          <StatCard
            title="Premium"
            value={data.premium_users}
            icon={Crown}
            variant="success"
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Conversion Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <div className="stat-card border-primary/20">
          <span className="stat-label">Overall Conversion</span>
          <div className="stat-value text-primary">{conversionRate}%</div>
          <p className="text-xs text-muted-foreground mt-1">
            Free → Premium
          </p>
        </div>
        <div className="stat-card border-success/20">
          <span className="stat-label">Trial Conversion</span>
          <div className="stat-value text-success">{trialConversion}%</div>
          <p className="text-xs text-muted-foreground mt-1">
            Trial → Premium
          </p>
        </div>
      </div>

      {/* User Distribution Bar */}
      <div className="stat-card">
        <span className="stat-label mb-3 block">User Distribution</span>
        <div className="h-3 rounded-full bg-secondary overflow-hidden flex">
          <div
            className="bg-muted-foreground/50 h-full transition-all"
            style={{ width: `${(data.free_users / data.total_users) * 100}%` }}
          />
          <div
            className="bg-warning h-full transition-all"
            style={{ width: `${(data.trial_users / data.total_users) * 100}%` }}
          />
          <div
            className="bg-success h-full transition-all"
            style={{ width: `${(data.premium_users / data.total_users) * 100}%` }}
          />
        </div>
        <div className="flex justify-between mt-3 text-xs">
          <span className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-muted-foreground/50" />
            Free
          </span>
          <span className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-warning" />
            Trial
          </span>
          <span className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-success" />
            Premium
          </span>
        </div>
      </div>
    </div>
  );
}

export default OverviewTab;
