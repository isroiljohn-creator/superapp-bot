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
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex items-end justify-between px-2">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-foreground/90">Umumiy ko'rinish</h2>
          <p className="text-sm text-muted-foreground font-medium mt-1">
            Jonli foydalanuvchi metrikalari va asosiy KPI ko'rsatkichlari
          </p>
        </div>
        <div className="flex items-center gap-3 px-4 py-2 glass-panel rounded-2xl border-white/5 shadow-inner">
          <div className="w-2.5 h-2.5 rounded-full bg-success animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
          <span className="text-[10px] uppercase font-black tracking-widest text-success">Live Sync</span>
        </div>
      </div>

      {/* Primary KPIs */}
      {/* Primary KPIs & Activity */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
        <StatCard
          title="Jami foydalanuvchilar"
          value={displayData.total_users}
          icon={Users}
          variant="primary"
          change={12.5}
          changeLabel="OY"
          isLoading={isLoading}
          className="col-span-2 md:col-span-2"
        />
        <StatCard
          title="24s FAOL"
          value={displayData.active_24h}
          icon={Activity}
          change={8.3}
          changeLabel="KUN"
          isLoading={isLoading}
          className="col-span-1 md:col-span-1"
        />
        <StatCard
          title="Yangi (24s)"
          value={Math.round(displayData.total_users * 0.02)}
          icon={Sparkles}
          variant="success"
          isLoading={isLoading}
          className="col-span-1 md:col-span-1"
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-2 gap-4 md:gap-6">
        <StatCard
          title="7 kunlik faol"
          value={displayData.active_7d}
          icon={TrendingUp}
          isLoading={isLoading}
        />
        <StatCard
          title="30 kunlik faol"
          value={displayData.active_30d}
          icon={Activity}
          isLoading={isLoading}
        />
      </div>

      {/* User Segments */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 px-2">
          <Crown className="w-4 h-4 text-primary" />
          <h3 className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">
            Foydalanuvchi segmentlari
          </h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
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
            variant="primary"
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Conversion Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        <div className="glass-card flex flex-col items-center justify-center text-center py-10 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <TrendingUp className="w-24 h-24" />
          </div>
          <span className="stat-label mb-4">Umumiy konversiya</span>
          <div className="stat-value text-5xl md:text-6xl mb-4">{conversionRate}%</div>
          <div className="flex items-center gap-3 px-4 py-1.5 bg-primary/10 rounded-full border border-primary/20">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-widest text-primary">Bepul → Paid</span>
          </div>
        </div>

        <div className="glass-card flex flex-col items-center justify-center text-center py-10 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <Sparkles className="w-24 h-24 text-success" />
          </div>
          <span className="stat-label mb-4">Sinov konversiyasi</span>
          <div className="stat-value text-5xl md:text-6xl mb-4 text-success" style={{ backgroundImage: 'none', color: 'hsl(var(--success))' }}>{trialConversion}%</div>
          <div className="flex items-center gap-3 px-4 py-1.5 bg-success/10 rounded-full border border-success/20">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-widest text-success">Sinov → Paid</span>
          </div>
        </div>
      </div>

      {/* User Distribution Bar */}
      <div className="glass-card p-8">
        <div className="flex items-center justify-between mb-6">
          <span className="stat-label">Foydalanuvchilar taqsimoti</span>
          <span className="text-[10px] font-black uppercase tracking-widest px-3 py-1 bg-white/5 rounded-full border border-white/5">Segment Analytics</span>
        </div>

        <div className="h-4 rounded-full bg-white/5 overflow-hidden flex shadow-inner">
          <div
            className="bg-muted-foreground/30 h-full transition-all duration-1000 ease-out"
            style={{ width: `${(displayData.free_users / displayData.total_users) * 100}%` }}
          />
          <div
            className="bg-warning h-full transition-all duration-1000 ease-out delay-100"
            style={{ width: `${(displayData.trial_users / displayData.total_users) * 100}%` }}
          />
          <div
            className="bg-success h-full transition-all duration-1000 ease-out delay-200"
            style={{ width: `${(displayData.plus_users / displayData.total_users) * 100}%` }}
          />
          <div
            className="bg-primary h-full transition-all duration-1000 ease-out delay-300 shadow-[0_0_15px_rgba(var(--primary),0.5)]"
            style={{ width: `${(displayData.pro_users / displayData.total_users) * 100}%` }}
          />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 mt-8">
          <div className="flex flex-col gap-1">
            <span className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest opacity-60">
              <div className="w-2.5 h-2.5 rounded-full bg-muted-foreground/50" />
              Bepul
            </span>
            <span className="text-xl font-bold font-mono">{((displayData.free_users / displayData.total_users) * 100).toFixed(1)}%</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest opacity-60">
              <div className="w-2.5 h-2.5 rounded-full bg-warning" />
              Sinov
            </span>
            <span className="text-xl font-bold font-mono">{((displayData.trial_users / displayData.total_users) * 100).toFixed(1)}%</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest opacity-60">
              <div className="w-2.5 h-2.5 rounded-full bg-success" />
              Plus
            </span>
            <span className="text-xl font-bold font-mono">{((displayData.plus_users / displayData.total_users) * 100).toFixed(1)}%</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest opacity-60">
              <div className="w-2.5 h-2.5 rounded-full bg-primary" />
              Pro
            </span>
            <span className="text-xl font-bold font-mono">{((displayData.pro_users / displayData.total_users) * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OverviewTab;
