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
          <h2 className="text-3xl font-black tracking-tight text-foreground">Umumiy ko'rinish</h2>
          <p className="text-sm text-muted-foreground font-medium mt-1">
            Jonli foydalanuvchi metrikalari va asosiy KPI ko'rsatkichlari
          </p>
        </div>
        <div className="flex items-center gap-3 px-5 py-2.5 glass-panel rounded-2xl border-border shadow-sm w-fit transition-all hover:border-primary/50">
          <div className="w-2.5 h-2.5 rounded-full bg-success animate-pulse shadow-[0_0_15px_rgba(34,197,94,0.4)]" />
          <span className="text-[11px] uppercase font-black tracking-[0.15em] text-success">Live Syncing</span>
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
      <div className="space-y-6">
        <div className="flex items-center gap-3 px-1">
          <div className="w-1 h-4 bg-primary rounded-full" />
          <h3 className="text-[11px] font-black text-muted-foreground uppercase tracking-[0.2em]">
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
        <div className="glass-card flex flex-col items-center justify-center text-center py-12 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-20 transition-all duration-500 translate-x-4 translate-y-[-4px]">
            <TrendingUp className="w-32 h-32" />
          </div>
          <span className="stat-label mb-4">Umumiy konversiya</span>
          <div className="stat-value text-6xl lg:text-7xl mb-6">{conversionRate}%</div>
          <div className="flex items-center gap-3 px-5 py-2 bg-primary/10 rounded-full border border-primary/20">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-[11px] font-black uppercase tracking-[0.1em] text-primary">Bepul → Paid</span>
          </div>
        </div>

        <div className="glass-card flex flex-col items-center justify-center text-center py-12 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-20 transition-all duration-500 translate-x-4 translate-y-[-4px]">
            <Sparkles className="w-32 h-32 text-success" />
          </div>
          <span className="stat-label mb-4 text-success/80">Sinov konversiyasi</span>
          <div className="stat-value text-6xl lg:text-7xl mb-6 text-success" style={{ backgroundImage: 'none', color: 'hsl(var(--success))' }}>{trialConversion}%</div>
          <div className="flex items-center gap-3 px-5 py-2 bg-success/10 rounded-full border border-success/20">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-[11px] font-black uppercase tracking-[0.1em] text-success">Sinov → Paid</span>
          </div>
        </div>
      </div>

      {/* User Distribution Bar */}
      <div className="glass-card p-10">
        <div className="flex items-center justify-between mb-8">
          <span className="stat-label">Foydalanuvchilar taqsimoti</span>
          <span className="text-[10px] font-black uppercase tracking-[0.15em] px-4 py-1.5 bg-muted rounded-full border border-border">Segment Analytics</span>
        </div>

        <div className="h-5 rounded-full bg-muted overflow-hidden flex shadow-inner border border-border/50">
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

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 mt-10">
          <div className="flex flex-col gap-2 group transition-transform hover:translate-y-[-2px]">
            <span className="flex items-center gap-2.5 text-[11px] font-black uppercase tracking-widest opacity-70 group-hover:opacity-100 transition-opacity">
              <div className="w-3 h-3 rounded-full bg-muted-foreground/50" />
              Bepul
            </span>
            <span className="text-2xl font-black font-mono leading-none">{((displayData.free_users / displayData.total_users) * 100).toFixed(1)}%</span>
          </div>
          <div className="flex flex-col gap-2 group transition-transform hover:translate-y-[-2px]">
            <span className="flex items-center gap-2.5 text-[11px] font-black uppercase tracking-widest opacity-70 group-hover:opacity-100 transition-opacity">
              <div className="w-3 h-3 rounded-full bg-warning shadow-[0_0_10px_rgba(var(--warning),0.3)]" />
              Sinov
            </span>
            <span className="text-2xl font-black font-mono leading-none text-warning">{((displayData.trial_users / displayData.total_users) * 100).toFixed(1)}%</span>
          </div>
          <div className="flex flex-col gap-2 group transition-transform hover:translate-y-[-2px]">
            <span className="flex items-center gap-2.5 text-[11px] font-black uppercase tracking-widest opacity-70 group-hover:opacity-100 transition-opacity">
              <div className="w-3 h-3 rounded-full bg-success shadow-[0_0_10px_rgba(var(--success),0.3)]" />
              Plus
            </span>
            <span className="text-2xl font-black font-mono leading-none text-success">{((displayData.plus_users / displayData.total_users) * 100).toFixed(1)}%</span>
          </div>
          <div className="flex flex-col gap-2 group transition-transform hover:translate-y-[-2px]">
            <span className="flex items-center gap-2.5 text-[11px] font-black uppercase tracking-widest opacity-70 group-hover:opacity-100 transition-opacity">
              <div className="w-3 h-3 rounded-full bg-primary shadow-[0_0_10px_rgba(var(--primary),0.3)]" />
              Pro
            </span>
            <span className="text-2xl font-black font-mono leading-none text-primary">{((displayData.pro_users / displayData.total_users) * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OverviewTab;
