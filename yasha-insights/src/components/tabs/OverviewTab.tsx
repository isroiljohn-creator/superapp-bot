import {
  Users,
  Activity,
  Crown,
  Sparkles,
  Clock,
  TrendingUp,
} from 'lucide-react';
import { StatCard } from '@/components/StatCard';
import { useOverview } from '@/hooks/useAnalytics';

interface OverviewTabProps {
  isLoading?: boolean;
}

export function OverviewTab({ isLoading: externalLoading = false }: OverviewTabProps) {
  const { data, isLoading: internalLoading } = useOverview();
  const isLoading = externalLoading || internalLoading;

  if (!data && !isLoading) return null;

  const displayData = data || {
    total_users: 0,
    active_24h: 0,
    active_7d: 0,
    active_30d: 0,
    free_users: 0,
    trial_users: 0,
    plus_users: 0,
    pro_users: 0
  };

  const payingUsers = displayData.plus_users + displayData.pro_users;

  const conversionRate = displayData.total_users > 0
    ? ((payingUsers / displayData.total_users) * 100).toFixed(1)
    : '0.0';

  const trialTotal = displayData.trial_users + payingUsers;
  const trialConversion = trialTotal > 0
    ? ((payingUsers / trialTotal) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Umumiy ko'rinish</h2>
          <p className="text-sm text-muted-foreground">
            Jonli foydalanuvchi metrikalari
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
          Jonli
        </div>
      </div>

      {/* Primary KPIs */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          title="Jami foydalanuvchilar"
          value={displayData.total_users}
          icon={Users}
          variant="primary"
          change={12.5}
          changeLabel="o'tgan oyga nisbatan"
          isLoading={isLoading}
        />
        <StatCard
          title="24s faol"
          value={displayData.active_24h}
          icon={Activity}
          change={8.3}
          changeLabel="kechaga nisbatan"
          isLoading={isLoading}
        />
      </div>

      {/* Activity Breakdown */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard
          title="24s faol"
          value={displayData.active_24h}
          icon={Clock}
          isLoading={isLoading}
          className="text-center"
        />
        <StatCard
          title="7k faol"
          value={displayData.active_7d}
          icon={TrendingUp}
          isLoading={isLoading}
          className="text-center"
        />
        <StatCard
          title="30k faol"
          value={displayData.active_30d}
          icon={Activity}
          isLoading={isLoading}
          className="text-center"
        />
      </div>

      {/* User Segments */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider">
          Foydalanuvchi segmentlari
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard
            title="Bepul"
            value={displayData.free_users}
            icon={Users}
            isLoading={isLoading}
          />
          <StatCard
            title="Sinov"
            value={displayData.trial_users}
            icon={Sparkles}
            variant="warning"
            isLoading={isLoading}
          />
          <StatCard
            title="Plus"
            value={displayData.plus_users}
            icon={Crown}
            variant="success"
            isLoading={isLoading}
          />
          <StatCard
            title="Pro"
            value={displayData.pro_users}
            icon={Crown}
            variant="success"
            className="bg-primary/10 border-primary/20"
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Conversion Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <div className="stat-card border-primary/20">
          <span className="stat-label">Umumiy konversiya</span>
          <div className="stat-value text-primary">{conversionRate}%</div>
          <p className="text-xs text-muted-foreground mt-1">
            Bepul → Plus/Pro
          </p>
        </div>
        <div className="stat-card border-success/20">
          <span className="stat-label">Sinov konversiyasi</span>
          <div className="stat-value text-success">{trialConversion}%</div>
          <p className="text-xs text-muted-foreground mt-1">
            Sinov → Plus/Pro
          </p>
        </div>
      </div>

      {/* User Distribution Bar */}
      <div className="stat-card">
        <span className="stat-label mb-3 block">Foydalanuvchilar taqsimoti</span>
        <div className="h-3 rounded-full bg-secondary overflow-hidden flex">
          <div
            className="bg-muted-foreground/50 h-full transition-all"
            style={{ width: `${(displayData.free_users / displayData.total_users) * 100}%` }}
          />
          <div
            className="bg-warning h-full transition-all"
            style={{ width: `${(displayData.trial_users / displayData.total_users) * 100}%` }}
          />
          <div
            className="bg-success h-full transition-all"
            style={{ width: `${(displayData.plus_users / displayData.total_users) * 100}%` }}
          />
          <div
            className="bg-primary h-full transition-all"
            style={{ width: `${(displayData.pro_users / displayData.total_users) * 100}%` }}
          />
        </div>
        <div className="flex justify-between mt-3 text-xs flex-wrap gap-2">
          <span className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-muted-foreground/50" />
            Bepul
          </span>
          <span className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-warning" />
            Sinov
          </span>
          <span className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-success" />
            Plus
          </span>
          <span className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-primary" />
            Pro
          </span>
        </div>
      </div>
    </div>
  );
}

export default OverviewTab;
